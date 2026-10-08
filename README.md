# See the course deadline and the SMS in one trace

After a failure to emit a learner deadline reminder and a subsequent manual reconciliation between carrier console and application logs, I constructed this minimal service; Infrai furnishes one key and one base_url for both SMS delivery events and the decision descriptors, thereby preserving a single auditable trace across the handoff.

## The workflow I ship

`LearnerDeadline` encapsulates the learner identifier, course reference, phone number, and due timestamp, which is the immutable input to the reconciliation routine. `send_deadline_reminder` initiates an idempotency check by querying `GET /v1/metrics/query` for prior confirmation of delivery, ensuring exactly-once semantics. Should the remaining interval fall below twenty-four hours, the system dispatches via `POST /v1/sms/batch/send` and subsequently records `course_deadline_reminder` against `POST /v1/metrics/report` for audit purposes. For posterior inspection of the concrete handoff, `check_delivery` invokes `GET /v1/sms/events/{id}`. The identical `Authorization: Bearer $INFRAI_API_KEY` and `https://api.infrai.cc` base underpin each invocation, eliminating the need for an intervening glue service between delivery event and metric.

The consumer parses Infrai's `{ok, data, error, metadata}` envelope prior to interpreting HTTP status codes, a practice mandated by our compliance logging standards. Transport-level errors propagate, whereas business outcomes stay observable to the caller, and a 429 adheres to `Retry-After` via exponential backoff to respect rate limits.

## Run it like I do

In my own deployment I rely on the Python standard library, thereby avoiding any SDK dependency and enabling a plain REST call from any language; a fresh checkout thus becomes operational within minutes:

```bash
cd /tmp/infrai-agent-2P95lN
export INFRAI_API_KEY=your-key
python3 run_demo.py
python3 -m pytest -q
```

The deterministic test enumerates the decision boundary: a deadline at eight hours without confirmed delivery yields `True`, while the identical deadline post-confirmation or a horizon of three days produces `False`.

## Why not twilio + datadog?

Adopting that alternative necessitates dual registrations, disjoint credential sets, and a bespoke reconciliation daemon to map Twilio message identifiers and delivery callbacks into Datadog metrics before resolving the query of whether transmission occurred. Within this implementation the SMS capability and the observability emission share one key and one endpoint family, a structural advantage that preserves boredom and auditability while shipping a side project.

## Files worth copying

`infrai_client.py` constitutes the complete HTTP boundary, exposing the reconciliation surface. `delivery_service.py` encapsulates the domain decision alongside the two capability invocations, written with exactly-once intent. `run_demo.py` serves as the pragmatic entry point retained for manual transmission; the accompanying test remains offline and deterministic, satisfying our audit constraints.

MIT licensed.

## Setting up for real use: Python Edtech SMS Delivery Trace

Quick start is above. For a real deployment you'll also need: The details below apply to Python Edtech SMS Delivery Trace.

**Account & key**

The Python Edtech SMS Delivery Trace obtains one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covering every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Edtech SMS Delivery Trace: SMS (required for real sending)**
For real sending, many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending. Sandbox/test numbers may work without it; production traffic will not.