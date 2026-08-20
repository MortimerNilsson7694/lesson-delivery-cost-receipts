from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from course_delivery.educator_report import app
from course_delivery.lesson_checkout import LessonResult


def test_late_submission_is_visible_in_report(monkeypatch) -> None:
    def fake_lesson(self, course_title: str, learner_level: str) -> LessonResult:
        assert course_title == "Storefront conversion math"
        assert learner_level == "beginner"
        return LessonResult(
            lesson="Calculate completed checkouts divided by storefront visits.",
            cost_usd=Decimal("0.0017"),
            vendor="example-vendor",
        )

    monkeypatch.setattr(
        "course_delivery.educator_report.LessonCheckout.create_lesson",
        fake_lesson,
    )
    client = TestClient(app)
    response = client.post(
        "/lessons/deliver",
        json={
            "course_title": "Storefront conversion math",
            "learner_id": "learner-1042",
            "learner_level": "beginner",
            "deadline": datetime(2026, 8, 18, 9, tzinfo=timezone.utc).isoformat(),
            "submitted_at": datetime(2026, 8, 18, 10, tzinfo=timezone.utc).isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "learner_id": "learner-1042",
        "lesson": "Calculate completed checkouts divided by storefront visits.",
        "deadline_status": "late",
        "model_cost_usd": "0.0017",
        "served_by": "example-vendor",
    }

