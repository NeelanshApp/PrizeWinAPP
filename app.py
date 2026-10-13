"""Run: python -m streamlit run app.py"""

from datetime import datetime, timezone

import streamlit as st

from session_model import (
    candidates, confirm, export_backup, fresh_state, import_backup, invalidate,
    replace_purchases, suggest, undo_purchase,
)
from ticket_logic import (
    LIMIT, SERIES, STATUSES, ValidationError, balance, book_range, coverage,
    parse_tickets,
)


st.set_page_config(page_title="PrizeWin · Ticket Coverage", page_icon="🎟️", layout="centered")

if "record" not in st.session_state:
    st.session_state.record = fresh_state()


def sync_widgets():
    record = st.session_state.record
    st.session_state.purchase_text = ", ".join(record["purchased"])
    st.session_state.maximum = record["settings"]["max_ticket"]
    for series in SERIES:
        st.session_state[f"series_{series}"] = record["availability"][series]


if "purchase_text" not in st.session_state:
    sync_widgets()


def notice(message, error=False):
    st.session_state.notice = (message, error)


def save_purchases():
    try:
        replace_purchases(st.session_state.record, st.session_state.purchase_text)
        sync_widgets()
        notice("Purchased list saved. Download a fresh backup.")
    except ValidationError as exc:
        notice(str(exc), True)


def discard_edit():
    sync_widgets()
    notice("Unsaved edit discarded.")


def restore():
    upload = st.session_state.get("backup_upload")
    try:
        if upload is None:
            raise ValidationError("Choose a JSON backup first.")
        restored = import_backup(upload.getvalue())
        st.session_state.record = restored
        sync_widgets()
        st.session_state.first = ""
        st.session_state.last = ""
        st.session_state.excluded = ""
        st.session_state.book_scope = None
        notice("Backup restored. Enter the current book again.")
    except ValidationError as exc:
        notice(str(exc), True)


def change_maximum():
    record = st.session_state.record
    maximum = int(st.session_state.maximum)
    try:
        parse_tickets(",".join(record["purchased"]), maximum, LIMIT)
        record["settings"]["max_ticket"] = maximum
        record["suggestion"] = None
        st.session_state.last = ""
        st.session_state.excluded = ""
        st.session_state.book_scope = None
    except ValidationError:
        st.session_state.maximum = record["settings"]["max_ticket"]
        notice("That ceiling would exclude a purchased ticket. Correct the purchased list first; records were kept.", True)


def confirm_click():
    try:
        if st.session_state.purchase_text != ", ".join(st.session_state.record["purchased"]):
            raise ValidationError("Save or discard the purchased-list edit first.")
        if int(st.session_state.maximum) != st.session_state.record["settings"]["max_ticket"]:
            st.session_state.record["suggestion"] = None
            raise ValidationError("The ticket ceiling changed. Suggest a number again after applying it.")
        # A click and an availability edit can arrive in the same browser event.
        # Revalidate using the widget values already received for this rerun.
        st.session_state.record["availability"] = {
            s: st.session_state[f"series_{s}"] for s in SERIES
        }
        ticket = confirm(st.session_state.record, st.session_state.first,
                         st.session_state.get("last", ""), st.session_state.get("excluded", ""))
        sync_widgets()
        notice(f"{ticket} recorded as purchased. Download a fresh backup below.")
    except ValidationError as exc:
        notice(str(exc), True)


def undo_click():
    try:
        ticket = undo_purchase(st.session_state.record)
        sync_widgets()
        notice(f"Removed {ticket} from the record. This only corrects the app record; it does not return a physical ticket.")
    except ValidationError as exc:
        notice(str(exc), True)


def enable_zero():
    st.session_state.series_0 = "Available"
    st.session_state.record["availability"]["0"] = "Available"
    st.session_state.record["suggestion"] = None


record = st.session_state.record
maximum = record["settings"]["max_ticket"]
st.title("🎟️ Ticket Coverage Planner")
st.caption("PrizeWin · 10 tickets total · INR 501 each · full budget INR 5,010")
if message := st.session_state.pop("notice", None):
    (st.error if message[1] else st.success)(message[0])

info = coverage(record["purchased"])
left, right = st.columns(2)
left.metric("Purchased", f"{len(record['purchased'])} / {LIMIT}")
right.metric("Tickets remaining", LIMIT - len(record["purchased"]))
st.markdown(" ".join(f":{'gray' if d in info['missing'] else 'green'}-badge[{d}]" for d in "0123456789"))
st.caption("Green = covered · Missing endings: " + (", ".join(info["missing"]) or "none"))
if info["repeated"]:
    st.warning("Repeated purchased endings: " + ", ".join(info["repeated"]) +
               ". Complete ten-ending coverage is impossible within ten total tickets with these purchases. All distinct purchased tickets are kept; correct the record only if it is wrong.")

with st.expander("Purchased tickets · edit, copy, or undo"):
    st.text_area("Purchased ticket list", key="purchase_text", max_chars=10000,
                 help="Separate numbers with commas, spaces, or newlines. An empty list removes all recorded purchases.")
    st.button("Save purchased list", key="save_purchases", on_click=save_purchases, width="stretch")
    st.button("Discard unsaved edit", key="discard_edit", on_click=discard_edit)
    st.button("Undo last confirmed purchase", key="undo", on_click=undo_click,
              disabled=record["undo"] is None)
    st.code(", ".join(record["purchased"]) or "(no purchased tickets)", language=None, wrap_lines=True)
    if record["purchased"]:
        st.table([{"Ticket": t, "Last 1": t[-1:], "Last 2": t[-2:],
                   "Last 3": t[-3:], "Last 4": t[-4:]} for t in record["purchased"]])
    st.caption("Distinct suffixes: " + " · ".join(f"last {n}: {count}" for n, count in info["suffix_counts"].items()))

dirty = st.session_state.purchase_text != ", ".join(record["purchased"])
if dirty:
    record["suggestion"] = None
    st.warning("The purchased list has an unsaved edit. Save or discard it before suggesting or confirming.")

st.subheader("At the counter")
first = st.text_input("First currently available number", key="first", max_chars=5, placeholder="e.g. 15786")
with st.expander("Series availability · 0 starts Unknown"):
    st.caption("These settings describe purchasing availability here, not eligibility in the draw. Unknown does not mean sold out.")
    for series in SERIES:
        record["availability"][series] = st.selectbox(f"Series {series}", STATUSES, key=f"series_{series}")

book = None
input_error = None
if first.strip():
    try:
        book = book_range(first, maximum)
    except ValidationError as exc:
        input_error = str(exc)

scope = (book.start, maximum) if book else None
if scope != st.session_state.get("book_scope"):
    had_details = bool(st.session_state.get("last") or st.session_state.get("excluded"))
    st.session_state.last = ""
    st.session_state.excluded = ""
    st.session_state.book_scope = scope
    if had_details:
        st.info("Book changed: previous exclusions and shortened end were cleared.")

if book and f"{book.first:05d}"[0] == "0" and record["availability"]["0"] == "Unknown":
    st.info("Series 0 availability is Unknown. Enable it if you can buy from it here.")
    st.button("Series 0 is available here", key="enable_zero", on_click=enable_zero, width="stretch")

with st.expander("Book details · sold numbers and shortened end"):
    st.text_input("Actual last available number (optional)", key="last", max_chars=5)
    st.text_area("Sold / unavailable numbers in this search range", key="excluded", max_chars=10000,
                 help="Comma, space, or newline separated. Retained within the same book; cleared when you switch books.")
    st.caption("If you move the first number within this book, review these details. Entries outside the new search range must be removed.")

last, excluded = st.session_state.last, st.session_state.excluded
invalidate(record, first, last, excluded)
result = None
if first.strip() and not input_error:
    try:
        effective = book_range(first, maximum, last)
        st.caption(f"Original book {effective.start:05d}–{effective.nominal_end:05d} · search {effective.first:05d}–{effective.end:05d}")
        st.caption("Assumed available: every number in this search range except your exclusions, subject to enabled series. Live sales are not known.")
        result = candidates(record, first, last, excluded)
    except ValidationError as exc:
        input_error = str(exc)
if input_error:
    record["suggestion"] = None
    st.error(input_error)

bal = balance(record["purchased"], record["availability"], maximum)
st.caption("First-digit counts: " + " · ".join(f"{s}: {n}" for s, n in info["series_counts"].items()))
if bal["ideal"]:
    st.caption("Preferred final balance across enabled series: any order of " + ", ".join(map(str, bal["ideal"])) + ". This is a preference only.")
    if not bal["attainable"]:
        st.info("This ideal balance is unattainable with the recorded purchases and current enabled series / ceiling. Missing endings still take priority.")
    st.caption("Preferred series for the next book: " + ", ".join(bal["preferred"]) + " (least represented among enabled series). Check availability at the counter.")
else:
    st.info("Enable at least one series as Available.")

full = len(record["purchased"]) >= LIMIT
if full:
    st.info("Ten tickets recorded. No further purchases can be recommended. Your coverage is shown above.")
elif result and result.reason:
    st.info(result.reason)

can_suggest = bool(result and result.best and not dirty and not full)
if st.button("Suggest number", key="suggest", type="primary", width="stretch", disabled=not can_suggest):
    result = suggest(record, first, last, excluded)

if record["suggestion"]:
    ticket = record["suggestion"]["ticket"]
    with st.container(border=True):
        st.caption("SUGGESTED TICKET · CHECK IT IS STILL AVAILABLE")
        st.markdown(f'<div style="font-size:clamp(3rem,15vw,5rem);font-weight:750;letter-spacing:.1em;color:#0f766e">{ticket}</div>', unsafe_allow_html=True)
        st.write(f"Adds missing ending **{ticket[-1]}**. Chosen at random among {len(result.best)} equally ranked candidate(s).")
        if ticket[0] not in bal["preferred"]:
            st.info("This improves ending coverage but may weaken the preferred first-digit balance. You can also check a book in series " + ", ".join(bal["preferred"]) + ".")
        if len(result.best) == 1:
            st.caption("Only one best-ranked candidate is available; Suggest another will keep this option.")
        if st.button("Suggest another", key="another", width="stretch"):
            suggest(record, first, last, excluded, another=True)
            st.rerun()
        st.button("Confirm purchased", key="confirm", on_click=confirm_click, type="primary", width="stretch")

st.divider()
st.subheader("Keep your records")
st.caption("Refresh, disconnection, or a hosted restart may lose this session. Download a backup after purchases; restore it on another device or in a new session.")
st.download_button("Download backup JSON", export_backup(record),
                   file_name=f"prizewin-backup-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json",
                   mime="application/json", on_click="ignore", width="stretch", key="download_backup")
with st.expander("Restore a backup"):
    st.file_uploader("Backup JSON (up to 64 KiB)", type=["json"], key="backup_upload", max_upload_size=1)
    st.caption("Restore replaces this session's records and settings only after the whole file passes validation.")
    st.button("Restore backup", key="restore", on_click=restore, width="stretch")

with st.expander("Settings and what coverage means"):
    st.number_input("Provisional maximum ticket", min_value=1, max_value=39999,
                    step=1, key="maximum", on_change=change_maximum)
    st.caption("The ceiling is a range limit, not confirmation that all these tickets exist or are sold. 00000 is always excluded.")
    st.write("This is a number-selection assistant, not a prediction or ticket-purchasing service. Ten different endings also give ten different suffixes of lengths 2, 3, and 4.")
    st.write("Covering endings 0–9 guarantees a numerical last-digit match to any accepted winning number. It does not guarantee prize eligibility, payment, recovery of spend, or profit. Gift rules, exclusions, overlap, and values are unverified.")
    st.write("Under fair independent bowls and a complete five-digit redraw for unsold results, each sold number is equally likely. Owning k distinct sold tickets out of N gives first-prize chance k/N. N is unknown; it cannot be inferred from the printed ceiling or available series.")
    st.write("First-digit balance and random tie-breaking offer no jackpot advantage. Uneven sold-number distributions can affect suffix events; this is a coverage heuristic, not a proven way to maximise returns. Repeated internal digits and attractive numbers have no special merit.")
