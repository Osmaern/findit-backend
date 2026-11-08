# FindIt

A lost-and-found web app for USTED. Students and staff can report lost items and found items, search the list, claim an item, and get SMS updates through Arkesel.

## What it does

- Sign up with a Ghana phone number (accepting the Terms), verify it with an SMS code, log in
- Report a lost or found item (up to 2 photos, optional private detail, optional phone sharing)
- Browse and search open items
- Claim an item, approve or decline claims, mark items as returned
- My Posts: see your reports, close them
- Report a post to moderators; moderators can remove or restore posts
- Profile: change name, email and password
- Forgot password by SMS code
- Admin overview: site totals, all people, suspend and restore accounts

Documents are in `docs/`: [SRS](docs/SRS.md), [UML](docs/UML.md), [design](docs/DESIGN.md), [test plan](docs/TEST_PLAN.md), [test results](docs/TEST_RESULTS.md), [risk register](docs/RISK_REGISTER.md), [sprint plan](docs/SPRINT_PLAN.md), [demo script](docs/DEMO_SCRIPT.md), [submission checklist](docs/SUBMISSION_CHECKLIST.md) and [member tasks](docs/MEMBER_TASKS.md).

## Set up on your computer (Windows, PowerShell)

You need Python 3.13, MySQL 8.0 (port 3307), and VS Code.

```powershell
cd findit-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a file called `.env` in `findit-backend` with these lines (fill in your own values, never commit this file):

```
DATABASE_URL=mysql+pymysql://findit_app:YOUR_PASSWORD@localhost:3307/findit
SECRET_KEY=a-long-random-string-of-at-least-32-characters
ARKESEL_API_KEY=your-arkesel-key
ARKESEL_SENDER_ID=FindIt
```

Create the database tables and run the app:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/dashboard.html.

## Run the tests

```powershell
python -m pytest
```

The tests use an in-memory database and do not send real SMS. They need no `.env` file.

## Make someone a moderator or admin

Roles are never changed on the website. Run this on the server, with the person already registered:

```powershell
python -m app.scripts.make_admin 0244123456 moderator
python -m app.scripts.make_admin 0244123456 admin
```

A moderator handles reported posts. An admin can do that too, and also opens the Admin overview.

## Project layout

| Folder | What is in it |
| --- | --- |
| `app/core` | Settings, database, password hashing, tokens, rate limiting |
| `app/models` | Database tables (one file per feature) |
| `app/schemas` | Request and response shapes, with validation |
| `app/routers` | API routes (one file per feature, added automatically) |
| `app/services` | SMS and image cleaning |
| `app/scripts` | Command-line tools for the team |
| `frontend` | The web pages (plain HTML, CSS and JavaScript) |
| `tests` | Automated tests (run with pytest) |
| `docs` | SRS, UML, design, test plan and results, risk register, sprint plan, demo script, checklists |

## Contributing

Read [TEAM.md](TEAM.md). In short: one branch per task, run `alembic upgrade head` after every pull, run `python -m pytest` before every commit, and open a pull request.

Never commit `.env`, `venv/` or `uploads/`. They are in `.gitignore`.
