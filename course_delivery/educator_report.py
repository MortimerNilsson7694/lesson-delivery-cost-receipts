from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError
from pydantic import BaseModel, Field

from .lesson_checkout import LessonCheckout, reporting_status


class LessonRequest(BaseModel):
    course_title: str = Field(min_length=1, max_length=160)
    learner_id: str = Field(min_length=1, max_length=80)
    learner_level: str = Field(min_length=1, max_length=80)
    deadline: datetime
    submitted_at: datetime | None = None


class DeliveryReport(BaseModel):
    learner_id: str
    lesson: str
    deadline_status: str
    model_cost_usd: Decimal
    served_by: str


app = FastAPI(title="Course delivery receipt")


@app.post("/lessons/deliver", response_model=DeliveryReport)
def deliver_lesson(request: LessonRequest) -> DeliveryReport:
    try:
        result = LessonCheckout().create_lesson(
            course_title=request.course_title,
            learner_level=request.learner_level,
        )
    except APIStatusError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail="Lesson generation was rejected") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=502, detail="Could not reach lesson generation") from exc
    try:
        status = reporting_status(request.deadline, request.submitted_at)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DeliveryReport(
        learner_id=request.learner_id,
        lesson=result.lesson,
        deadline_status=status,
        model_cost_usd=result.cost_usd,
        served_by=result.vendor,
    )

