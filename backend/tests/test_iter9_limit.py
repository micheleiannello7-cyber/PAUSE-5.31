"""Iteration 9 — enforced 4h pause, session_seconds accumulation, and random discover."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------------- limit-check: enforce=true + session_seconds ----------------
class TestLimitCheckEnforce:
    def test_new_user_enforce_true(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        r = s.get(f"{API}/user/{uid}/limit-check")
        assert r.status_code == 200
        d = r.json()
        assert d["enforce"] is True, f"expected enforce=true, got {d}"
        assert d["blocked"] is False
        assert d["session_count"] == 0
        assert d["session_seconds"] == 0
        assert d["limit"] == 5

    def test_complete_accumulates_seconds(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        totals = [42, 60, 75]
        for i, secs in enumerate(totals):
            r = s.post(f"{API}/user/complete", json={
                "user_id": uid, "story_id": f"iter9-fake-{i}", "minutes": 2, "seconds": secs,
            })
            assert r.status_code == 200
            d = r.json()
            assert d["session_count"] == i + 1
            assert d["session_seconds"] == sum(totals[: i + 1])
        # verify via limit-check as well
        lc = s.get(f"{API}/user/{uid}/limit-check").json()
        assert lc["session_seconds"] == sum(totals)
        assert lc["session_count"] == 3
        assert lc["blocked"] is False

    def test_five_completes_block_and_sum(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        secs = [30, 40, 50, 60, 70]
        for i, sec in enumerate(secs):
            r = s.post(f"{API}/user/complete", json={
                "user_id": uid, "story_id": f"iter9-blk-{i}", "minutes": 2, "seconds": sec,
            })
            assert r.status_code == 200
        lc = s.get(f"{API}/user/{uid}/limit-check").json()
        assert lc["enforce"] is True
        assert lc["session_count"] == 5
        assert lc["reached"] is True
        assert lc["blocked"] is True, f"expected blocked after 5 completes, got {lc}"
        assert lc["session_seconds"] == sum(secs)
        assert lc["blocked_until"], "blocked_until should be set"
        # remaining_seconds should be ~4h (14400s), tolerate small delta
        assert 14000 <= lc["remaining_seconds"] <= 14400

    def test_same_story_doesnt_double_count_seconds(self, s):
        uid = f"TEST_{uuid.uuid4()}"
        s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "dup", "minutes": 2, "seconds": 33})
        r = s.post(f"{API}/user/complete", json={"user_id": uid, "story_id": "dup", "minutes": 2, "seconds": 99})
        d = r.json()
        assert d["session_count"] == 1
        assert d["session_seconds"] == 33, f"expected 33 (no double-add), got {d['session_seconds']}"


# ---------------- discover-next randomization ----------------
class TestDiscoverRandom:
    def test_repeated_first_call_varies(self, s):
        """With no completions, call /discover-next 12 times for fresh users;
        expect >=3 distinct first stories (MongoDB $sample)."""
        seen = set()
        for _ in range(12):
            uid = f"TEST_{uuid.uuid4()}"
            r = s.get(f"{API}/discover-next", params={"user_id": uid, "interests": "scienza,spazio,storia,natura"})
            assert r.status_code == 200
            seen.add(r.json()["id"])
        assert len(seen) >= 3, f"discover-next appears non-random; got only {seen}"


# ---------------- Pausedemo seed for pause-limit UI test ----------------
class TestSeedPauseDemo:
    """Seed 'pausedemo' with a blocked session for the frontend pause-screen test."""

    def test_seed_pausedemo_blocked(self, s):
        uid = "pausedemo"
        # Ensure a clean slate — post 5 completes; each accumulates seconds.
        # If already blocked from a prior run, backend still increments up to
        # existing sequence (was_new=False for duplicates). Use unique ids
        # to force new counts on first-run environments.
        secs = [50, 60, 70, 71, 70]  # total = 321
        for i, sec in enumerate(secs):
            s.post(f"{API}/user/complete", json={
                "user_id": uid, "story_id": f"pausedemo-seed-{i}", "minutes": 2, "seconds": sec,
            })
        lc = s.get(f"{API}/user/{uid}/limit-check").json()
        assert lc["session_count"] >= 5
        # blocked_until may already have been set from a prior run, in which
        # case the newly-summed seconds accumulate on top. We only need it to
        # be blocked and >= our seeded amount for the UI probe.
        assert lc["blocked"] is True, f"pausedemo must be blocked, got {lc}"
        assert lc["session_seconds"] >= sum(secs) - 1
