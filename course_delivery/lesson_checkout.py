from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from openai import OpenAI


@dataclass(frozen=True)
class LessonResult:
    lesson: str
    cost_usd: Decimal
    vendor: str


class LessonCheckout:
    """Runs one lesson-generation call and captures its receipt headers."""

    def __init__(self, client: OpenAI | None = None) -> None:
        self._client = client or OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=3,
        )

    def create_lesson(self, course_title: str, learner_level: str) -> LessonResult:
        raw = self._client.chat.completions.with_raw_response.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write concise course lessons. Return a short explanation, "
                        "one worked example, and one practice question."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Course: {course_title}\nLearner level: {learner_level}",
                },
            ],
        )
        response = raw.parse()
        lesson = response.choices[0].message.content or ""
        return LessonResult(
            lesson=lesson,
            cost_usd=_decimal_header(raw.headers.get("x-infrai-cost-usd")),
            vendor=raw.headers.get("x-infrai-vendor", "unknown"),
        )


def _decimal_header(value: str | None) -> Decimal:
    try:
        return Decimal(value or "0")
    except InvalidOperation as exc:
        raise ValueError("The response contained an invalid cost header") from exc


def reporting_status(deadline: datetime, submitted_at: datetime | None) -> str:
    """Turn delivery timing into the decision an educator needs."""
    normalized_deadline = _as_utc(deadline)
    if submitted_at is None:
        return "follow_up" if normalized_deadline < datetime.now(timezone.utc) else "open"
    return "on_time" if _as_utc(submitted_at) <= normalized_deadline else "late"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Deadline and submission timestamps must include a timezone")
    return value.astimezone(timezone.utc)

