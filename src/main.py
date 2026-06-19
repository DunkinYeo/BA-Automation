"""
BioArmour Regression Test Runner
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_dotenv()

import yaml

from src.device_manager import DeviceManager
from src.reporter import RunReporter
from src.artifacts import ArtifactManager
from src.regression.runner import TestRunner
from src.regression.helpers import reset_to_login, go_to_exam_screen
from src.regression import login, settings, exam_info, exam, summary, connectivity
from src.slack import (
    slack_run_start, slack_run_complete, slack_run_failed, slack_regression_suite,
)


def load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser(description="BioArmour Regression Test Automation")
    ap.add_argument("--config", required=True, help="Path to config yaml")
    ap.add_argument("--result-json", default="", help="Path to save JSON result")
    args = ap.parse_args()

    cfg      = load_cfg(args.config)
    a_cfg    = cfg.get("android") or {}
    run_cfg  = cfg.get("run") or {}

    run_id  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join("output", run_id)
    os.makedirs(out_dir, exist_ok=True)

    hub_cfg  = cfg.get("hub") or {}
    reporter = RunReporter(
        out_dir=out_dir,
        run_name=run_cfg.get("name", "ba_regression"),
        hub_url=hub_cfg.get("url", "") if hub_cfg.get("enabled") else "",
        tester_name=hub_cfg.get("tester_name", ""),
    )
    artifacts = ArtifactManager(out_dir=out_dir)

    slack_cfg = cfg.get("slack") or {}
    _webhook  = os.environ.get("SLACK_WEBHOOK_URL") or slack_cfg.get("webhook_url", "")
    _mention  = slack_cfg.get("mention", "")
    _slack_on = bool(slack_cfg.get("enabled") and _webhook)

    reporter.log_event("run_start", {"config": args.config})

    dm = None
    total_passed = 0
    total_all    = 0

    try:
        dm = DeviceManager(a_cfg, {}, artifacts=artifacts, reporter=reporter)
        driver = dm.driver
        reporter.log_event("device_info", driver.get_device_info())

        if _slack_on:
            try:
                slack_run_start(_webhook, device=a_cfg.get("udid", ""), mention=_mention)
            except Exception:
                pass

        runner = TestRunner(driver, artifacts)

        # 스위트 정의
        # Phase 1: 로그인 화면 (앱 재시작 후 진행)
        # Phase 2: 검사 정보 화면 (go_to_exam_screen으로 진입)
        # Phase 3: 검사 화면 + 설정 + 연결성
        # Phase 4: 요약 화면 (검사 종료 후)

        suites_phase1 = [("login", login.TESTS), ("settings", settings.TESTS)]
        suites_phase2 = [("exam_info", exam_info.TESTS)]
        # Phase 3: 검사 화면 활성 상태에서 실행 (connectivity 포함, 종료 전)
        suites_phase3a = [("exam", exam.TESTS_PRE_STOP), ("connectivity", connectivity.TESTS)]
        # Phase 3b: 검사 종료 → 요약 화면 진입
        suites_phase3b = [("exam_stop", exam.TESTS_STOP)]
        suites_phase4 = [("summary", summary.TESTS)]

        def _run_suite(name, tests):
            pre = len(runner.results)
            runner.run_all(tests)
            batch    = runner.results[pre:]
            skipped  = sum(1 for r in batch if r.skipped)
            passed   = sum(1 for r in batch if r.passed and not r.skipped)
            ran      = len(batch) - skipped
            failures = [f"{r.name}: {r.message}" for r in batch if not r.passed and not r.skipped]
            reporter.log_event("regression_suite_result", {
                "suite": name, "passed": passed, "total": ran,
                "skipped": skipped, "failures": failures,
            })
            if _slack_on:
                try:
                    slack_regression_suite(_webhook, name, passed, len(batch), failures, _mention)
                except Exception:
                    pass
            return passed, ran

        # Phase 1 — 로그인 화면
        reset_to_login(driver, hard=True)
        for name, tests in suites_phase1:
            reset_to_login(driver, hard=False)
            p, t = _run_suite(name, tests)
            total_passed += p; total_all += t

        # Phase 2 — 검사 정보 화면
        # enter_serial → 연결하기 → 검사 정보 화면(BLE 연결 대기 최대 60s) → TC 실행
        reset_to_login(driver, hard=True)
        device_num = a_cfg.get("test_device_number", "")
        if device_num:
            try:
                import time as _t
                from src.regression.helpers import enter_serial, CONNECT_BTN
                _INFO_SCREEN = ["검사 정보 확인", "Study Information Confirmation", "대상 ID", "이름"]
                _ERR_POPUP   = ["알 수 없는 오류", "오류", "Error"]
                _OK_BTNS     = ["확인", "Ok", "OK"]
                for _ in range(5):
                    enter_serial(driver, device_num)
                    driver.tap_text(CONNECT_BTN, timeout=5, contains=False)
                    # BLE 연결 + 서버 응답 대기 (최대 90s), 에러 팝업 감지 시 dismiss 후 재시도
                    deadline = _t.monotonic() + 90
                    reached = False
                    while _t.monotonic() < deadline:
                        if driver.is_visible_text(_INFO_SCREEN, timeout=1):
                            reached = True
                            break
                        if driver.is_visible_text(_ERR_POPUP, timeout=1):
                            try:
                                driver.tap_text(_OK_BTNS, timeout=3, contains=False)
                            except Exception:
                                pass
                            _t.sleep(10)  # 서버 세션 정리 대기
                            break
                        _t.sleep(0.5)
                    if reached:
                        break
                    _t.sleep(5)  # 다음 시도 전 대기
            except Exception:
                pass
        for name, tests in suites_phase2:
            p, t = _run_suite(name, tests)
            total_passed += p; total_all += t

        # Phase 3a — 검사 화면 (검사 시작 후 연결 상태 테스트, 종료 전)
        try:
            go_to_exam_screen(driver)
        except Exception as _e:
            reporter.log_event("go_to_exam_screen_failed", {"error": str(_e)})
        for name, tests in suites_phase3a:
            p, t = _run_suite(name, tests)
            total_passed += p; total_all += t

        # Phase 3b — 검사 종료 → 요약 화면 진입
        for name, tests in suites_phase3b:
            p, t = _run_suite(name, tests)
            total_passed += p; total_all += t

        # Phase 4 — 요약 화면 (검사 종료 직후 실행)
        for name, tests in suites_phase4:
            p, t = _run_suite(name, tests)
            total_passed += p; total_all += t

        total_skipped = sum(1 for r in runner.results if r.skipped)
        reporter.log_event("run_complete", {
            "passed": total_passed, "total": total_all,
            "skipped": total_skipped, "status": "ok",
        })

        if _slack_on:
            try:
                slack_run_complete(_webhook, run_id, total_passed, total_all, _mention)
            except Exception:
                pass

        if args.result_json:
            import json
            results = [
                {"name": r.name, "passed": r.passed, "skipped": r.skipped,
                 "message": r.message, "duration_s": r.duration_s}
                for r in runner.results
            ]
            os.makedirs(os.path.dirname(args.result_json) or ".", exist_ok=True)
            with open(args.result_json, "w", encoding="utf-8") as f:
                json.dump({"passed": total_passed, "total": total_all,
                           "skipped": total_skipped, "results": results}, f,
                          ensure_ascii=False, indent=2)

    except Exception as e:
        reporter.log_event("run_failed", {"error": str(e)})
        if _slack_on:
            try:
                slack_run_failed(_webhook, run_id, str(e), _mention)
            except Exception:
                pass
        raise
    finally:
        if dm:
            dm.close()
        try:
            reporter.render_html_summary()
        except Exception:
            pass


if __name__ == "__main__":
    main()
