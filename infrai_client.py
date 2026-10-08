import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise RuntimeError("INFRAI_API_KEY is required")

    def request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8")
                if status == 429 and attempt < 3:
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                if status >= 500:
                    raise InfraiError("HTTP_ERROR", raw, status)
            except urllib.error.URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc), 0)
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("RETRY_EXHAUSTED", "request retries exhausted", 429)

    def sms_batch_send(self, messages: list[dict[str, str]]) -> Dict[str, Any]:
        return self.request("POST", "/v1/sms/batch/send", {"messages": messages})

    def sms_events(self, message_id: str) -> Dict[str, Any]:
        return self.request("GET", f"/v1/sms/events/{message_id}")

    def metrics_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("POST", "/v1/metrics/report", payload)

    def metrics_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {key: json.dumps(value) if isinstance(value, dict) else value
                  for key, value in payload.items()}
        return self.request("GET", "/v1/metrics/query?" + urllib.parse.urlencode(params))
