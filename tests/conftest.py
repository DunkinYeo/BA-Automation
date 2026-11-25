"""Tests never reach a real phone: any adb call a test didn't fake fails."""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def _no_real_adb(monkeypatch):
    real = subprocess.run

    def guard(cmd, *a, **kw):
        if cmd and str(cmd[0]).endswith("adb"):
            raise AssertionError(f"test tried a real adb call: {cmd}")
        return real(cmd, *a, **kw)

    monkeypatch.setattr(subprocess, "run", guard)
