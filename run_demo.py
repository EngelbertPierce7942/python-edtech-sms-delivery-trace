from datetime import datetime, timedelta, timezone

from delivery_service import LearnerDeadline, send_deadline_reminder
from infrai_client import InfraiClient


deadline = LearnerDeadline(
    learner_id="learner-17",
    phone="+15551234567",
    course="Intro to Python",
    due_at=datetime.now(timezone.utc) + timedelta(days=3),
)
result = send_deadline_reminder(InfraiClient(), deadline, datetime.now(timezone.utc))
print(result)
