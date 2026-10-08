from datetime import datetime, timedelta, timezone

from delivery_service import LearnerDeadline, send_deadline_reminder, should_remind


def test_near_deadline_without_delivery_is_reminded():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    deadline = LearnerDeadline("l-1", "+15550000000", "Algebra", now + timedelta(hours=8))
    assert should_remind(deadline, now, delivered=False) is True
    assert should_remind(deadline, now, delivered=True) is False


def test_far_deadline_is_not_reminded():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    deadline = LearnerDeadline("l-2", "+15550000001", "Biology", now + timedelta(days=3))
    assert should_remind(deadline, now, delivered=False) is False


def test_reminder_uses_contract_fields():
    class Client:
        def metrics_query(self, payload):
            assert payload == {
                "name": "course_deadline_reminder", "agg": "sum",
                "tags": {"learner_id": "l-1", "course": "Algebra"},
            }
            return {"data": {"delivered": False}}

        def sms_batch_send(self, messages):
            return {"data": {"message_id": "m-1"}}

        def metrics_report(self, payload):
            assert payload == {
                "name": "course_deadline_reminder", "value": 1, "type": "counter",
                "tags": {"learner_id": "l-1", "course": "Algebra"},
            }

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    deadline = LearnerDeadline("l-1", "+15550000000", "Algebra", now + timedelta(hours=8))
    assert send_deadline_reminder(Client(), deadline, now) == {"action": "sent", "message_id": "m-1"}
