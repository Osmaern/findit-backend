# Member Tasks

The brief needs **commit history from every member**, so every member needs real work to commit. The application itself is finished and tested. What is left is checking it, fixing what the checks find, and writing up the evidence. Each task below ends in a commit by the person who did it.

Tasks belong to a **role**, not a person. Whoever holds the role does them, and the next holder carries on after the rotation. In a team of five, the fifth member helps the lead developer and the tester.

**Rules**

- Commit only work you did and can explain. If a teammate asks "how does this route work?", you should be able to answer.
- Set your own name and email in Git first (see [TEAM.md](../TEAM.md)), so the history shows who did what.
- If an AI assistant helped with a commit, say so in the commit message and in your reflection.
- One task per branch, one pull request per branch. Someone else reviews it.

## Everyone

| Task | Evidence |
| --- | --- |
| Get the app running on your own computer and run `python -m pytest` | Your own pass result added to [TEST_RESULTS.md](TEST_RESULTS.md) (any member, one row each) |
| Be able to explain one route from the page to the database (pick from [DESIGN.md](DESIGN.md)) | Asked at the demo |
| Write your own one-page reflection ([REFLECTION_TEMPLATE.md](REFLECTION_TEMPLATE.md)) | Handed in with the submission |

## Project manager

| ID | Task | Done when |
| --- | --- | --- |
| PM-1 | Write the real dates in the sprint table and the names in the rotation log in [SPRINT_PLAN.md](SPRINT_PLAN.md). Add what each sprint actually delivered. | Commit changes `docs/SPRINT_PLAN.md` |
| PM-2 | Update every status in [RISK_REGISTER.md](RISK_REGISTER.md). Add any new risk the team meets. | Commit changes `docs/RISK_REGISTER.md` |
| PM-3 | Build the presentation from [DEMO_SCRIPT.md](DEMO_SCRIPT.md), choose who speaks for each part, and rehearse with a timer. | Slides file or link added under `docs/`; rehearsal time written in the sprint review notes |
| PM-4 | Tick off [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) and collect every reflection before the deadline. | Checklist fully ticked |

## Lead developer

| ID | Task | Done when |
| --- | --- | --- |
| LD-1 | Give the team a 30-minute walk through the code: a request from the page to the database and back. | Notes added to `docs/DESIGN.md` for anything the walk-through found unclear |
| LD-2 | Create an **empty** MySQL database, point `.env` at it, run `alembic upgrade head`, start the app and register. If it fails, fix the migrations. | Test MT-15 recorded in [TEST_RESULTS.md](TEST_RESULTS.md); any fix committed |
| LD-3 | Change the database password and update `.env`. Never commit `.env`. | Risk R-2 updated in the register |
| LD-4 | Review every pull request, and keep the GitHub test run green on `main`. | Reviews visible on the pull requests |
| LD-5 (optional) | Let a member delete their own account (the Terms currently say requests are handled by hand). Include tests. | Pull request merged, SRS and Terms updated |

## Tester

| ID | Task | Done when |
| --- | --- | --- |
| T-1 | Run manual tests MT-6 to MT-14 in [TEST_RESULTS.md](TEST_RESULTS.md) on real phones and in Firefox. Use two phones for the claim flow. | Every row says Pass or Fail, with name and date |
| T-2 | Make a table of every requirement in the SRS (FR and NFR numbers) against the test that checks it. Find requirements with no test and write tests for at least three. | `docs/TRACEABILITY.md` and the new tests committed |
| T-3 | Open a GitHub issue for every bug (label `bug` and a severity). Check each fix before it is closed. | Issues visible on GitHub |
| T-4 | Run `python -m pytest` after every merge to `main` and record the result. | New rows in section 1 of the results |

## Documentation lead

| ID | Task | Done when |
| --- | --- | --- |
| DL-1 | Read every requirement in [SRS.md](SRS.md) and try it on the running app. Correct anything that is wrong. | Commit changes `docs/SRS.md` |
| DL-2 | Take real screenshots (dashboard, browse, an item, My Claims, My Posts, Moderation, Admin overview, Terms) and add them to the design document. | Images under `docs/screenshots/` and linked from `docs/DESIGN.md` |
| DL-3 | Replace `[contact email to be added by the team]` in `frontend/terms.html`. Read the Terms against what the app really does, and ask your lecturer or a qualified person to review them. | Commit changes `frontend/terms.html` |
| DL-4 | Follow the README on a clean computer exactly as written. Fix every step that does not work. | Commit changes `README.md` |
| DL-5 | Check [UML.md](UML.md) against the code. Fix any diagram that does not match. | Commit changes `docs/UML.md` |
