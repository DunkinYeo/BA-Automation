"""Phone Bluetooth over adb (2026-11-25). The Galaxy A32 (Samsung, Android
11) answers exactly as recorded here: `svc bluetooth disable` is killed
(exit 137), `cmd bluetooth_manager disable` prints "No shell command
implementation" with exit 0, and only the Appium Settings broadcast turns
it off (bluetooth_on 0, state BLE_ON) and back on. Ported from
MA-automation tests/test_adb_bluetooth.py."""
from types import SimpleNamespace

import src.regression.connectivity as conn
from src.adb_bluetooth import accepted, set_bluetooth

ADB = ["adb", "-s", "RF9R503211R"]


class Phone:
    """Answers adb like a phone; `works` = the ways that really switch BT."""

    def __init__(self, works, bt="1"):
        self.works, self.bt, self.calls = set(works), bt, []

    def __call__(self, cmd, **kw):
        sh = cmd[3:] if cmd[:3] == ADB else cmd[1:]
        sh = sh[1:] if sh and sh[0] == "shell" else sh
        self.calls.append(" ".join(sh[:3]))
        r = lambda out="", err="", rc=0: SimpleNamespace(returncode=rc, stdout=out if kw.get("text") else out.encode(),  # noqa: E731
                                                          stderr=err if kw.get("text") else err.encode())
        if sh[:3] == ["settings", "get", "global"]:
            return r(self.bt + "\n")
        word = sh[-1]
        if sh[0] == "svc":
            if "svc" not in self.works:
                return r(err="Killed\n", rc=137)
        elif sh[0] == "cmd":
            if "cmd" not in self.works:
                return r(out="No shell command implementation.\n")
        elif sh[0] == "am":
            if "appium" not in self.works:
                return r(out="Broadcasting: Intent { ... }\n")          # never completed
            out = "Broadcasting: Intent { ... }\nBroadcast completed: result=-1\n"
            self.bt = "1" if word == "enable" else "0"
            return r(out=out)
        self.bt = "1" if word == "enable" else "0"
        return r()


def test_a32_answers_aren_t_taken_for_success():
    k = SimpleNamespace(returncode=137, stdout=b"", stderr=b"Killed\n")
    n = SimpleNamespace(returncode=0, stdout=b"No shell command implementation.\n", stderr=b"")
    ok = SimpleNamespace(returncode=0, stdout=b"Broadcast completed: result=-1\nBroadcasting: x", stderr=b"")
    assert not accepted(k) and not accepted(n) and accepted(ok)


def test_a32_turns_off_and_on_through_appium_settings():
    p = Phone(works={"appium"})
    assert set_bluetooth(ADB, on=False, run=p, sleep=lambda s: None) == ("Appium Settings broadcast", True)
    assert p.bt == "0"
    assert set_bluetooth(ADB, on=True, run=p, sleep=lambda s: None) == ("Appium Settings broadcast", True)
    assert p.bt == "1"


def test_pixel_uses_svc_and_never_needs_the_broadcast():
    p = Phone(works={"svc"})
    assert set_bluetooth(ADB, on=False, run=p, sleep=lambda s: None)[0] == "svc bluetooth disable"
    assert not any(c.startswith("am ") for c in p.calls)


def test_nothing_works_is_none_and_no_command_taken():
    p = Phone(works=set())
    assert set_bluetooth(ADB, on=False, run=p, sleep=lambda s: None, wait_sec=4) == (None, False)


def test_already_in_the_wanted_state_sends_nothing():
    p = Phone(works={"svc"}, bt="0")
    assert set_bluetooth(ADB, on=False, run=p, sleep=lambda s: None) == ("already", True)
    assert p.calls == ["settings get global"]


def test_regression_bt_off_works_on_the_a32(monkeypatch):
    p = Phone(works={"appium"})
    monkeypatch.setattr("subprocess.run", p)
    monkeypatch.setattr("time.sleep", lambda s: None)
    drv = SimpleNamespace(cfg={"udid": "RF9R503211R"})
    assert conn._bt_off(drv) is True and p.bt == "0"
    conn._bt_on(drv)
    assert p.bt == "1"


class _Skip(Exception):
    pass


class _Runner:
    def skip(self, reason=""):
        raise _Skip(reason)


def test_regression_skips_bt_tc_when_no_way_works(monkeypatch):
    """Before: TC-CONN-001 sent `cmd bluetooth_manager disable` (exit 0, no-op
    on the A32) and then failed as "no Bluetooth popup". Now it is a SKIP."""
    import pytest
    p = Phone(works=set())
    monkeypatch.setattr("subprocess.run", p)
    monkeypatch.setattr("time.sleep", lambda s: None)
    monkeypatch.setattr(conn, "_on_exam_screen", lambda drv: True)
    drv = SimpleNamespace(cfg={"udid": "RF9R503211R"})
    for tc in (conn.test_conn_001_bt_off_popup, conn.test_conn_002_bt_recovery):
        with pytest.raises(_Skip):
            tc(drv, _Runner())
    assert p.bt == "1"
