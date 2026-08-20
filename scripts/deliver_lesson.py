import json
import os
from datetime import datetime, timedelta, timezone

import httpx


def main() -> None:
    deadline = datetime.now(timezone.utc) + timedelta(days=2)
    response = httpx.request(
        method="POST",
        url=os.environ.get("COURSE_SERVICE_URL", "http://127.0.0.1:8000/lessons/deliver"),
        json={
            "course_title": "Storefront conversion math",
            "learner_id": "learner-1042",
            "learner_level": "beginner",
            "deadline": deadline.isoformat(),
            "submitted_at": None,
        },
        timeout=30,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()

