# Sprint Plan: FindIt

Four sprints of two weeks each cover the eight weeks of the course. Each sprint ends with a working build on `main`, a demo to the group, and a short review. Write the real dates next to the week numbers.

| Sprint | Weeks and dates | Goal | Main features | Exit check |
| --- | --- | --- | --- | --- |
| 1 | Weeks 1–2: ____ | Accounts and browsing work | Sign-up with phone verification, sign-in, sign-out, post a lost or found item, browse and search, item page, dashboard | Register, verify, post and find an item in the browser |
| 2 | Weeks 3–4: ____ | Claims work end to end | Claim an item, owner approves or declines, My Posts, My Claims, SMS messages | Full claim flow, with SMS sent |
| 3 | Weeks 5–6: ____ | Safety and recovery | Forgot password, profile and password change, photo clean-up (removes GPS data), rate limits | Reset works; photos have no GPS data; limits return a clear message |
| 4 | Weeks 7–8: ____ | Moderation, polish and launch readiness | Report a post, moderator queue, remove and restore, docs, CI, security checks, demo rehearsal | All tests pass on GitHub; demo script runs in 10 minutes |

## Role rotation

The brief asks for four roles that rotate every three weeks. With eight weeks that gives three periods.

| Role | Responsibility |
| --- | --- |
| Project manager | Plans each sprint, runs the daily check and the review, owns the risk register, keeps the submission checklist |
| Lead developer | Decides how things are built, reviews every pull request, keeps `main` working |
| Tester | Owns the test plan and results, runs the manual checks, logs bugs, checks every fix |
| Documentation lead | Keeps the SRS, UML, design document, README and demo notes true to the app |

A fifth member (if the team has five) is a developer who works on tasks from the lead developer and joins the rotation.

### Rotation log (fill in as it happens)

| Period | Project manager | Lead developer | Tester | Documentation lead |
| --- | --- | --- | --- | --- |
| Weeks 1–3 | | | | |
| Weeks 4–6 | | | | |
| Weeks 7–8 | | | | |

## Ceremonies

- **Sprint start (30 min):** pick items from the backlog, split them into branches, agree the exit check.
- **Daily check (10 min):** what finished, what is blocked, who needs help.
- **Sprint review (30 min):** demo the exit check; log any failures as `bug` issues.
- **Retrospective (20 min):** one thing to keep, one to change. Write it in `docs/SPRINT_PLAN.md`.

## Definition of done

A feature is done when:

1. It has tests that pass with `python -m pytest`.
2. Its pull request has been reviewed by one other teammate.
3. Migrations are included if the database changed.
4. The SRS or README is updated if behaviour changed.
5. The change works in the browser at a desktop width and a phone width.
