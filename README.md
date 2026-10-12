# A Little Love Letter

This existing Flask website keeps its login, proposal, beauty, date, funny, final, and Aashi editing-show pages. Authentication is checked server-side. Local runs use SQLite at `instance/proposal.sqlite3` for login results, proposal/date responses, date plans, and video settings. Passwords are not stored. The recovered database backup was restored to this path.

## Local Setup In VS Code

Open the project folder, choose **Terminal → New Terminal**, then run in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
$env:DATABASE_PATH = (Join-Path $PWD "instance\proposal.sqlite3")
$env:PROPOSAL_USERNAME = "aashiyana"
$loginPassword = Read-Host "Proposal login password" -AsSecureString
$env:PROPOSAL_PASSWORD = [System.Net.NetworkCredential]::new("", $loginPassword).Password
$videoSetupKey = Read-Host "Private local video setup key" -AsSecureString
$env:VIDEO_SETUP_KEY = [System.Net.NetworkCredential]::new("", $videoSetupKey).Password
python app.py
```

Open <http://127.0.0.1:5000>. The SQLite database is created automatically if it is missing; the restored visitor data is already in `instance/proposal.sqlite3`. The secure prompts do not echo passwords. Keep the same `FLASK_SECRET_KEY` between local restarts if you want the current session to stay signed in. If PowerShell blocks environment activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.

For macOS/Linux, create and activate `.venv`, install `requirements.txt`, then export `FLASK_SECRET_KEY`, `DATABASE_PATH="$PWD/instance/proposal.sqlite3"`, `PROPOSAL_USERNAME`, and `PROPOSAL_PASSWORD` before `python app.py`.

## Vercel Files And Routing

- `app.py` is the root Flask entrypoint and exports the `app` object Vercel detects.
- `vercel.json` configures the Python function. Flask handles the existing page routes; no catch-all rewrite is required.
- `.python-version` selects Python 3.12.
- `public/static/` contains the site's CSS and JavaScript. Vercel serves these assets from its static CDN at the same `/static/...` URLs used locally.
- `requirements.txt` contains only the Flask runtime dependencies.

## Deploy From GitHub

1. Test locally with `python -m unittest discover -s tests` and `python app.py`.
2. Create a GitHub repository and push this project. `.gitignore` excludes `.env`, virtual environments, local Vercel files, `instance/`, and SQLite files. Do not commit the restored database because it contains private visitor activity.
3. In Vercel, select **Add New → Project**, import the GitHub repository, and keep the project root at the repository root. Vercel detects Flask from `app.py` and `requirements.txt`; do not add a persistent server command.
4. In **Project Settings → Environment Variables**, add `FLASK_SECRET_KEY`, `PROPOSAL_USERNAME`, `PROPOSAL_PASSWORD`, and `DATABASE_PATH=/tmp/proposal.sqlite3` for Production (and Preview if desired). Generate a random secret locally with `python -c "import secrets; print(secrets.token_hex(32))"`, then enter its output directly in Vercel. Never commit those values or `.env` files.
5. Optionally add `FINAL_VIDEO_URL` with a public HTTPS YouTube, Vimeo, or direct MP4/M4V/MOV/WebM URL. Vercel does not use local uploads; its filesystem is temporary. The page works without this setting and will simply omit the video section.
6. Click **Deploy**, open the generated `*.vercel.app` URL on a phone, and test login and the complete proposal flow.
7. To update the site, commit and push changes to the connected GitHub branch. Vercel automatically creates a deployment; promote it to Production as needed.

On Vercel, HTTPS is detected and session cookies are marked `Secure`, `HttpOnly`, and `SameSite=Lax`. `COOKIE_SECURE=1` can explicitly enable secure cookies in another HTTPS host. The production login has no hard-coded credential fallback: missing username, password, or Flask secret prevents startup. Vercel's `/tmp` SQLite file is temporary and private to a function instance; it is suitable for trying the restored feature, not durable or shared records. For reliable database persistence on Vercel, use a hosted database service and configure a persistent database adapter before relying on login history or date plans there.

## Video And Drive Link

Local video setup remains at <http://127.0.0.1:5000/video-setup>. For Vercel, set `FINAL_VIDEO_URL` in Project Settings and redeploy instead of uploading a local file. YouTube/Vimeo links use their hosted players; direct URLs must be public HTTPS video files. The final page remains valid when no video is configured. A local `127.0.0.1` URL is not reachable from Aashi's phone over the internet.

The editing-show button uses `AASHI_EDIT_COLLECTION_URL` in `app.py`. It opens the exact Google Drive folder in a new tab and respects that folder's existing permissions; it does not make the folder public.

## Date Preferences And Privacy

Date submissions show an immediate confirmation and are also recorded in SQLite for the local app. Login history records usernames, time, and success/failure only; it never stores passwords. Proposal and date answers are associated with a visitor's app session record.
