"""Pure ticket rules. Availability is supplied by the user, never inferred."""

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
import random
import re

LIMIT = 10
MAX_TICKET = 39999
SERIES = ("0", "1", "2", "3")
STATUSES = ("Available", "Unavailable", "Unknown")


class ValidationError(ValueError):
    """An input error suitable for display."""


def validate_maximum(value):
    if type(value) is not int or not 1 <= value <= MAX_TICKET:
        raise ValidationError("Maximum ticket must be an integer from 1 to 39999.")
    return value


def normalize_ticket(value, maximum=MAX_TICKET):
    validate_maximum(maximum)
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,5}", value.strip()):
        raise ValidationError(f"Invalid ticket {value!r}: use 1–5 ASCII digits only.")
    number = int(value.strip())
    if not 1 <= number <= maximum:
        raise ValidationError(f"Ticket {value!r} must be between 00001 and {maximum:05d}.")
    return f"{number:05d}"


def parse_tickets(text, maximum=MAX_TICKET, limit=None):
    if not isinstance(text, str) or len(text) > 10000:
        raise ValidationError("Ticket list must be text of at most 10,000 characters.")
    tickets = [normalize_ticket(t, maximum) for t in re.split(r"[,\s]+", text.strip()) if t]
    duplicates = sorted(t for t, count in Counter(tickets).items() if count > 1)
    if duplicates:
        raise ValidationError("Duplicate complete tickets: " + ", ".join(duplicates) + ". Remove the repeated entries.")
    if limit is not None and len(tickets) > limit:
        raise ValidationError(f"At most {limit} distinct purchased tickets are allowed. Existing records were kept.")
    return tuple(tickets)


def validate_availability(availability):
    if (not isinstance(availability, dict) or set(availability) != set(SERIES)
            or any(status not in STATUSES for status in availability.values())):
        raise ValidationError("Each series 0–3 needs Available, Unavailable, or Unknown status.")
    return dict(availability)


@dataclass(frozen=True)
class Book:
    start: int
    nominal_end: int
    first: int
    end: int

    @property
    def tickets(self):
        return tuple(f"{n:05d}" for n in range(self.first, self.end + 1))


def book_range(first, maximum=MAX_TICKET, last=""):
    n = int(normalize_ticket(first, maximum))
    start = ((n - 1) // 50) * 50 + 1
    nominal_end = start + 49
    end = min(nominal_end, maximum)
    if last.strip():
        actual = int(normalize_ticket(last, maximum))
        if not n <= actual <= end:
            raise ValidationError(f"Last available number must be between {n:05d} and {end:05d}.")
        end = actual
    return Book(start, nominal_end, n, end)


def coverage(purchased):
    endings = Counter(t[-1] for t in purchased)
    return {
        "missing": tuple(d for d in "0123456789" if d not in endings),
        "repeated": tuple(d for d, count in sorted(endings.items()) if count > 1),
        "series_counts": {s: sum(t[0] == s for t in purchased) for s in SERIES},
        "suffix_counts": {n: len({t[-n:] for t in purchased}) for n in range(1, 5)},
    }


def balance(purchased, availability, maximum=MAX_TICKET):
    enabled = tuple(s for s in SERIES if availability[s] == "Available")
    counts = coverage(purchased)["series_counts"]
    if not enabled:
        return {"preferred": (), "ideal": (), "attainable": False}
    lowest = min(counts[s] for s in enabled)
    preferred = tuple(s for s in enabled if counts[s] == lowest)
    base, extra = divmod(LIMIT, len(enabled))
    ideal = tuple(sorted([base + 1] * extra + [base] * (len(enabled) - extra), reverse=True))
    attainable = False
    # Check every permutation of floor/ceiling targets, including series bounds.
    for raised in combinations(enabled, extra):
        targets = {s: base + (s in raised) if s in enabled else 0 for s in SERIES}
        capacities = {s: max(0, min(maximum, int(s) * 10000 + 9999)
                                 - max(1, int(s) * 10000) + 1) for s in SERIES}
        if all(counts[s] <= targets[s] <= capacities[s] for s in SERIES):
            attainable = True
            break
    return {"preferred": preferred, "ideal": ideal, "attainable": attainable}


@dataclass(frozen=True)
class Selection:
    eligible: tuple[str, ...]
    best: tuple[str, ...]
    reason: str


def selection(purchased, availability, first, *, maximum=MAX_TICKET, last="", excluded=""):
    purchased = parse_tickets(",".join(purchased), maximum, LIMIT)
    availability = validate_availability(availability)
    if len(purchased) >= LIMIT:
        return Selection((), (), "Ten tickets are already recorded. No further purchase can be suggested.")
    book = book_range(first, maximum, last)
    unavailable = set(parse_tickets(excluded, maximum))
    if not unavailable.issubset(book.tickets):
        raise ValidationError("Unavailable numbers must be inside the current search range.")
    enabled = {s for s in SERIES if availability[s] == "Available"}
    if not enabled:
        return Selection((), (), "Enable at least one series as Available.")
    missing = set(coverage(purchased)["missing"])
    covering = tuple(t for t in book.tickets if t[-1] in missing and t not in purchased)
    if not covering:
        return Selection((), (), "No missing ending is available in this range. Choose another book.")
    allowed = tuple(t for t in covering if t[0] in enabled)
    if not allowed:
        return Selection((), (), "Series needs enabling: the missing endings here are in Unknown or Unavailable series. Confirm availability here, or choose another book.")
    eligible = tuple(t for t in allowed if t not in unavailable)
    if not eligible:
        return Selection((), (), "Every eligible number in this range is excluded as unavailable. Check exclusions or choose another book.")
    counts = coverage(purchased)["series_counts"]
    lowest = min(counts[t[0]] for t in eligible)
    best = tuple(t for t in eligible if counts[t[0]] == lowest)
    return Selection(eligible, best, "")


def choose(selection_result, previous=None, rng=None):
    """Uniform choice within the best rank; exclude the previous option if possible."""
    options = selection_result.best
    if not options:
        return None
    alternatives = tuple(t for t in options if t != previous)
    return (rng or random.SystemRandom()).choice(alternatives or options)
