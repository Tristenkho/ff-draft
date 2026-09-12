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


def rostered(pid, projection, slot_id=20, *, name=None, pos="RB", nfl_team="PIT", **kw):
    p = player(pid, projection, slot_id=slot_id, **kw)
    p.update(name=name or f"Player {pid}", pos=pos, slot=service.SLOTS[slot_id], nfl_team=nfl_team,
             opponent="vs ATL" if p["kickoff"] else None)
    return p


def sync(snapshot_id, at, roster, *, week=1, others=()):
    return {"snapshot_id": snapshot_id, "data_as_of": at, "week": week,
            "teams": [{"id": 5, "roster": roster}, {"id": 6, "roster": list(others)}]}


RB_FLEX = [{"id": 2, "label": "RB", "count": 1}, {"id": 23, "label": "FLEX", "count": 1}]


def team_snapshot(roster, *, ir_slots=2, slots=RB_FLEX):
    return service.enrich({"rules": {"lineup_slots": slots, "ir_slots": ir_slots},
                           "league": {"my_team_id": 5}, "teams": [{"id": 5, "roster": roster}]})


class TeamChangesTests(unittest.TestCase):
    T1 = "2026-09-08T00:00:00+00:00"
    T2 = "2026-09-09T00:00:00+00:00"
    T3 = "2026-09-10T00:00:00+00:00"

    def changes(self, *syncs):
        return [(e["kind"], e["name"], e["from"], e["to"]) for e in service.team_changes(list(syncs), 5)]

    def test_a_status_change_is_dated_by_the_first_sync_that_saw_it(self):
        brown = dict(name="A.J. Brown", pos="WR")
        events = service.team_changes([
            sync("a", self.T1, [rostered(1, 13.2, 4, **brown)]),
            sync("b", self.T2, [rostered(1, 13.2, 4, **brown)]),
            sync("c", self.T3, [rostered(1, 13.2, 4, status="INJURY_RESERVE", **brown)])], 5)
        self.assertEqual([(e["kind"], e["from"], e["to"]) for e in events], [("status", "ACTIVE", "INJURY_RESERVE")])
        self.assertEqual((events[0]["observed_at"], events[0]["previous_observed_at"]), (self.T3, self.T2))
        self.assertIn("Active → Injured reserve", events[0]["detail"])

    def test_newest_sync_comes_first(self):
        events = service.team_changes([
            sync("a", self.T1, [rostered(1, 10, status="QUESTIONABLE")]),
            sync("b", self.T2, [rostered(1, 10)]),
            sync("c", self.T3, [rostered(1, 10, status="OUT")])], 5)
        self.assertEqual([e["to"] for e in events], ["OUT", "ACTIVE"])

    def test_a_flex_swap_reports_both_players(self):
        self.assertCountEqual(self.changes(
            sync("a", self.T1, [rostered(1, 11.2, 23, name="Burden"), rostered(2, 12.6, 20, name="Warren")]),
            sync("b", self.T2, [rostered(1, 11.2, 20, name="Burden"), rostered(2, 12.6, 23, name="Warren")])),
            [("slot", "Burden", "FLEX", "Bench"), ("slot", "Warren", "Bench", "FLEX")])

    def test_adds_and_drops(self):
        self.assertCountEqual(self.changes(
            sync("a", self.T1, [rostered(1, 5.1, name="Rodriguez")]),
            sync("b", self.T2, [rostered(2, 8.4, name="Holani")])),
            [("added", "Holani", None, "Bench"), ("dropped", "Rodriguez", "Bench", None)])

    def test_only_projection_moves_of_two_points_are_reported(self):
        self.assertEqual(self.changes(
            sync("a", self.T1, [rostered(1, 12.6), rostered(2, 5.1)]),
            sync("b", self.T2, [rostered(1, 13.8), rostered(2, 7.6)])),
            [("projection", "Player 2", 5.1, 7.6)])

    def test_projections_are_not_compared_across_weeks(self):
        self.assertEqual(self.changes(
            sync("a", self.T1, [rostered(1, 18.6)], week=1),
            sync("b", self.T2, [rostered(1, 10.0)], week=2)), [])

    def test_a_player_without_a_game_is_not_reported_as_traded(self):
        scheduled = sync("a", self.T1, [rostered(1, 10, nfl_team="NE")])
        bye = sync("b", self.T2, [rostered(1, 10, nfl_team="PHI", kickoff=None)])
        self.assertEqual(self.changes(scheduled, bye), [])
        moved = sync("c", self.T3, [rostered(1, 10, nfl_team="PHI")])
        self.assertEqual(self.changes(scheduled, moved), [("nfl_team", "Player 1", "NE", "PHI")])

    def test_other_teams_are_ignored(self):
        self.assertEqual(self.changes(
            sync("a", self.T1, [rostered(1, 10)], others=[rostered(9, 10)]),
            sync("b", self.T2, [rostered(1, 10)], others=[rostered(9, 10, status="OUT")])), [])


class RosterAlertTests(unittest.TestCase):
    def alerts(self, roster, **kw):
        return service.roster_alerts(team_snapshot(roster, **kw), 5)

    def starters(self, first=None):
        """RB 13.7 and FLEX 12.6 starting, a 9.8 back on the bench: nothing to flag."""
        return [first or rostered(1, 13.7, 2, eligible=(2, 23)), rostered(2, 12.6, 23, eligible=(2, 23)),
                rostered(3, 9.8, eligible=(2, 23))]

    def test_a_sound_lineup_flags_nothing(self):
        self.assertEqual(self.alerts(self.starters()), [])

    def test_a_projection_gap_names_the_swap_and_calls_it_a_lean(self):
        roster = [rostered(1, 13.7, 2, eligible=(2, 23)),
                  rostered(2, 11.2, 23, eligible=(23,), name="Luther Burden III"),
                  rostered(3, 12.6, eligible=(2, 23), name="Jaylen Warren")]
        [alert] = self.alerts(roster)
        self.assertEqual(alert["title"], "Start Jaylen Warren over Luther Burden III")
        self.assertEqual(alert["severity"], "check")
        self.assertIn("+1.4", alert["detail"])
        self.assertEqual(alert["player_ids"], [3, 2])

    def test_a_large_projection_gap_is_an_action(self):
        roster = [rostered(1, 13.7, 2, eligible=(2, 23)), rostered(2, 4.0, 23, eligible=(23,)),
                  rostered(3, 12.6, eligible=(2, 23))]
        self.assertEqual([(a["id"], a["severity"]) for a in self.alerts(roster)], [("lineup-gap", "act")])

    def test_an_out_starter_before_kickoff_must_be_replaced(self):
        alerts = self.alerts(self.starters(rostered(1, 0, 2, eligible=(2, 23), status="OUT")))
        self.assertEqual([(a["id"], a["severity"]) for a in alerts],
                         [("starter-status-1", "act"), ("lineup-gap", "act")])
        self.assertEqual(alerts[0]["act_by"], FUTURE)
        # ESPN's strongest lineup already benches the out player, so the fix is named.
        self.assertEqual(alerts[1]["title"], "Start Player 3 over Player 1")

    def test_a_questionable_starter_is_a_check_before_kickoff(self):
        [alert] = self.alerts(self.starters(rostered(1, 13.7, 2, eligible=(2, 23), status="QUESTIONABLE")))
        self.assertEqual((alert["id"], alert["severity"], alert["act_by"]), ("starter-status-1", "check", FUTURE))

    def test_locked_starters_are_left_alone(self):
        done = rostered(1, 0, 2, eligible=(2, 23), status="OUT", game_state="post", actual=5.1)
        self.assertEqual(self.alerts(self.starters(done)), [])

    def test_injured_reserve_in_a_locked_slot_waits_for_the_unlock(self):
        brown = rostered(1, 13.2, 2, eligible=(2, 23, 21), status="INJURY_RESERVE", game_state="post",
                         actual=5.1, name="A.J. Brown")
        [alert] = self.alerts(self.starters(brown))
        self.assertEqual((alert["severity"], alert["title"]), ("later", "Move A.J. Brown to IR once the lineup unlocks"))
        self.assertIn("2 of 2 IR slots open", alert["detail"])

    def test_injured_reserve_on_the_bench_can_move_now(self):
        [alert] = self.alerts(self.starters() + [rostered(4, 0, status="INJURY_RESERVE")])
        self.assertEqual((alert["id"], alert["severity"]), ("ir-4", "act"))

    def test_a_full_ir_is_a_check_not_an_action(self):
        roster = self.starters() + [rostered(5, 0, 21, status="OUT"), rostered(4, 0, status="INJURY_RESERVE")]
        [alert] = self.alerts(roster, ir_slots=1)
        self.assertEqual((alert["severity"], alert["title"]), ("check", "No open IR slot for Player 4"))

    def test_unknown_ir_capacity_defers_to_espn(self):
        [alert] = self.alerts(self.starters() + [rostered(4, 0, status="INJURY_RESERVE")], ir_slots=None)
        self.assertIn("Check how many IR slots are open in ESPN", alert["detail"])

    def test_an_empty_slot_is_flagged(self):
        [alert] = self.alerts([rostered(1, 13.7, 2, eligible=(2, 23))])
        self.assertEqual((alert["id"], alert["detail"]), ("empty-slot", "Nothing is starting at FLEX."))

    def test_a_starter_with_no_game_is_flagged(self):
        alerts = self.alerts(self.starters(rostered(1, 0, 2, eligible=(2, 23), kickoff=None)))
        self.assertCountEqual([a["id"] for a in alerts], ["no-game-1", "lineup-gap"])

    def test_actions_sort_ahead_of_checks(self):
        roster = self.starters(rostered(1, 13.7, 2, eligible=(2, 23), status="QUESTIONABLE"))
        roster.append(rostered(4, 0, status="INJURY_RESERVE"))
        self.assertEqual([a["severity"] for a in self.alerts(roster)], ["act", "check"])

    def test_a_team_missing_from_the_snapshot_has_no_alerts(self):
        self.assertEqual(service.roster_alerts(team_snapshot(self.starters()), 99), [])


class OverviewChangeLogTests(unittest.TestCase):
    def test_overview_reports_the_week_and_the_sync_before_it(self):
        def stored(snapshot_id, at, week, roster):
            return {"schema_version": 1, "snapshot_id": snapshot_id, "generated_at": at, "data_as_of": at,
                    "season": 2026, "week": week, "league": {"my_team_id": 5},
                    "rules": {"lineup_slots": [{"id": 2, "label": "RB", "count": 1}], "ir_slots": 2},
                    "teams": [{"id": 5, "roster": roster}], "warnings": [], "source_health": []}
        rows = [stored("w1", "2026-09-08T00:00:00+00:00", 1, [rostered(1, 10, 2)]),
                stored("w2a", "2026-09-15T00:00:00+00:00", 2, [rostered(1, 10, 2, status="QUESTIONABLE")]),
                stored("w2b", "2026-09-16T00:00:00+00:00", 2,
                       [rostered(1, 10, 2, status="QUESTIONABLE"), rostered(2, 8)])]
        with tempfile.TemporaryDirectory() as temp, patch.object(service, "DATA", Path(temp)), \
                patch.object(service, "DB", Path(temp) / "season.sqlite3"):
            with service.connect() as conn:
                for s in rows:
                    conn.execute("INSERT INTO snapshots VALUES (?,?,?,?,?)",
                                 (s["snapshot_id"], s["season"], s["week"], s["data_as_of"], json.dumps(s)))
            view = service.get_overview(2026, 2)
        changes = view["team_changes"]
        self.assertEqual((changes["since"], changes["syncs_compared"]), ("2026-09-08T00:00:00+00:00", 3))
        self.assertEqual([(e["kind"], e["player_id"]) for e in changes["events"]], [("added", 2), ("status", 1)])
        self.assertEqual([a["id"] for a in view["attention"]], ["starter-status-1"])


LEAGUE_SCORING = [
    {"stat_id": "3", "points": 0.04}, {"stat_id": "4", "points": 4}, {"stat_id": "24", "points": 0.1},
    {"stat_id": "25", "points": 6}, {"stat_id": "26", "points": 2}, {"stat_id": "42", "points": 0.1},
    {"stat_id": "43", "points": 6}, {"stat_id": "53", "points": 0.5}, {"stat_id": "72", "points": -2},
    {"stat_id": "211", "points": 0.1}, {"stat_id": "212", "points": 0.25}, {"stat_id": "213", "points": 0.5},
    {"stat_id": "95", "points": 0, "overrides": {"16": 2}}, {"stat_id": "99", "points": 0, "overrides": {"16": 1}},
]
# ESPN's Week 2 projected stat lines as returned on 2026-09-12; ESPN's totals were
# 10.69 for Warren and 11.21 for Burden.
WARREN_WEEK2 = {"23": 10.34, "24": 44.81, "25": 0.23, "26": 0.01, "42": 18.64, "43": 0.08, "53": 2.77,
                "58": 3.43, "72": 0.05, "212": 2.44, "213": 1.11}
BURDEN_WEEK2 = {"23": 0.55, "24": 2.94, "25": 0.02, "42": 54.68, "43": 0.31, "53": 4.32,
                "58": 6.56, "72": 0.04, "212": 0.27, "213": 2.55}


class ProjectionBreakdownTests(unittest.TestCase):
    def warren(self, total=10.69):
        return service.projection_breakdown(WARREN_WEEK2, LEAGUE_SCORING, "RB", total)

    def test_categories_reproduce_espns_total(self):
        breakdown = self.warren()
        self.assertTrue(breakdown["reconciled"])
        self.assertEqual([g["label"] for g in breakdown["groups"]],
                         ["Rushing yards", "Receiving yards", "Receptions", "First downs", "Touchdowns", "Turnovers"])
        self.assertAlmostEqual(sum(g["points"] for g in breakdown["groups"]), 10.69, delta=0.15)

    def test_first_downs_are_their_own_category(self):
        first_downs = next(g for g in self.warren()["groups"] if g["label"] == "First downs")
        self.assertAlmostEqual(first_downs["points"], 2.44 * 0.25 + 1.11 * 0.5, delta=0.01)

    def test_usage_is_reported_beside_the_points(self):
        volume = {v["label"]: v["value"] for v in self.warren()["volume"]}
        self.assertEqual((volume["Carries"], volume["Targets"], volume["Rushing first downs"]), (10.3, 3.4, 2.4))

    def test_defense_points_come_from_the_dst_slot_override(self):
        line = {"99": 2.27, "95": 0.82}
        dst = service.projection_breakdown(line, LEAGUE_SCORING, "DST", 3.91)
        self.assertEqual([(g["label"], g["points"]) for g in dst["groups"]], [("Sacks", 2.27), ("Takeaways", 1.64)])
        self.assertTrue(dst["reconciled"])
        # The same stats score nothing for a position without the override.
        self.assertEqual(service.projection_breakdown(line, LEAGUE_SCORING, "RB", 0)["groups"], [])

    def test_a_breakdown_that_misses_espns_total_is_flagged(self):
        self.assertFalse(self.warren(total=15.0)["reconciled"])
        self.assertFalse(self.warren(total=None)["reconciled"])

    def test_enrich_scores_rostered_and_free_agents_and_drops_the_raw_line(self):
        rostered_player = dict(rostered(1, 11.21, 23, eligible=(4, 23), pos="WR"), projected_stats=dict(BURDEN_WEEK2))
        free_agent = dict(rostered(9, 10.69, eligible=(2, 23)), projected_stats=dict(WARREN_WEEK2))
        view = service.enrich({"rules": {"lineup_slots": RB_FLEX, "scoring": LEAGUE_SCORING},
                               "league": {"my_team_id": 5}, "teams": [{"id": 5, "roster": [rostered_player]}],
                               "free_agents": [free_agent]})
        for p in (view["teams"][0]["roster"][0], view["free_agents"][0]):
            self.assertNotIn("projected_stats", p)
            self.assertTrue(p["breakdown"]["reconciled"])


class ComparePlayersTests(unittest.TestCase):
    WARREN, BURDEN, BROWN, BLACK, HOLANI, CHARGERS = 4569987, 4685278, 4047646, 4696044, 4429835, -16024

    def overview(self, briefing=None):
        roster = [rostered(1, 13.7, 2, eligible=(2, 23), name="Cam Skattebo"),
                  rostered(2, 18.6, 4, eligible=(4, 23), name="Ja'Marr Chase", pos="WR"),
                  rostered(self.BROWN, 13.2, 4, eligible=(4, 23, 21), name="A.J. Brown", pos="WR",
                           game_state="post", actual=5.1),
                  rostered(self.WARREN, 12.6, 20, eligible=(2, 23), name="Jaylen Warren"),
                  rostered(self.BURDEN, 11.2, 23, eligible=(4, 23), name="Luther Burden III", pos="WR"),
                  rostered(self.CHARGERS, 6.7, 16, eligible=(16,), name="Chargers D/ST", pos="DST")]
        free_agents = [dict(rostered(self.BLACK, 8.5, eligible=(2, 23), name="Kaelon Black"), availability="WAIVERS"),
                       dict(rostered(self.HOLANI, 12.4, eligible=(2, 23), name="George Holani"), availability="WAIVERS")]
        slots = [{"id": 2, "label": "RB", "count": 1}, {"id": 4, "label": "WR", "count": 2},
                 {"id": 23, "label": "FLEX", "count": 1}, {"id": 16, "label": "D/ST", "count": 1}]
        return service.enrich({"snapshot_id": "snap", "season": 2026, "week": 1, "rules": {"lineup_slots": slots},
                               "league": {"my_team_id": 5}, "teams": [{"id": 5, "name": "Tristen", "roster": roster}],
                               "free_agents": free_agents, "briefing": briefing})

    def test_names_the_leader_and_calls_a_small_edge_a_lean(self):
        result = service.compare_players(self.overview(), [self.BURDEN, self.WARREN])
        self.assertEqual((result["leader_id"], result["edge"], result["strength"]), (self.WARREN, 1.4, "lean"))
        self.assertEqual([p["name"] for p in result["players"]], ["Luther Burden III", "Jaylen Warren"])
        self.assertEqual(result["players"][0]["owner"], "Tristen")

    def test_a_near_tie_is_not_called_a_lean(self):
        result = service.compare_players(self.overview(), [self.WARREN, self.HOLANI])
        self.assertEqual(result["strength"], "none")

    def test_shared_slots_and_the_earliest_unlocked_kickoff(self):
        result = service.compare_players(self.overview(), [self.WARREN, self.BURDEN, self.BROWN])
        self.assertEqual(result["shared_slots"], ["FLEX"])
        # Brown's game is over, so only the unlocked players set the deadline.
        self.assertEqual(result["decide_by"], FUTURE)

    def test_a_roster_decision_across_positions_has_no_shared_slot(self):
        result = service.compare_players(self.overview(), [self.BLACK, self.CHARGERS])
        self.assertEqual(result["shared_slots"], [])
        self.assertIsNone(result["players"][0]["owner"])

    def test_research_mentioning_either_player_comes_along(self):
        briefing = {"decisions": [{"id": "flex", "player_ids": [self.WARREN, self.BURDEN]}, {"id": "k", "player_ids": [7]}],
                    "news": [{"title": "Burden cleared", "player_ids": [self.BURDEN]}]}
        result = service.compare_players(self.overview(briefing), [self.WARREN, self.BURDEN])
        self.assertEqual([d["id"] for d in result["decisions"]], ["flex"])
        self.assertEqual([n["title"] for n in result["news"]], ["Burden cleared"])

    def test_rejects_unknown_players_and_a_single_player(self):
        with self.assertRaises(LookupError):
            service.compare_players(self.overview(), [self.WARREN, 999])
        with self.assertRaises(ValueError):
            service.compare_players(self.overview(), [self.WARREN, str(self.WARREN)])


if __name__ == "__main__":
    unittest.main()
