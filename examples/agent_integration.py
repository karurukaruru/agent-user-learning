"""Runnable host integration: persistence, response context, correction, forgetting.

All inputs are synthetic. The response callback is deterministic and makes no
model call. Replace it with your existing agent invocation when integrating.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_user_learning import UserLearner


def answer_task(learner, task, scopes, respond):
    """Host boundary: supply memory as data alongside the current request."""
    snapshot = learner.context(scopes)
    return respond(task, snapshot)


def style_event(message_id, action, *, correction=False):
    """Example of an explicit remember command, not free-text extraction.

    IDs must come from the host's message/session records. These fixed scopes,
    keys and session IDs are demo choices, not automatic task classification.
    """
    return {
        'event_id': f'style:{message_id}',
        'source_id': message_id,
        'session_id': 'demo-session',
        'kind': 'preference',
        'scope': 'coding',
        'key': 'reply.style',
        'action': action,
        'signal': 'correction' if correction else 'explicit',
        'evidence': f'User explicitly requests: {action}',
    }


def demo_respond(task, user_context):
    """Show exactly what the real responder would receive; no simulated LLM."""
    actions = [rule['action'] for rule in user_context['rules']]
    return f'{task} | reply style: {"; ".join(actions) or "default"}'


def run_demo():
    # Temporary storage is only for this offline demo. A real host resolves a
    # persistent private path per authenticated user, outside the repository.
    with TemporaryDirectory(prefix='aul-demo-') as directory:
        db = Path(directory) / 'synthetic-user.db'
        with UserLearner(db, 'synthetic-user') as learner:
            print('1. Before learning:', answer_task(learner, 'Review this patch', ['coding'], demo_respond))
            learner.observe(style_event('message-1', 'Use short replies.'),
                            expected_version=learner.version)

        # New connection: memory survives the previous session closing.
        with UserLearner(db, 'synthetic-user') as learner:
            print('2. Next session:', answer_task(learner, 'Review this patch', ['coding'], demo_respond))
            print('3. Different task:', answer_task(learner, 'Review this draft', ['writing'], demo_respond))
            learner.observe(style_event('message-2', 'Explain step by step.', correction=True),
                            expected_version=learner.version)
            print('4. After correction:', answer_task(learner, 'Review this patch', ['coding'], demo_respond))
            learner.forget_rule('coding', 'reply.style', expected_version=learner.version)
            print('5. After forgetting:', answer_task(learner, 'Review this patch', ['coding'], demo_respond))


if __name__ == '__main__':
    run_demo()
