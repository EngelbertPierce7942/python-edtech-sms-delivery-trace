from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from infrai_client import InfraiClient


@dataclass(frozen=True)
class LearnerDeadline:
    learner_id: str
    phone: str
    course: str
    due_at: datetime


def should_remind(deadline: LearnerDeadline, now: datetime, delivered: bool) -> bool:
    """Remind only when a deadline is within 24 hours and no delivery is confirmed."""
    hours_left = (deadline.due_at - now).total_seconds() / 3600
    return 0 <= hours_left <= 24 and not delivered


def send_deadline_reminder(client: InfraiClient, deadline: LearnerDeadline, now: datetime) -> Dict[str, Any]:
    event = client.metrics_query({
        "name": "course_deadline_reminder",
        "agg": "sum",
        "tags": {"learner_id": deadline.learner_id, "course": deadline.course},
    })
    delivered = bool(event.get("data", {}).get("delivered"))
    if not should_remind(deadline, now, delivered):
        return {"action": "skip", "reason": "delivery already confirmed or deadline is outside window"}

    message = {
        "to": deadline.phone,
        "body": f"Your {deadline.course} work is due by {deadline.due_at.isoformat()}.",
    }
    sent = client.sms_batch_send([message])
    message_id = sent.get("data", {}).get("message_id")
    client.metrics_report({
        "name": "course_deadline_reminder",
        "value": 1,
        "type": "counter",
        "tags": {"learner_id": deadline.learner_id, "course": deadline.course},
    })
    return {"action": "sent", "message_id": message_id}


def check_delivery(client: InfraiClient, message_id: str) -> Dict[str, Any]:
    return client.sms_events(message_id)
