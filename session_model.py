"""Atomic session transitions and versioned JSON backups; no shared mutable records."""

import json

from ticket_logic import (
    LIMIT, MAX_TICKET, ValidationError, choose, normalize_ticket, parse_tickets,
    selection, validate_availability, validate_maximum,
)

BACKUP_LIMIT = 65536


def fresh_state():
    return {"version": 1, "purchased": ["20397"],
            "availability": {"0": "Unknown", "1": "Available", "2": "Available", "3": "Available"},
            "settings": {"max_ticket": MAX_TICKET}, "suggestion": None, "undo": None}


def validate_record(data):
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValidationError("Unsupported backup: expected schema version 1.")
    settings = data.get("settings")
    if not isinstance(settings, dict):
        raise ValidationError("Backup is missing settings.")
    maximum = validate_maximum(settings.get("max_ticket"))
    entries = data.get("purchased")
    if not isinstance(entries, list) or len(entries) > LIMIT or any(not isinstance(t, str) for t in entries):
        raise ValidationError("Backup purchased tickets must be a list of at most 10 digit strings.")
    # Validate each list entry separately: embedded separators must not become extra tickets.
    tickets = [normalize_ticket(t, maximum) for t in entries]
    purchased = parse_tickets(",".join(tickets), maximum, LIMIT)
    availability = validate_availability(data.get("availability"))
    return {"version": 1, "purchased": list(purchased), "availability": availability,
            "settings": {"max_ticket": maximum}, "suggestion": None, "undo": None}


def export_backup(state):
    clean = validate_record(state)
    return json.dumps({key: clean[key] for key in ("version", "purchased", "availability", "settings")}, indent=2)


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("Backup contains duplicate JSON keys.")
        result[key] = value
    return result


def import_backup(payload):
    if not isinstance(payload, (bytes, str)):
        raise ValidationError("Backup must be a JSON file no larger than 64 KiB.")
    if isinstance(payload, str):
        try:
            payload = payload.encode("utf-8")
        except UnicodeError as exc:
            raise ValidationError("Backup is not valid UTF-8. Existing records were kept.") from exc
    if len(payload) > BACKUP_LIMIT:
        raise ValidationError("Backup must be a JSON file no larger than 64 KiB.")
    try:
        data = json.loads(payload, object_pairs_hook=_unique_keys)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError("Backup is not valid JSON. Existing records were kept.") from exc
    return validate_record(data)


def replace_purchases(state, text):
    parsed = parse_tickets(text, state["settings"]["max_ticket"], LIMIT)
    state.update(purchased=list(parsed), suggestion=None, undo=None)


def fingerprint(state, first, last="", excluded=""):
    return (tuple(state["purchased"]), tuple(sorted(state["availability"].items())),
            state["settings"]["max_ticket"], first, last, excluded)


def invalidate(state, first, last="", excluded=""):
    suggestion = state["suggestion"]
    if suggestion and suggestion["fingerprint"] != fingerprint(state, first, last, excluded):
        state["suggestion"] = None


def candidates(state, first, last="", excluded=""):
    return selection(state["purchased"], state["availability"], first,
                     maximum=state["settings"]["max_ticket"], last=last, excluded=excluded)


def suggest(state, first, last="", excluded="", *, another=False, rng=None):
    invalidate(state, first, last, excluded)
    result = candidates(state, first, last, excluded)
    previous = state["suggestion"]["ticket"] if another and state["suggestion"] else None
    ticket = choose(result, previous, rng)
    state["suggestion"] = ({"ticket": ticket, "fingerprint": fingerprint(state, first, last, excluded)}
                           if ticket else None)
    return result


def confirm(state, first, last="", excluded=""):
    invalidate(state, first, last, excluded)
    suggestion = state["suggestion"]
    if suggestion is None:
        raise ValidationError("No current suggestion to confirm. Suggest a number first.")
    result = candidates(state, first, last, excluded)
    ticket = suggestion["ticket"]
    if ticket not in result.eligible:
        state["suggestion"] = None
        raise ValidationError("This suggestion is no longer eligible. Suggest again.")
    state["purchased"] = [*state["purchased"], ticket]
    state["undo"] = ticket
    state["suggestion"] = None
    return ticket


def undo_purchase(state):
    ticket = state["undo"]
    if ticket is None or ticket not in state["purchased"]:
        raise ValidationError("There is no confirmed purchase to undo.")
    state["purchased"] = [t for t in state["purchased"] if t != ticket]
    state.update(undo=None, suggestion=None)
    return ticket
