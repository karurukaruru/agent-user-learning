from datetime import UTC, datetime, timedelta
import json
import unittest

from agent_user_learning import UserLearner


def attribute(n, **changes):
    return dict(event_id=f'a-{n}', source_id=f'user-message-{n}', kind='attribute',
                scope='general', key='profile.name', value='Mina', signal='explicit',
                session_id='session-a', evidence='User says their name is Mina.') | changes


class UnderstandingTests(unittest.TestCase):
    def setUp(self):
        self.store = UserLearner(':memory:', 'synthetic')

    def tearDown(self):
        self.store.close()

    def save(self, n, **changes):
        e = attribute(n, **changes)
        self.store.observe(e, expected_version=self.store.version)
        return e

    def test_profile_goal_interest_and_help_style_are_separate_and_relevant(self):
        self.save(1)
        self.save(2, scope='study:japanese', key='goals.pass-n4', value='Pass JLPT N4.')
        self.save(3, scope='music', key='likes.city-pop', value='Enjoys city pop.')
        self.store.observe(dict(event_id='p-1', source_id='user-message-4', kind='preference',
                                scope='study:japanese', key='examples.format', action='Use short worked examples.',
                                signal='explicit', session_id='session-a', evidence='User asks for short examples.'),
                           expected_version=self.store.version)
        study = self.store.context(['study:japanese'])
        self.assertEqual(study['user']['profile'][0]['value'], 'Mina')
        self.assertEqual(study['user']['goals'][0]['value'], 'Pass JLPT N4.')
        self.assertNotIn('likes', study['user'])
        self.assertEqual(study['rules'][0]['action'], 'Use short worked examples.')
        self.assertEqual(self.store.context(['music'])['user']['likes'][0]['value'], 'Enjoys city pop.')
        self.assertNotIn('evidence', json.dumps(study))
        self.assertNotIn('source_id', json.dumps(study))

    def test_identity_constraints_cannot_be_inferred(self):
        for key in ('profile.age', 'constraints.accessibility'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.save(1, key=key, signal='inferred')
        self.assertEqual(self.store.version, 0)

    def test_attribute_keys_require_a_named_field(self):
        for key in ('profile', 'profile.', 'likes.', 'goals..study'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.save(1, key=key)
        self.assertEqual(self.store.version, 0)
        self.assertEqual(self.store.inspect()['attributes'], [])

    def test_invalid_explain_and_forget_kind_preserve_stored_understanding(self):
        self.save(1)
        for kind in ([], {}, None, 'unknown'):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    self.store.explain('general|profile.name', kind=kind)
                with self.assertRaises(ValueError):
                    self.store.forget_rule('general', 'profile.name', kind=kind, expected_version=1)
        self.assertEqual(self.store.version, 1)
        self.assertEqual(self.store.context()['user']['profile'][0]['value'], 'Mina')

    def test_interest_inference_needs_distinct_sources_and_sessions(self):
        self.save(1, key='interests.music', value='Music', signal='inferred')
        self.save(2, key='interests.music', value='Music', signal='inferred')
        self.save(3, key='interests.music', value='Music', signal='inferred',
                  source_id='user-message-1', session_id='session-b')
        self.assertEqual(self.store.context()['user'], {})
        self.save(4, key='interests.music', value='Music', signal='inferred', session_id='session-b')
        self.assertIn('interests', self.store.context()['user'])
        self.store.forget('user-message-4', expected_version=self.store.version)
        self.assertEqual(self.store.context()['user'], {})

    def test_correction_replaces_explicit_taste_without_inferred_override(self):
        self.save(1, key='likes.city-pop', value='Enjoys city pop.')
        self.save(2, key='dislikes.city-pop', value='No longer enjoys city pop.', signal='correction')
        for n in (3, 4):
            self.save(n, key='likes.city-pop', value='Enjoys city pop.', signal='inferred', session_id=f'session-{n}')
        context = self.store.context()
        self.assertNotIn('likes', context['user'])
        self.assertIn('dislikes', context['user'])
        explanation = self.store.explain('general|dislikes.city-pop', kind='attribute')
        self.assertEqual(explanation['evidence'][0]['source_id'], 'user-message-2')

    def test_narrow_scope_taste_overrides_general_without_affecting_other_tasks(self):
        self.save(1, key='likes.background-music', value='Enjoys background music.')
        self.save(2, scope='study', key='dislikes.background-music', value='Wants quiet while studying.')
        self.assertIn('likes', self.store.context(['conversation'])['user'])
        self.assertNotIn('likes', self.store.context(['study'])['user'])
        self.assertIn('dislikes', self.store.context(['study'])['user'])

    def test_current_state_requires_expiry_and_expires(self):
        with self.assertRaises(ValueError):
            self.save(1, key='current.energy', value='Tired today.')
        future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        self.save(2, key='current.energy', value='Tired today.', expires_at=future)
        self.assertIn('current', self.store.context()['user'])
        past = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        self.save(3, key='current.schedule', value='Busy this morning.', expires_at=past)
        self.assertEqual(len(self.store.context()['user']['current']), 1)

    def test_forget_attribute_removes_old_values_and_both_taste_polarities(self):
        self.save(1, key='likes.city-pop', value='Enjoys city pop.')
        self.save(2, key='dislikes.city-pop', value='No longer enjoys city pop.', signal='correction')
        result = self.store.forget_rule('general', 'dislikes.city-pop', kind='attribute', expected_version=2)
        self.assertEqual(result['removed_events'], 2)
        self.assertEqual(self.store.inspect()['attributes'], [])
        self.save(3)
        self.save(4, value='Mina K.', signal='correction')
        self.store.forget_rule('general', 'profile.name', kind='attribute', expected_version=self.store.version)
        self.assertEqual(self.store.context()['user'], {})

    def test_context_budget_keeps_user_and_behavior_and_is_frozen(self):
        self.save(1)
        for n in range(10):
            self.store.observe(dict(event_id=f'p-{n}', source_id=f'p-source-{n}', kind='preference',
                                    scope='general', key=f'format.{n}', action='Use a worked example. ' * 9,
                                    signal='explicit', session_id='s-a', evidence='Synthetic user instruction.'),
                               expected_version=self.store.version)
        frozen = self.store.context(max_chars=700, max_attributes=1, max_rules=2)
        self.assertLessEqual(len(json.dumps(frozen, ensure_ascii=False)), 700)
        self.assertEqual(frozen['user']['profile'][0]['value'], 'Mina')
        self.assertEqual(len(frozen['rules']), 1)
        self.save(2, value='Mina K.', signal='correction')
        self.assertEqual(frozen['user']['profile'][0]['value'], 'Mina')
        self.assertEqual(self.store.context()['user']['profile'][0]['value'], 'Mina K.')

    def test_unconfirmed_scoped_attribute_does_not_hide_explicit_general(self):
        self.save(1, key='goals.learn-japanese', value='Learn for travel.')
        self.save(2, scope='study', key='goals.learn-japanese', value='Learn for work.', signal='inferred')
        self.assertEqual(self.store.context(['study'])['user']['goals'][0]['value'], 'Learn for travel.')

    def test_feedback_cannot_rewrite_identity_or_interests(self):
        self.save(1)
        record = self.store.inspect()['attributes'][0]
        with self.assertRaises(ValueError):
            self.store.observe(dict(event_id='f-1', source_id='reply-1', kind='feedback',
                                    rule_id=record['id'], rule_revision=record['revision'], outcome='accepted',
                                    evidence='User likes the answer.'), expected_version=1)
        self.assertEqual(self.store.context()['user']['profile'][0]['value'], 'Mina')


if __name__ == '__main__':
    unittest.main()
