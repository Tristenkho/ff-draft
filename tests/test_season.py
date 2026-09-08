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


if __name__ == "__main__":
    unittest.main()
