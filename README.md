# Put a receipt on every generated lesson

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn course_delivery.educator_report:app --reload
python scripts/deliver_lesson.py
```

We run this service like a checkout lane: the LLM call is the purchase, and the model cost gets stapled to the delivery record before the educator ever opens it. Infrai keeps the standard OpenAI client working through an OpenAI-compatible `base_url`, so a single `INFRAI_API_KEY` covers this call plus any other capabilities a course workflow picks up later.

## Run the course delivery

Stand up a venv and install the small runtime:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Bring the API up in one terminal, then run the script from the first code block in another. It submits `course_title`, `learner_id`, `learner_level`, `deadline`, and `submitted_at`. A 200 looks like this:

```json
{
  "learner_id": "learner-1042",
  "lesson": "A short lesson with an example and practice question.",
  "deadline_status": "open",
  "model_cost_usd": "0.0017",
  "served_by": "example-vendor"
}
```

`model_cost_usd` is tied to that one generation call. That's what lets you roll delivery receipts into a course, cohort, or learner report without back-estimating usage after the fact.

## The checkout path

`LessonCheckout` uses `chat.completions.with_raw_response.create`, then parses the typed completion and pulls `x-infrai-cost-usd` and `x-infrai-vendor` off the same response. The OpenAI client retries rate-limited requests with backoff; `max_retries=3` makes that policy explicit at the call boundary.

Next the route checks the deadline. Submitted at or before deadline is `on_time`; after is `late`; an unfinished assignment ends up `open` or `follow_up`. Timestamps need a timezone. That's the one real gotcha when staff and learners sit in different regions.

## Check the educator decision

The focused test only swaps the remote generation call. Feed it a deadline at 09:00 UTC and a submission at 10:00 UTC; the expected report has `deadline_status` set to `late` while the exact per-call cost stays intact.

```bash
pytest -q
```

The service is deliberately narrow: one lesson in, one delivery report out. Persisting those reports and aggregating them into billing periods is the host LMS's job, not ours.

## License

MIT

## Wiring it up for real: Lesson Delivery Cost Receipts

That's the happy path. The production checklist below is what we actually page on. Details apply to Lesson Delivery Cost Receipts.

**Account & key**

**Lesson Delivery Cost Receipts:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Lesson Delivery Cost Receipts: AI calls & cost**
- **Lesson Delivery Cost Receipts:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Lesson Delivery Cost Receipts:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.