# Test Results: FindIt

This file records what was actually run and what happened. Add a row every time a test is run. Only write a result you saw yourself.

## 1. Automated tests (pytest)

| Run | Date | Where | Tests | Result |
| --- | --- | --- | --- | --- |
| 1 | 8 Nov 2026 | Osman's Windows computer, Python 3.13.14 | 154 | **154 passed** in 64.16 s (1 harmless library warning) |
| 2 | 8 Nov 2026 | Development environment (Linux), after adding the SMS reply tests | 162 | **162 passed** |
| 3 | | | | (fill in: run `python -m pytest` after applying the latest files, and paste the last line) |

The tests use an in-memory database and a fake SMS sender, so they never send a real text.

## 2. Manual tests on the running app

Result is **Pass**, **Fail** or **Not run**. For every Fail, open a GitHub issue and write its number in Notes.

| ID | Test | Device and browser | Tester | Date | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| MT-1 | A real text arrives on a real phone within a minute | Real phone, Ghana network | Osman | 8 Nov 2026 | Pass | Arrived on time after Arkesel approved the sender name. Sender name shown was not written down. |
| MT-2 | Register with the Terms box unticked is refused with a clear message | Chrome, Windows | Osman | 8 Nov 2026 | Pass | |
| MT-3 | The Terms link opens the Terms page | Chrome, Windows | Osman | 8 Nov 2026 | Pass | |
| MT-4 | My Posts, My Claims and Profile pages open without an error | Chrome, Windows | Osman | 8 Nov 2026 | Pass | |
| MT-5 | Admin overview opens for an admin with totals and the people list | Chrome, Windows | Osman | 8 Nov 2026 | Pass | |
| MT-6 | Register with the box ticked, enter the SMS code, log in | | | | Not run | |
| MT-7 | Post a lost item with a photo; it appears in Browse and My Posts | | | | Not run | |
| MT-8 | Full claim flow with two phones: claim, SMS to owner, approve, SMS to claimant, mark returned | | | | Not run | |
| MT-9 | Report a post, then remove and restore it as a moderator | | | | Not run | |
| MT-10 | Forgot password: code arrives, new password works, old one does not | | | | Not run | |
| MT-11 | As an admin, suspend a person: they cannot log in and get a text; restore them | | | | Not run | |
| MT-12 | A member and a moderator cannot open the Admin overview | | | | Not run | |
| MT-13 | Every page works at 360 px wide on a real phone, with no sideways scrolling | | | | Not run | |
| MT-14 | All pages work in Firefox | | | | Not run | |
| MT-15 | Setting up an empty database with `alembic upgrade head` works from scratch | | | | Not run | |

## 3. Informal checks during development

The developer also ran browser scripts (Playwright) against a test copy of the app on 8 November 2026. They covered claims, My Posts, password reset, moderation, profile, the Admin overview and the Terms box, and every check in them passed. These scripts are not stored in the repository, so the team cannot repeat them. Do not use them as evidence in place of Section 2.

## 4. Defects found and fixed

| ID | Problem | Found by | Fix | Status |
| --- | --- | --- | --- | --- |
| D-1 | Sessions were invalidated by comparing timestamps to the second, so a test failed at random | Automated test (flaky) | Replaced with a `token_version` counter | Fixed |
| D-2 | `make_admin` crashed when printing the result after its database session closed | Manual run | Build the message inside the session | Fixed |
| D-3 | The Logout link showed when it should be hidden (a style overrode `hidden`) | Visual check | One global rule for `[hidden]` | Fixed |
| D-4 | A test for anonymous claims was logged in by a leftover cookie | Failing test | Clear cookies in the test | Fixed |
| D-5 | Texts said "Successfully Sent" but never arrived: the Arkesel balance was 0 and the sender name was pending. The app ignored Arkesel's reply. | Manual test on a real phone | Sender name approved, account topped up, and the app now logs warnings for rejected texts and low balance | Fixed |
| D-6 | The Terms field accepted the word "yes" as agreement | Automated test | Only a real `true` counts | Fixed |
| D-7 | A suspended person was told to "verify your phone number" at login | Review while building suspension | A clear "account suspended" message | Fixed |
| D-8 | `requirements.txt` did not list Pillow, so a fresh install would fail on photos | Review of `git status` | Added `Pillow==13.0.0` | Fixed |
| D-9 | The dashboard search box was cut off on a phone | Screenshot at 360 px | Search bar moved to its own line | Fixed |
| D-10 | Login, register and forgot-password failed with a 500 error after new files were copied in but before `alembic upgrade head` was run | Manual run | Ran the migration. Rule: run `alembic upgrade head` after every update. | Fixed |

## 5. Summary

- Automated: 162 of 162 pass in the latest run.
- Manual: 5 passed, 10 not yet run. Run MT-6 to MT-15 before the demo and record the results here.
- Open defects: none known. Add any new ones to Section 4.
| 3 | 8 Nov 2026 | Osman's Windows computer, Python 3.13.14, after Pack G | 162 | **162 passed** |