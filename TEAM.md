# Team Guide: FindIt

How we work together. Read this once, then follow it for every task.

## 1. Get the code

In PowerShell, in the folder where you keep projects:

```powershell
git clone https://github.com/Osmaern/findit-backend.git
cd findit-backend
```

## 2. Set up

Follow the "Set up" steps in the [README](README.md): virtual environment, `pip install -r requirements.txt`, your own `.env`, then `alembic upgrade head`.

Never share your `.env` file and never paste a key or password into a chat or an issue.

## 3. Tell Git who you are

The commit history is graded per person, so it must show your own name:

```powershell
git config user.name "Your Full Name"
git config user.email "the email on your GitHub account"
```

## 4. One task, one branch

Pick a task from [docs/MEMBER_TASKS.md](docs/MEMBER_TASKS.md). Then:

```powershell
git checkout main
git pull
alembic upgrade head
git checkout -b task/short-name
```

Run `alembic upgrade head` after **every** pull. New code can need new database columns, and without them the app fails with a 500 error.

## 5. Make the change and test it

```powershell
python -m pytest
python -m uvicorn app.main:app --reload
```

All tests must pass. Try your change in the browser too.

## 6. Commit

```powershell
git status
git add -A
git commit -m "Short summary of what you did"
git push -u origin task/short-name
```

Check `git status` before you add anything. `.env`, `venv/` and `uploads/` must never appear in the list. If they do, stop and ask.

If an AI assistant helped you, say so on the last line of the commit message, for example: `Assisted-by: <tool name>`.

## 7. Pull request

Open a pull request on GitHub and describe what you changed and how you tested it. The lead developer or another teammate reviews it. The tester checks anything that changes what the app does. Merge only when the GitHub test run is green.

## Rules

- One feature or document per branch.
- Commit only what you did and can explain.
- A change to the database needs a migration. Create it with `alembic revision --autogenerate -m "what changed"`, read the file it makes, then run `alembic upgrade head`.
- Never commit secrets, `.env`, `venv/` or uploaded photos.
