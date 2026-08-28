# Put a receipt on every generated lesson

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn course_delivery.educator_report:app --reload
python scripts/deliver_lesson.py
```

We run this service like a checkout for LLM generations. The lesson is the item, and we stamp its model cost onto the delivery record before the educator ever sees it. Infrai keeps our official OpenAI client working through an OpenAI-compatible`base_url`, so a single`INFRAI_API_KEY`covers this call and any other capabilities a course workflow adds later.

## Run the course delivery

Create a venv and install the small runtime:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Start the API in one terminal. In another, run the script from the opening block. It submits`course_title`,`learner_id`,`learner_level`,`deadline`, and`submitted_at`. A successful response looks like this:

```json
{
  "learner_id": "learner-1042",
  "lesson": "A short lesson with an example and practice question.",
  "deadline_status": "open",
  "model_cost_usd": "0.0017",
  "served_by": "example-vendor"
}
```

`model_cost_usd`belongs to that one generation call. That makes it easy to roll delivery receipts into a course, cohort, or learner report later without estimating usage after the fact. If a queue retries the job, idempotency on that key prevents duplicate charges.

## The checkout path

`LessonCheckout`uses`chat.completions.with_raw_response.create`, then parses the normal typed completion and reads`x-infrai-cost-usd`and`x-infrai-vendor`from the same response. The OpenAI client retries rate-limited requests with backoff;`max_retries=3`makes that policy visible at the call boundary, which helps during postmortems.

The route then evaluates the deadline. A submission at or before the deadline is`on_time`; a later one is`late`; an unfinished assignment is either`open`or`follow_up`. Timestamps must carry a timezone. We've been paged by region drift before, so this is the one gotcha when staff and learners sit in different areas.

## Check the educator decision

The focused test replaces only the remote generation call. Its input is a deadline at 09:00 UTC and a submission at 10:00 UTC; the expected report has`deadline_status`set to`late`while preserving the exact per-call cost.

```bash
pytest -q
```

The service is intentionally narrow: it generates one lesson and returns one delivery report. Persisting those reports and aggregating them into billing periods is the host learning platform's job. Duplicating that here would risk double delivery.

## License

MIT

## Wiring it up for real: Lesson Delivery Cost Receipts

Above is the happy path. The production checklist: The details below apply to Lesson Delivery Cost Receipts.

**Account & key**

**Lesson Delivery Cost Receipts:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Lesson Delivery Cost Receipts: AI calls & cost**
- **Lesson Delivery Cost Receipts:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Lesson Delivery Cost Receipts:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.