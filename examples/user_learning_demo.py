"""Offline, synthetic example: understand, adapt, correct and forget."""
import json
from agent_user_learning import UserLearner


def run():
    with UserLearner(':memory:', 'synthetic-mina') as learner:
        def learn(n, kind, key, text, scope='general', signal='explicit'):
            learner.observe(dict(event_id=f'demo-{n}', source_id=f'message-{n}',
                                 session_id='demo-session', kind=kind, scope=scope,
                                 key=key, signal=signal, evidence=f'Synthetic user explicitly states: {text}',
                                 **{'value' if kind == 'attribute' else 'action': text}),
                            expected_version=learner.version)

        learn(1, 'attribute', 'profile.name', 'Mina')
        learn(2, 'attribute', 'goals.pass-n4', 'Pass JLPT N4.', 'study:japanese')
        learn(3, 'attribute', 'likes.city-pop', 'Enjoys city pop.', 'music')
        learn(4, 'preference', 'examples.format', 'Use short worked examples.', 'study:japanese')
        print('Study context:')
        print(json.dumps(learner.context(['study', 'study:japanese']), ensure_ascii=False, indent=2))
        print('Music context:')
        print(json.dumps(learner.context(['music']), ensure_ascii=False, indent=2))
        learn(5, 'attribute', 'dislikes.city-pop', 'No longer enjoys city pop.', 'music', 'correction')
        print('Corrected music understanding:')
        print(json.dumps(learner.context(['music'])['user'], ensure_ascii=False, indent=2))
        learner.forget_rule('music', 'dislikes.city-pop', kind='attribute', expected_version=learner.version)
        print('After forgetting this taste:')
        print(json.dumps(learner.context(['music'])['user'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
