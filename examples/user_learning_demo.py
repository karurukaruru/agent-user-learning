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
        learn(2, 'attribute', 'goals.finish-draft', 'Finish a first draft.', 'writing:blog')
        learn(3, 'attribute', 'likes.background-music', 'Prefers background music while writing.', 'writing')
        learn(4, 'preference', 'examples.format', 'Use short worked examples.', 'writing:blog')
        print('Writing context:')
        print(json.dumps(learner.context(['writing', 'writing:blog']), ensure_ascii=False, indent=2))
        print('General context:')
        print(json.dumps(learner.context(), ensure_ascii=False, indent=2))
        learn(5, 'attribute', 'dislikes.background-music', 'Prefers quiet while writing.', 'writing', 'correction')
        print('Corrected writing context:')
        print(json.dumps(learner.context(['writing'])['user'], ensure_ascii=False, indent=2))
        learner.forget_rule('writing', 'dislikes.background-music', kind='attribute', expected_version=learner.version)
        print('After forgetting this taste:')
        print(json.dumps(learner.context(['writing'])['user'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
