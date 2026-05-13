"""
Slack 알림 모듈 — BioArmour 자동화
"""
import datetime
import requests


def _post(webhook_url: str, payload: dict):
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception:
        pass


def _mention(mention: str) -> str:
    if not mention:
        return ""
    m = mention.strip()
    if m.startswith("<") or m.startswith("@"):
        return m + " "
    return f"<@{m}> "


def slack_run_start(webhook_url: str, device: str, mention: str = ""):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    text = (
        f"{_mention(mention)}:rocket: *BioArmour Regression 시작* — {now}\n"
        f"  • Device: `{device}`"
    )
    _post(webhook_url, {"text": text})


def slack_run_complete(webhook_url: str, run_id: str, passed: int, total: int, mention: str = ""):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    icon = ":white_check_mark:" if passed == total else ":x:"
    text = (
        f"{icon} *BioArmour Regression 완료* — {now}\n"
        f"  • Run ID: `{run_id}`\n"
        f"  • 결과: `{passed}/{total}` passed"
    )
    _post(webhook_url, {"text": text})


def slack_run_failed(webhook_url: str, run_id: str, error: str, mention: str = ""):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    text = (
        f"{_mention(mention)}:x: *BioArmour Regression 실패* — {now}\n"
        f"  • Run ID: `{run_id}`\n"
        f"  • Error: {error}"
    )
    _post(webhook_url, {"text": text})


def slack_regression_suite(webhook_url: str, suite: str, passed: int, total: int,
                            failures: list, mention: str = ""):
    icon = ":white_check_mark:" if passed == total else ":x:"
    lines = [f"{icon} *[Regression] {suite}* — {passed}/{total} passed"]
    for f in failures[:5]:
        lines.append(f"  • {f}")
    _post(webhook_url, {"text": "\n".join(lines)})
