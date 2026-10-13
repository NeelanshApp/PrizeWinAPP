from copy import deepcopy
import json
import random
import unittest

from session_model import (
    confirm, export_backup, fresh_state, import_backup, invalidate, replace_purchases,
    suggest, undo_purchase,
)
from ticket_logic import ValidationError


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.state = fresh_state()

    def test_fresh_states_are_independent(self):
        self.state["purchased"].clear()
        self.state["availability"]["1"] = "Unavailable"
        self.assertEqual(fresh_state()["purchased"], ["20397"])
        self.assertEqual(fresh_state()["availability"]["1"], "Available")

    def test_suggestion_stable_until_relevant_change(self):
        suggest(self.state, "15786", rng=random.Random(2))
        original = deepcopy(self.state["suggestion"])
        invalidate(self.state, "15786")
        self.assertEqual(self.state["suggestion"], original)
        for change in ["first", "last", "excluded", "availability", "purchased", "maximum"]:
            state = deepcopy(self.state)
            args = ["15786", "", ""]
            if change == "first": args[0] = "15787"
            if change == "last": args[1] = "15799"
            if change == "excluded": args[2] = "15788"
            if change == "availability": state["availability"]["1"] = "Unknown"
            if change == "purchased": state["purchased"].append("10001")
            if change == "maximum": state["settings"]["max_ticket"] = 39998
            invalidate(state, *args)
            self.assertIsNone(state["suggestion"], change)

    def test_confirmation_only_once_and_undo(self):
        suggest(self.state, "15800")
        self.assertEqual(self.state["purchased"], ["20397"])
        self.assertEqual(confirm(self.state, "15800"), "15800")
        with self.assertRaises(ValidationError):
            confirm(self.state, "15800")
        self.assertEqual(self.state["purchased"], ["20397", "15800"])
        self.assertEqual(undo_purchase(self.state), "15800")
        self.assertEqual(self.state["purchased"], ["20397"])
        with self.assertRaises(ValidationError):
            undo_purchase(self.state)

    def test_stale_confirm_revalidates(self):
        suggest(self.state, "15800")
        with self.assertRaises(ValidationError):
            confirm(self.state, "15800", excluded="15800")
        self.assertEqual(self.state["purchased"], ["20397"])

    def test_cannot_confirm_eleventh_ticket(self):
        suggest(self.state, "15800")
        self.state["purchased"] = [f"1000{d}" for d in range(10)]
        with self.assertRaises(ValidationError):
            confirm(self.state, "15800")
        self.assertEqual(len(self.state["purchased"]), 10)

    def test_bad_edits_are_atomic_and_empty_list_removes_seed(self):
        for bad in ["342 nonsense", "20397 20397", " ".join(str(n) for n in range(1, 12))]:
            before = deepcopy(self.state)
            with self.assertRaises(ValidationError):
                replace_purchases(self.state, bad)
            self.assertEqual(self.state, before)
        replace_purchases(self.state, "")
        self.assertEqual(self.state["purchased"], [])

    def test_round_trip_strings_and_settings(self):
        replace_purchases(self.state, "342 20397")
        self.state["availability"]["0"] = "Available"
        self.state["settings"]["max_ticket"] = 35000
        restored = import_backup(export_backup(self.state).encode())
        self.assertEqual(restored, self.state)
        self.assertIn('"00342"', export_backup(self.state))

    def test_malformed_backups_do_not_change_live_state(self):
        baseline = deepcopy(self.state)
        valid = json.loads(export_backup(self.state))
        bad_records = [None, [], {}, {**valid, "version": True}, {**valid, "version": 2},
                       {**valid, "purchased": ["00001"] * 2}, {**valid, "purchased": [1]},
                       {**valid, "purchased": ["1,2"]}, {**valid, "purchased": ["00000"]},
                       {**valid, "purchased": [str(n) for n in range(1, 12)]},
                       {**valid, "availability": {"0": "Available"}},
                       {**valid, "settings": {"max_ticket": True}},
                       {**valid, "settings": {"max_ticket": 40000}}]
        for value in bad_records:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                import_backup(json.dumps(value))
            self.assertEqual(self.state, baseline)
        for raw in [b"{broken", b"\xff", b" " * 65537, b'{"version":1,"version":2}', b"[" * 2000]:
            with self.subTest(raw=raw[:20]), self.assertRaises(ValidationError):
                import_backup(raw)
            self.assertEqual(self.state, baseline)

    def test_backup_limit_counts_utf8_bytes(self):
        data = json.loads(export_backup(self.state))
        data["note"] = "\u00e9" * 33000
        payload = json.dumps(data, ensure_ascii=False)
        self.assertLess(len(payload), 65536)
        self.assertGreater(len(payload.encode("utf-8")), 65536)
        for value in (payload, payload.encode("utf-8")):
            with self.assertRaisesRegex(ValidationError, "64 KiB"):
                import_backup(value)
        with self.assertRaisesRegex(ValidationError, "UTF-8"):
            import_backup("\ud800")


if __name__ == "__main__":
    unittest.main()
