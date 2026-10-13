# PrizeWinAPP — Ticket Coverage Planner

A small, phone-friendly Streamlit app implementing [context.md](context.md). Record up to **10 tickets total**, cover missing final digits, and use first-digit balance as a soft preference. A suggestion is recorded only when you press **Confirm purchased**.

The existing `CopyPasteApp` was used as an architectural reference; its files are unchanged. This app has its own logic and private per-session records. See [PROJECT_NOTES.md](PROJECT_NOTES.md) for the folder comparison and acceptance-case mapping, and [PROGRESS.md](PROGRESS.md) for the latest session checkpoint.

## 1. Install/check Python and Git on Windows

Open **PowerShell** from the Start menu:

```powershell
py --list
git --version
```

If Python is missing, install **Python 3.12** from [Python for Windows](https://www.python.org/downloads/windows/), including the Python launcher and PATH option, then reopen PowerShell. Python 3.11 is also compatible with the selected Streamlit package; the supplied setup script can use your existing Python 3.11 installation. The logic was tested here using Python 3.12.3.

If Git is missing, install [Git for Windows](https://git-scm.com/downloads/win) and reopen PowerShell. Git is required for the GitHub steps, not for running the app locally.

## 2. Set up and run locally

**Easy option:** open `C:\Users\sonal\Projects\PrizeWinAPP`, double-click `setup_windows.bat`, and wait for installation and checks. After it reports success, double-click `start_windows.bat`. On later days, use `start_windows.bat` directly. `test-and-start.cmd` repeats all checks before launching.

**Manual option:** run these PowerShell commands one line at a time. Continue only if the preceding command succeeds.

```powershell
Set-Location "C:\Users\sonal\Projects\PrizeWinAPP"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe verify.py
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost
```

If using the existing Python 3.11 installation, replace only the environment creation command with `py -3.11 -m venv .venv`. If `py` is unavailable, use `python -m venv .venv` after checking `python --version`, or use your installed interpreter's full path:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m venv .venv
```

Open **http://localhost:8501** if your browser does not open automatically. Keep the terminal open. Press **Ctrl+C** to stop the app.

These commands call the virtual environment's Python directly and do not require activation. If you prefer activation:

```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

If PowerShell blocks `Activate.ps1`, use the direct `.venv\Scripts\python.exe` commands above; no execution-policy change is necessary.

Linux/macOS equivalent (requires Python with venv/pip installed):

```bash
cd PrizeWinAPP
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python verify.py
.venv/bin/python -m streamlit run app.py
```

## 3. Use it at the ticket counter

1. Check **Purchased**. A fresh session starts with `20397` once. Open **Purchased tickets** to correct/remove it or enter your real purchases. Press **Save purchased list**. An empty saved list removes all entries, including the seed.
2. Enter the first **currently available** number, such as `15786`. The first number is included; this example searches through `15800`.
3. Check **Series availability**. Series 1, 2, and 3 start Available as a working assumption. Series 0 starts Unknown. For a zero-series book, press **Series 0 is available here** after checking at the counter, or change its availability control.
4. Optionally enter sold/unavailable numbers and a shortened last-available number under **Book details**. The app assumes the rest of that range is available; it cannot see live sales.
5. Press **Suggest number**. Numbers with already-covered endings are excluded. Among useful candidates, the least-represented series is preferred, then a random tie-break is used. An overrepresented series remains usable for a missing ending.
6. **Suggest another** chooses a different equally ranked option if possible. With one best option, it stays the same. Unrelated reruns keep the current suggestion; relevant edits clear it.
7. Check the physical ticket is still available. Press **Confirm purchased** only after buying it. Confirmation updates the count exactly once and clears the suggestion.
8. **Download backup JSON** after recording purchases. The ten-ticket limit includes existing purchases.

Book exclusions and the shortened end are cleared when switching to a different original 50-ticket book. Moving the first number within the same book keeps them, with an explicit reminder; remove any exclusions now outside the search range.

**Undo last confirmed purchase** corrects the latest app entry only. Older corrections can be made in the purchased-list editor. Neither action returns a physical ticket. Editing/restoring the purchased list clears undo history.

Distinct existing tickets with repeated endings are preserved. The app warns that full ten-ending coverage is then impossible within ten total purchases. Invalid edits and duplicate complete ticket entries are rejected without changing saved records. Availability changes never erase purchased tickets.

## 4. Backup and restore

Records live only in your Streamlit browser session. Refreshes, disconnects, sleeping/restarting hosted apps, or opening a different device may start a new session. Session state and hosted disk are **not durable storage**.

- Download the JSON backup prominently shown below the recommendations.
- On the new session/device, open **Restore a backup**, choose that JSON, then press **Restore backup**. This replaces records only after the entire file validates.
- Copy purchased-ticket text from the code box in the purchased-ticket panel when useful.
- Backups contain schema version `1`, purchased numbers as five-character strings, all four availability states, and `settings.max_ticket`.
- The current book, temporary exclusions, displayed suggestion, and undo history are intentionally not restored. Re-enter current counter availability.
- Invalid JSON, unknown schema versions, invalid tickets/settings, duplicates, and lists over ten purchases are rejected atomically. Maximum backup size: 64 KiB.
- Save personal backup files in `backups/` or retain the generated `prizewin-backup-...json` filename so `.gitignore` excludes them. Do not put renamed personal backups outside that ignored folder.

## 5. Put the project on GitHub

You need a GitHub account and Git installed. These steps publish the app source; do not include personal backup JSON, `.venv`, or credentials.

1. Sign in at [GitHub](https://github.com/) and create a repository named **PrizeWinAPP**. A public repository is the simplest option for a public app. Leave the new repository empty: do **not** add a README, `.gitignore`, or license there, because the local project already contains files.
2. In PowerShell, run:

   ```powershell
   Set-Location "C:\Users\sonal\Projects\PrizeWinAPP"
   git init -b main
   git add .
   git status
   ```

3. Review the staged filenames. They should be project code/docs/tests/config only. Then:

   ```powershell
   git commit -m "Build ticket coverage planner"
   git remote add origin https://github.com/YOUR_USERNAME/PrizeWinAPP.git
   git push -u origin main
   ```

   Replace `YOUR_USERNAME` with your actual GitHub username. Complete Git's GitHub sign-in prompt. Do not put an access token in a URL or project file.

4. If Git asks for your identity before committing, set it for this repository, then retry the commit:

   ```powershell
   git config user.name "Your Name"
   git config user.email "YOUR_GITHUB_EMAIL_OR_NOREPLY_ADDRESS"
   ```

5. Refresh the repository page and verify `app.py`, `ticket_logic.py`, `session_model.py`, and `requirements.txt` appear at the repository root, with `.streamlit/config.toml` inside its folder.

If `origin` already exists, check `git remote -v` and use `git remote set-url origin ...` only if the URL needs correcting. Do not force-push over an existing repository with different work.

These steps follow [GitHub's official local-project guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## 6. Deploy on Streamlit Community Cloud

1. Visit [Streamlit Community Cloud](https://share.streamlit.io/), sign in, and connect the GitHub account containing your repository.
2. Click **Create app**, then **Yup, I have an app** if prompted.
3. Select repository **YOUR_USERNAME/PrizeWinAPP**, branch **main**, and main file **app.py**. You can also paste the GitHub URL for `app.py`.
4. Open **Advanced settings** and choose **Python 3.12**. No secrets are required. Save those settings.
5. Optionally choose an app subdomain. Click **Deploy** and watch the build logs.
6. When the app opens at its `streamlit.app` address, enter `15786`, verify ending `7` is excluded with the seeded `20397`, and test backup download/restore. Share/open that URL on your phone.

Streamlit currently documents Python 3.12 as its default and provides Python selection in Advanced settings. The app uses the verified released package `streamlit==1.65.0`. See the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [file organization guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization), and [Streamlit package release](https://pypi.org/project/streamlit/1.65.0/). Guidance checked on 2026-10-13; future labels and supported versions may change.

For later updates, run the tests, then commit and push changes to `main`. Community Cloud picks up changes from the connected repository. Keep `requirements.txt` and `.streamlit/config.toml` in the locations shown here.

**Publication status:** this project has not been uploaded to GitHub or deployed. No remote account or hosting configuration was changed.

## Tests and actual verification

Run everything after installing requirements:

```powershell
.\.venv\Scripts\python.exe verify.py
```

- **19 selection/validation tests passed** using Python 3.12.3, including exact requested candidate sets, inclusive book ends, all three series boundaries, capped ranges, soft balance, and injected random choices. One test checks every original book across all 16 availability masks.
- **9 session/backup tests passed**, covering independent sessions, stable suggestions, input invalidation, stale/double confirmation, undo, the purchase limit, atomic bad edits/imports, leading-zero backup round trips, and the UTF-8 byte limit.
- All Python source files passed compilation.
- **All 35 tests and the real-server HTTP smoke check passed on Windows**, using Python 3.11.9 on 2026-10-13. The agent inspected `verification.log`, including all seven Streamlit interaction tests and the final `RESULT: PASS`. The user confirmed the app runs locally and meets their requirements. Mobile visual checks and hosted deployment remain pending.
- `setup_windows.bat` installs Streamlit, runs all **35 tests**, and runs the real HTTP startup smoke check on your Windows machine. The smoke check verifies the health endpoint and served HTML, then stops its temporary server. AppTest exercises the UI code separately; HTTP health alone does not verify widget interactions. Both Windows check scripts use `verify.py`, which saves detailed results to `verification.log` (ignored by Git). The log is replaced each run. Only a final `RESULT: PASS` means every check completed; an interrupted or failed log is not a pass.

Logic-only tests require no third-party packages:

```powershell
python -m unittest discover -s tests -p "test_ticket_logic.py" -v
python -m unittest discover -s tests -p "test_session_model.py" -v
```

## Troubleshooting

- **No module named streamlit:** install requirements using the same `.venv\Scripts\python.exe` used to run the app.
- **Installation cannot reach PyPI:** check your connection/proxy and rerun setup. Do not disable TLS verification.
- **Port 8501 is busy:** stop the older app with Ctrl+C, or append `--server.port 8502` and open `http://localhost:8502`.
- **No recommendation:** check missing endings, series settings, exclusions, and the ten-ticket total. The explanation identifies the cause; a different book may be needed.
- **Leading zeros disappear:** enter tickets in the app or use its JSON backups, which store strings. Avoid spreadsheet exports that convert ticket strings into numbers.
- **Cloud build fails:** inspect the Community Cloud logs. Confirm the repository, branch, `app.py` path, Python version, and requirements file.
- **Records reset after refreshing:** restore your most recent JSON backup. Each new session starts with the specified seed until restored or edited.

## Mathematical limits

This is a coverage assistant, not a prediction or purchasing service. Under the stated fair, independent bowls and complete redraw of unsold results, each sold ticket is equally likely; `k` distinct owned tickets out of `N` sold tickets have first-prize chance `k/N`. The app does not know `N` and never treats `39999` as the sold-ticket count.

Different final digits also give different last-two, last-three, and last-four strings. Covering all ten endings guarantees a numerical last-digit match to an accepted winner, but does not guarantee prize eligibility, payment, spend recovery, or profit. Advertised gift rules, overlap/exclusions, and values are unverified. Uneven sold-ticket distribution matters for suffix events; balance and random choice give no jackpot advantage. No odds calculator or return optimiser is included.
