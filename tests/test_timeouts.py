import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import utils.timeouts as timeouts

from utils.timeouts import reset_state_if_timeout


def make_fixed_datetime(timestamp):
    class FixedDatetime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime.fromtimestamp(timestamp)
    return FixedDatetime


def test_update_last_ts_when_missing(monkeypatch):
    monkeypatch.setattr(
        timeouts.datetime,
        "datetime",
        make_fixed_datetime(1000),
    )
    state = {"data": {}}
    result = reset_state_if_timeout(state, timeout_seconds=10)
    assert result is state
    assert result["last_ts"] == 1000
    assert result["data"] == {}


def test_full_reset_when_timeout_exceeded(monkeypatch):
    monkeypatch.setattr(
        timeouts.datetime,
        "datetime",
        make_fixed_datetime(2000),
    )
    state = {
        "data": {"a": 1},
        "step": 2,
        "level": "L1",
        "flight_options": [1],
        "hotel_options": [2],
        "last_ts": 100,
    }
    result = reset_state_if_timeout(state, timeout_seconds=1800)
    assert result != state
    assert result == {
        "data": {},
        "step": 0,
        "level": "L1",
        "flight_options": [],
        "hotel_options": [],
        "seen_flights": [],
        "seen_hotels": [],
        "last_ts": 2000,
    }
