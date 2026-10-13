"""Streamlit interaction tests; install requirements.txt before running."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def launch(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)
        return app

    def check(self, app):
        self.assertFalse(app.exception)

    def test_seed_only_once_and_sessions_are_separate(self):
        app = self.launch()
        self.assertEqual(app.session_state["record"]["purchased"], ["20397"])
        app.text_area(key="purchase_text").input("").run()
        app.button(key="save_purchases").click().run()
        app.run()
        self.check(app)
        self.assertEqual(app.session_state["record"]["purchased"], [])
        other = self.launch()
        self.assertEqual(other.session_state["record"]["purchased"], ["20397"])

    def test_suggest_rerun_confirm_and_undo(self):
        app = self.launch()
        app.text_input(key="first").input("15800").run()
        app.button(key="suggest").click().run()
        self.assertEqual(app.session_state["record"]["suggestion"]["ticket"], "15800")
        app.run()
        self.assertEqual(app.session_state["record"]["suggestion"]["ticket"], "15800")
        app.button(key="another").click().run()
        self.assertEqual(app.session_state["record"]["suggestion"]["ticket"], "15800")
        app.button(key="confirm").click().run()
        app.run()
        self.check(app)
        self.assertEqual(app.session_state["record"]["purchased"], ["20397", "15800"])
        self.assertIsNone(app.session_state["record"]["suggestion"])
        app.button(key="undo").click().run()
        self.check(app)
        self.assertEqual(app.session_state["record"]["purchased"], ["20397"])

    def test_zero_confirmation_and_purchase_preserved_when_disabled(self):
        app = self.launch()
        app.text_input(key="first").input("00342").run()
        self.assertTrue(app.button(key="suggest").disabled)
        app.button(key="enable_zero").click().run()
        self.assertFalse(app.button(key="suggest").disabled)
        app.button(key="suggest").click().run()
        ticket = app.session_state["record"]["suggestion"]["ticket"]
        self.assertEqual(ticket[0], "0")
        app.button(key="confirm").click().run()
        app.selectbox(key="series_0").select("Unavailable").run()
        self.assertIn(ticket, app.session_state["record"]["purchased"])
        self.check(app)

    def test_changes_invalidate_and_book_details_clear(self):
        app = self.launch()
        app.text_input(key="first").input("15786").run()
        app.text_input(key="last").input("15799").run()
        app.text_area(key="excluded").input("15788").run()
        app.button(key="suggest").click().run()
        app.selectbox(key="series_3").select("Unknown").run()
        self.assertIsNone(app.session_state["record"]["suggestion"])
        app.text_input(key="first").input("15801").run()
        self.assertEqual(app.text_input(key="last").value, "")
        self.assertEqual(app.text_area(key="excluded").value, "")
        self.check(app)

    def test_bad_edit_does_not_overwrite_and_discard_recovers(self):
        app = self.launch()
        app.text_input(key="first").input("15800").run()
        app.button(key="suggest").click().run()
        app.text_area(key="purchase_text").input("342 nope").run()
        self.assertIsNone(app.session_state["record"]["suggestion"])
        app.button(key="save_purchases").click().run()
        self.assertEqual(app.session_state["record"]["purchased"], ["20397"])
        self.assertTrue(app.error)
        self.assertTrue(app.button(key="suggest").disabled)
        app.button(key="discard_edit").click().run()
        self.assertFalse(app.button(key="suggest").disabled)
        self.check(app)

    def test_repeated_endings_warning_and_ten_ticket_limit(self):
        app = self.launch()
        app.text_area(key="purchase_text").input("20397 10397").run()
        app.button(key="save_purchases").click().run()
        self.assertTrue(any("impossible" in w.value for w in app.warning))
        app.text_area(key="purchase_text").input(" ".join(f"1000{d}" for d in range(10))).run()
        app.button(key="save_purchases").click().run()
        app.text_input(key="first").input("15786").run()
        self.assertTrue(app.button(key="suggest").disabled)
        self.check(app)

    def test_ceiling_cannot_erase_existing_purchase(self):
        app = self.launch()
        app.number_input(key="maximum").set_value(10000).run()
        self.assertEqual(app.session_state["record"]["settings"]["max_ticket"], 39999)
        self.assertEqual(app.session_state["record"]["purchased"], ["20397"])
        self.assertTrue(app.error)
        self.check(app)

if __name__ == "__main__":
    unittest.main()
