# Structure analysis and implementation map

## Reference project: CopyPasteApp

Inspected `app.py`, `storage.py`, tests, dependency/config files, Windows scripts, and the file tree. The reference uses:

- `app.py` for Streamlit widgets and user actions.
- `storage.py` for shared file/text storage, validation, locking, and expiry.
- `tests/` for storage and Streamlit interaction checks.
- `.streamlit/config.toml` for the theme/server settings.
- Pinned runtime/development requirements, README/context/planning docs, and Windows setup/start scripts.
- Local `.venv`, caches, `.git`, and a `data` folder as development/runtime artifacts.

PrizeWinAPP follows the small-module structure, theme, and Windows workflow. Shared disk storage, file locks, file-sharing features, automatic refresh, and the reference app's data are unnecessary for this specification and were not copied. The existing `context.md` remains the authoritative, unchanged specification. No CopyPasteApp files were modified.

## New project

```text
PrizeWinAPP/
├── app.py                    # Mobile-friendly Streamlit interface and session callbacks
├── ticket_logic.py           # Pure parsing, book ranges, coverage, ranking and random choice
├── session_model.py          # Atomic edits, suggestions, confirmations, undo, JSON backups
├── requirements.txt          # One direct dependency: Streamlit
├── context.md                # Original complete specification, preserved
├── README.md                 # Setup, usage, backup, deployment and validation status
├── PROJECT_NOTES.md          # This structure analysis / acceptance mapping
├── PROGRESS.md               # Latest checkpoint and exact remaining steps
├── verify.py                 # Runs checks, saves ignored verification.log
├── smoke_check.py            # Starts real server, checks HTTP, stops server
├── setup_windows.bat         # Create venv, install, run tests and smoke check
├── start_windows.bat         # Start local app
├── test-and-start.cmd        # Check then launch
├── .gitignore               # Ignore environments, secrets, caches, backups
├── .streamlit/
│   └── config.toml           # Theme, upload limit, usage statistics disabled
└── tests/
    ├── test_ticket_logic.py  # 19 logic tests
    ├── test_session_model.py # 9 state/backup tests
    └── test_app.py           # 7 Streamlit interaction tests
```

The live record belongs to `st.session_state` for one user. Pure functions never cache or share personal data. Runtime JSON backups contain only versioned records/settings; book details are re-entered after restoring. No database, authentication, payment, prediction API, or external service is needed to run the app.

## Acceptance cases from context.md

| Case | Implementation / checks |
| --- | --- |
| 1. Exact 15786–15800 candidate set | `test_required_candidate_set` |
| 2. 15800 is included | `test_last_page_is_inclusive` |
| 3–4. Zero series enabled vs Unknown | `test_zero_series_unknown_and_enabled`; inline availability button in app |
| 5. Nine endings, unhelpful last page | `test_nine_endings_and_unhelpful_single_page` |
| 6. No eleventh suggestion/confirmation | `test_ten_purchases_stop`, `test_cannot_confirm_eleventh_ticket` |
| 7. Candidate-specific series across boundaries | `test_each_cross_series_boundary`, all three transitions |
| 8. Provisional ceiling | `test_provisional_ceiling` |
| 9. Disabled series purchases retained | `test_existing_disabled_series_still_counts` |
| 10. Existing repeated endings retained/warned | `test_repeated_endings_preserved`; app warning |
| 11. Balance cannot block missing endings | `test_overrepresented_series_does_not_block_coverage` |
| 12. Stability, invalidation, confirmation once | Session tests plus AppTest interaction tests |
| 13. Atomic validated backup round trip | Session tests, malformed JSON/schema/list cases |
| 14. Single-option Suggest another | `test_random_tie_pool_and_alternatives`; AppTest single-page flow |

All 35 tests (19 logic, 9 session/backup, and 7 Streamlit interaction tests) and the real-server HTTP smoke check passed on Windows Python 3.11.9 on 2026-10-13, confirmed from `verification.log`. The user confirmed the app works locally as required. See PROGRESS.md for the latest checkpoint. Mobile visual checks and hosted deployment remain pending.
