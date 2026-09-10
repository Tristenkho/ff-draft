import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from season import service


FUTURE = "2099-09-13T18:00:00+00:00"


def player(pid, projection, *, eligible=(2,), slot_id=20, status="ACTIVE",
           game_state="pre", kickoff=FUTURE, actual=None):
    return {
        "id": pid,
        "name": f"Player {pid}",
        "projection": projection,
        "actual": actual,
        "eligible_slots": list(eligible),
        "slot_id": slot_id,
        "status": status,
        "game_state": game_state,
        "kickoff": kickoff,
        "locked": False,
    }


def slot(slot_id, label=None):
    return {"id": slot_id, "label": label or service.SLOTS.get(slot_id, str(slot_id))}


class LineupTests(unittest.TestCase):
    def test_locked_bench_is_reserved_and_excluded(self):
        locked_bench = player(1, 100, slot_id=20)
        locked_bench["locked"] = True
        available = player(2, 10)

        result = service.optimize([locked_bench, available], [slot(2, "RB")])

        self.assertEqual([a["player_id"] for a in result["assignments"]], [2])

    def test_locked_starter_is_fixed_even_when_another_player_projects_higher(self):
        locked_starter = player(1, 5, slot_id=2, game_state="in")
        locked_starter["locked"] = True
        higher = player(2, 50)

        result = service.optimize([locked_starter, higher], [slot(2, "RB")])

        self.assertEqual(result["assignments"][0]["player_id"], 1)

    def test_unavailable_players_are_excluded_unless_locked(self):
        out = player(1, 100, status="OUT")
        usable = player(2, 10)
        result = service.optimize([out, usable], [slot(2, "RB")])
        self.assertEqual(result["assignments"][0]["player_id"], 2)

        locked_out = player(3, 1, slot_id=2, status="OUT", game_state="in")
        locked_out["locked"] = True
        result = service.optimize([locked_out, usable], [slot(2, "RB")])
        self.assertEqual(result["assignments"][0]["player_id"], 3)

    def test_player_cannot_fill_rb_and_flex_twice(self):
        rb = player(1, 30, eligible=(2, 23))
        wr = player(2, 20, eligible=(23,))

        result = service.optimize([rb, wr], [slot(2, "RB"), slot(23, "FLEX")])

        assigned = [a["player_id"] for a in result["assignments"]]
        self.assertEqual(len(assigned), 2)
        self.assertEqual(len(set(assigned)), 2)
        self.assertEqual(assigned, [1, 2])

    def test_missing_projection_is_not_treated_as_zero(self):
        missing = player(1, None)
        projected = player(2, 0.1)
        result = service.optimize([missing, projected], [slot(2, "RB")])
        self.assertEqual(result["assignments"][0]["player_id"], 2)

        incomplete = service.lineup(
            [missing], [slot(2, "RB")],
            [{"slot_id": 2, "slot": "RB", "player_id": 1}],
        )
        self.assertIsNone(incomplete["projection"])
        self.assertFalse(incomplete["complete"])

    def test_unfillable_slot_produces_incomplete_lineup(self):
        result = service.optimize([player(1, 20, eligible=(2,))], [slot(2, "RB"), slot(4, "WR")])

        self.assertFalse(result["complete"])
        self.assertEqual(len(result["assignments"]), 1)

    def test_equal_flex_values_prefer_later_kickoff(self):
        early = player(1, 20, eligible=(23,), kickoff="2099-09-13T17:00:00+00:00")
        late = player(2, 20, eligible=(23,), kickoff="2099-09-13T21:00:00+00:00")

        result = service.optimize([early, late], [slot(23, "FLEX")])

        self.assertEqual(result["assignments"][0]["player_id"], 2)

    def test_in_progress_lineup_reports_actual_and_partial_projection(self):
        started = player(1, 12, game_state="in", actual=4)
        started["locked"] = True
        upcoming = player(2, 18)
        result = service.lineup(
            [started, upcoming], [slot(2, "RB"), slot(23, "FLEX")],
            [
                {"slot_id": 2, "slot": "RB", "player_id": 1},
                {"slot_id": 23, "slot": "FLEX", "player_id": 2},
            ],
        )

        self.assertEqual(result["actual"], 4)
        self.assertEqual(result["remaining_projection"], 18)
        self.assertTrue(result["in_progress"])
        self.assertFalse(result["complete"])


class ScheduleAndBriefingTests(unittest.TestCase):
    def test_schedule_map_rejects_wrong_week(self):
        payload = {"season": {"year": 2026}, "week": {"number": 2}, "events": []}
        with self.assertRaisesRegex(ValueError, "different season/week"):
            service.schedule_map(payload, 2026, 1)

    def _snapshot(self, snapshot_id="snap-1"):
        return {
            "schema_version": 1,
            "snapshot_id": snapshot_id,
            "generated_at": "2026-09-07T00:00:00+00:00",
            "data_as_of": "2026-09-07T00:00:00+00:00",
            "season": 2026,
            "week": 1,
            "rules": {"lineup_slots": []},
            "teams": [],
            "warnings": [],
            "source_health": [],
        }

    def _briefing(self, snapshot_id="snap-1"):
        return {
            "title": "Week 1 briefing",
            "season": 2026,
            "week": 1,
            "generated_at": "2026-09-07T01:00:00+00:00",
            "snapshot_id": snapshot_id,
            "summary": "Synthetic briefing",
            "coverage_note": "Synthetic sources only",
            "decisions": [{"text": "Start player 1", "source_ids": ["unknown"]}],
            "news": [],
            "sources": [{"id": "known", "url": "https://example.com/source"}],
            "trade_ideas": [],
            "watchlist": [],
        }

    def _with_temp_db(self):
        temp = tempfile.TemporaryDirectory()
        data = Path(temp.name)
        db = data / "season.sqlite3"
        patcher = patch.object(service, "DATA", data), patch.object(service, "DB", db)
        return temp, patcher

    def test_import_briefing_rejects_unknown_evidence_source(self):
        temp, (data_patch, db_patch) = self._with_temp_db()
        with temp, data_patch, db_patch:
            with service.connect() as conn:
                snapshot = self._snapshot()
                conn.execute(
                    "INSERT INTO snapshots VALUES (?,?,?,?,?)",
                    ("snap-1", 2026, 1, snapshot["generated_at"], json.dumps(snapshot)),
                )
            path = Path(temp.name) / "briefing.json"
            path.write_text(json.dumps(self._briefing()))
            with self.assertRaisesRegex(ValueError, "Unknown evidence source"):
                service.import_briefing(path)

    def test_import_briefing_rejects_snapshot_mismatch(self):
        temp, (data_patch, db_patch) = self._with_temp_db()
        with temp, data_patch, db_patch:
            with service.connect() as conn:
                snapshot = self._snapshot()
                conn.execute(
                    "INSERT INTO snapshots VALUES (?,?,?,?,?)",
                    ("snap-1", 2026, 1, snapshot["generated_at"], json.dumps(snapshot)),
                )
            path = Path(temp.name) / "briefing.json"
            path.write_text(json.dumps(self._briefing("stale-snapshot")))
            with self.assertRaisesRegex(ValueError, "latest snapshot"):
                service.import_briefing(path)

    def _import(self, briefing):
        temp, (data_patch, db_patch) = self._with_temp_db()
        with temp, data_patch, db_patch:
            with service.connect() as conn:
                snapshot = self._snapshot()
                conn.execute(
                    "INSERT INTO snapshots VALUES (?,?,?,?,?)",
                    ("snap-1", 2026, 1, snapshot["generated_at"], json.dumps(snapshot)),
                )
            path = Path(temp.name) / "briefing.json"
            path.write_text(json.dumps(briefing))
            return service.import_briefing(path)

    def _checkable(self, expects):
        briefing = self._briefing()
        briefing["decisions"] = [{"id": "flex", "source_ids": [], "expects": expects}]
        return briefing

    def test_import_rejects_an_unknown_expectation_key(self):
        with self.assertRaisesRegex(ValueError, "expects must be an object"):
            self._import(self._checkable({"activate": [1]}))

    def test_import_rejects_expectations_that_are_not_player_ids(self):
        with self.assertRaisesRegex(ValueError, r"expects\.start"):
            self._import(self._checkable({"start": ["Jaylen Warren"]}))

    def test_import_accepts_a_decision_with_no_expectations(self):
        briefing = self._briefing()
        briefing["decisions"] = [{"id": "prose", "source_ids": []}]
        self.assertEqual(self._import(briefing)["title"], "Week 1 briefing")


class WaiverWindowTests(unittest.TestCase):
    # Wednesday 2026-09-09 03:02 ET, the run this league actually performed.
    LAST_RUN = 1788937344712
    SETTINGS = {"waiverProcessDays": ["MONDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"],
                "waiverProcessHour": 11, "waiverHours": 24}

    def at(self, iso):
        return dt.datetime.fromisoformat(iso)

    def test_next_run_uses_the_observed_hour_not_the_reported_process_hour(self):
        window = service.waiver_window(self.SETTINGS, self.LAST_RUN, self.at("2026-09-09T21:00:00+00:00"))
        # Thursday is the next process day; 03:00 ET is 07:00 UTC. ESPN's own
        # waiverProcessHour of 11 would have produced 15:00 or 16:00 UTC.
        self.assertEqual(window["at"], "2026-09-10T07:00:00+00:00")
        self.assertTrue(window["verified"])

    def test_tuesday_is_skipped_because_the_league_does_not_process_then(self):
        window = service.waiver_window(self.SETTINGS, self.LAST_RUN, self.at("2026-09-14T12:00:00+00:00"))
        self.assertEqual(window["at"], "2026-09-16T07:00:00+00:00")

    def test_a_run_later_the_same_day_is_still_ahead(self):
        window = service.waiver_window(self.SETTINGS, self.LAST_RUN, self.at("2026-09-10T01:00:00+00:00"))
        self.assertEqual(window["at"], "2026-09-10T07:00:00+00:00")

    def test_the_hour_holds_across_the_dst_change(self):
        # 2026-11-01 ends US daylight time. The run must stay at 03:00 local,
        # which is 08:00 UTC, not slide to 07:00 UTC.
        window = service.waiver_window(self.SETTINGS, self.LAST_RUN, self.at("2026-11-04T12:00:00+00:00"))
        self.assertEqual(window["at"], "2026-11-05T08:00:00+00:00")

    def test_no_observed_run_is_unverified_rather_than_assumed(self):
        window = service.waiver_window(self.SETTINGS, None, self.at("2026-09-09T21:00:00+00:00"))
        self.assertIsNone(window["at"])
        self.assertFalse(window["verified"])

    def test_observed_run_on_a_day_the_settings_deny_is_not_trusted(self):
        settings = dict(self.SETTINGS, waiverProcessDays=["TUESDAY"])
        window = service.waiver_window(settings, self.LAST_RUN, self.at("2026-09-09T21:00:00+00:00"))
        self.assertIsNone(window["at"])
        self.assertFalse(window["verified"])


class DecisionReconciliationTests(unittest.TestCase):
    NAMES = {1: "Jaylen Warren", 2: "Luther Burden III", 3: "Chargers D/ST"}

    def reconcile(self, expects, starters=(1, 3), owned=(1, 2, 3)):
        return service.reconcile_decision(expects, set(starters), set(owned), self.NAMES)

    def test_start_and_bench_both_satisfied_is_executed(self):
        result = self.reconcile({"start": [1], "bench": [2]})
        self.assertEqual(result["state"], "executed")
        self.assertIn("Jaylen Warren starting", result["detail"])

    def test_unstarted_recommendation_is_not_executed(self):
        result = self.reconcile({"start": [2]})
        self.assertEqual(result["state"], "not executed")
        self.assertIn("Luther Burden III is not starting", result["detail"])

    def test_one_of_two_met_is_partly_executed(self):
        result = self.reconcile({"start": [1, 2]})
        self.assertEqual(result["state"], "partly executed")
        self.assertNotIn("Jaylen Warren is not", result["detail"])

    def test_a_benched_expectation_requires_ownership(self):
        # Dropping a player is not the same as benching him.
        self.assertEqual(self.reconcile({"bench": [9]})["state"], "not executed")

    def test_drop_is_met_only_when_the_player_is_gone(self):
        self.assertEqual(self.reconcile({"drop": [2]})["state"], "not executed")
        self.assertEqual(self.reconcile({"drop": [9]})["state"], "executed")

    def test_prose_only_decision_is_uncheckable_not_guessed(self):
        for expects in (None, {}, {"start": []}):
            self.assertEqual(self.reconcile(expects)["state"], "not checkable")

    def test_states_are_derived_against_my_team_only(self):
        snapshot = {
            "league": {"my_team_id": 5},
            "teams": [
                {"id": 5, "roster": [dict(player(1, 10, slot_id=23), name="Warren"),
                                     dict(player(2, 9, slot_id=20), name="Burden")]},
                {"id": 6, "roster": [dict(player(7, 8, slot_id=2), name="Someone else")]}],
            "free_agents": []}
        decisions = [{"id": "flex", "expects": {"start": [1], "bench": [2]}},
                     {"id": "theirs", "expects": {"start": [7]}}]

        service.decision_states(snapshot, decisions)

        self.assertEqual(decisions[0]["execution"]["state"], "executed")
        self.assertEqual(decisions[1]["execution"]["state"], "not executed")

if __name__ == "__main__":
    unittest.main()
