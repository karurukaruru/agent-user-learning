from pathlib import Path
import tempfile
import unittest

from agent_user_learning import UserLearner, VersionConflict
from examples.agent_integration import answer_task, style_event


class IntegrationExampleTests(unittest.TestCase):
    def test_responder_receives_persistent_scoped_corrected_and_forgotten_memory(self):
        received = []

        def respond(task, context):
            received.append((task, context))
            return 'response from existing agent'

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'one.db'
            with UserLearner(db, 'one') as learner:
                learner.observe(style_event('m1', 'Use short replies.'), expected_version=0)
            with UserLearner(db, 'one') as learner:
                result = answer_task(learner, 'Review this patch', ['coding'], respond)
                self.assertEqual(result, 'response from existing agent')
                self.assertEqual(received[-1][0], 'Review this patch')
                self.assertEqual(received[-1][1]['rules'][0]['action'], 'Use short replies.')
                answer_task(learner, 'Review this draft', ['writing'], respond)
                self.assertEqual(received[-1][1]['rules'], [])
                learner.observe(style_event('m2', 'Explain step by step.', correction=True), expected_version=1)
                answer_task(learner, 'Review this patch', ['coding'], respond)
                self.assertEqual([r['action'] for r in received[-1][1]['rules']], ['Explain step by step.'])
                learner.forget_rule('coding', 'reply.style', expected_version=2)
                answer_task(learner, 'Review this patch', ['coding'], respond)
                self.assertEqual(received[-1][1]['rules'], [])
                self.assertEqual(received[0][1]['rules'][0]['action'], 'Use short replies.')

    def test_other_user_and_stale_proposal_do_not_inherit_or_replace_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with UserLearner(Path(tmp) / 'one.db', 'one') as first, UserLearner(Path(tmp) / 'two.db', 'two') as second:
                event = style_event('m1', 'Use short replies.')
                first.observe(event, expected_version=0)
                self.assertTrue(first.observe(event, expected_version=0)['duplicate'])
                with self.assertRaises(VersionConflict):
                    first.observe(style_event('m2', 'Old delayed proposal.'), expected_version=0)
                self.assertEqual(first.version, 1)
                self.assertEqual(answer_task(first, 'task', ['coding'], lambda task, ctx: ctx)['rules'][0]['action'], 'Use short replies.')
                self.assertEqual(answer_task(second, 'task', ['coding'], lambda task, ctx: ctx)['rules'], [])


if __name__ == '__main__':
    unittest.main()
