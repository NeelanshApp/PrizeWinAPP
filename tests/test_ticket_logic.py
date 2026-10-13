import random
import unittest

from ticket_logic import (
    ValidationError, balance, book_range, choose, coverage, normalize_ticket,
    parse_tickets, selection,
)


class TicketLogicTests(unittest.TestCase):
    def setUp(self):
        self.availability = {"0": "Unknown", "1": "Available", "2": "Available", "3": "Available"}

    def test_ascii_normalization_and_invalid_tokens(self):
        self.assertEqual(normalize_ticket("342"), "00342")
        for invalid in ["-1", "1.2", "1e3", "abc", "１２３", "١٢٣", "000001", "00000", "40000", "", 1, True]:
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                normalize_ticket(invalid)

    def test_lists_duplicates_and_limit(self):
        self.assertEqual(parse_tickets("1, 2\n3\t4"), ("00001", "00002", "00003", "00004"))
        with self.assertRaisesRegex(ValidationError, "Duplicate.*00342"):
            parse_tickets("342 00342")
        with self.assertRaises(ValidationError):
            parse_tickets(" ".join(map(str, range(1, 12))), limit=10)

    def test_book_boundaries(self):
        for first, start, end, count in [
            ("15786", 15751, 15800, 15), ("15800", 15751, 15800, 1),
            ("15801", 15801, 15850, 50), ("00001", 1, 50, 50),
            ("00050", 1, 50, 1), ("00051", 51, 100, 50),
            ("00342", 301, 350, 9), ("39986", 39951, 39999, 14),
        ]:
            with self.subTest(first=first):
                book = book_range(first)
                self.assertEqual((book.start, book.end, len(book.tickets)), (start, end, count))
                self.assertEqual(book.tickets[0], first)

    def test_shortened_end(self):
        self.assertEqual(book_range("15786", last="15790").tickets[-1], "15790")
        self.assertEqual(book_range("15786", maximum=15788).end, 15788)
        for last in ["15785", "15801", "40000", "abc"]:
            with self.subTest(last=last), self.assertRaises(ValidationError):
                book_range("15786", last=last)

    def test_required_candidate_set(self):
        actual = selection(["20397"], self.availability, "15786")
        expected = ("15786", "15788", "15789", "15790", "15791", "15792", "15793",
                    "15794", "15795", "15796", "15798", "15799", "15800")
        self.assertEqual(actual.eligible, expected)
        self.assertEqual(actual.best, expected)

    def test_last_page_is_inclusive(self):
        self.assertEqual(selection(["20397"], self.availability, "15800").eligible, ("15800",))

    def test_zero_series_unknown_and_enabled(self):
        unknown = selection(["20397"], self.availability, "00342")
        self.assertFalse(unknown.eligible)
        self.assertIn("needs enabling", unknown.reason)
        self.assertNotIn("sold out", unknown.reason)
        self.availability["0"] = "Available"
        result = selection(["20397"], self.availability, "00342")
        self.assertEqual(result.eligible, ("00342", "00343", "00344", "00345", "00346", "00348", "00349", "00350"))

    def test_nine_endings_and_unhelpful_single_page(self):
        result = selection([f"1000{n}" for n in range(9)], self.availability, "15800")
        self.assertFalse(result.eligible)
        self.assertIn("No missing ending", result.reason)

    def test_ten_purchases_stop(self):
        result = selection([f"1000{n}" for n in range(10)], self.availability, "15786")
        self.assertFalse(result.eligible)
        self.assertIn("Ten tickets", result.reason)

    def test_each_cross_series_boundary(self):
        for lower, upper, first, crossing in [("0", "1", "09986", "10000"),
                                              ("1", "2", "19986", "20000"),
                                              ("2", "3", "29986", "30000")]:
            availability = {s: "Unavailable" for s in "0123"}
            availability[upper] = "Available"
            self.assertEqual(selection([], availability, first).eligible, (crossing,))

    def test_provisional_ceiling(self):
        result = selection([], self.availability, "39986")
        self.assertEqual(result.eligible[-1], "39999")
        self.assertNotIn("40000", result.eligible)

    def test_existing_disabled_series_still_counts(self):
        self.availability["2"] = "Unavailable"
        purchased = ["20397"]
        self.assertNotIn("15797", selection(purchased, self.availability, "15786").eligible)
        self.assertEqual(coverage(purchased)["series_counts"]["2"], 1)
        self.assertFalse(balance(purchased, self.availability)["attainable"])
        self.assertEqual(purchased, ["20397"])

    def test_repeated_endings_preserved(self):
        purchased = parse_tickets("20397 10397", limit=10)
        self.assertEqual(len(purchased), 2)
        self.assertEqual(coverage(purchased)["repeated"], ("7",))

    def test_overrepresented_series_does_not_block_coverage(self):
        purchased = ["10001", "10002", "10003", "10004", "10005"]
        result = selection(purchased, self.availability, "15800")
        self.assertEqual(result.best, ("15800",))
        self.assertFalse(balance(purchased, self.availability)["attainable"])

    def test_balance_and_rank_at_boundary(self):
        self.availability["0"] = "Available"
        result = selection(["00347"], self.availability, "09986")
        self.assertEqual(result.best, ("10000",))
        self.assertEqual(balance([], self.availability)["ideal"], (3, 3, 2, 2))
        self.availability["0"] = "Unknown"
        self.assertEqual(balance([], self.availability)["ideal"], (4, 3, 3))

    def test_exclusions_and_reason(self):
        result = selection([], self.availability, "15800", excluded="15800")
        self.assertIn("excluded", result.reason)
        with self.assertRaisesRegex(ValidationError, "inside"):
            selection([], self.availability, "15800", excluded="15799")

    def test_no_enabled_series(self):
        availability = dict.fromkeys("0123", "Unknown")
        self.assertIn("Enable at least", selection([], availability, "15786").reason)
        self.assertEqual(balance([], availability)["ideal"], ())

    def test_random_tie_pool_and_alternatives(self):
        result = selection(["20397"], self.availability, "15786")
        class CheckPool:
            def choice(inner, values):
                self.assertEqual(values, result.best)
                return values[-1]
        self.assertEqual(choose(result, rng=CheckPool()), "15800")
        picked = choose(result, rng=random.Random(1))
        self.assertNotEqual(choose(result, previous=picked, rng=random.Random(1)), picked)
        sole = selection([], self.availability, "15800")
        self.assertEqual(choose(sole, previous="15800", rng=random.Random(1)), "15800")

    def test_every_book_obeys_bounds_and_series_for_all_status_masks(self):
        # Exhaustive book endings across the provisional 39,999-number domain.
        for mask in range(16):
            availability = {str(s): "Available" if mask & (1 << s) else "Unknown" for s in range(4)}
            for first in range(1, 40000, 50):
                result = selection(["20397"], availability, str(first))
                for t in result.eligible:
                    self.assertTrue(first <= int(t) <= min(first + 49, 39999))
                    self.assertEqual(availability[t[0]], "Available")
                    self.assertNotEqual(t[-1], "7")


if __name__ == "__main__":
    unittest.main()
