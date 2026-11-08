# Test Plan: FindIt

## 1. Levels

| Level | What it checks | How |
| --- | --- | --- |
| Unit | Helpers: phone normalising, image cleaning, rate limiter, password hashing | pytest, files `tests/test_*.py` |
| API (integration) | Every route, with its status codes and rules | pytest with FastAPI's test client and an in-memory database |
| Browser (end-to-end) | Pages working together | Playwright script run by hand (see section 4) |
| Manual | Look, feel and phone layout | Checklist in section 5 |

## 2. Automated test files

| File | Covers | Tests |
| --- | --- | --- |
| `tests/test_auth.py` | Register, verify, resend, login, lockout, logout | 11 |
| `tests/test_register_email.py` | Optional email at sign-up | 5 |
| `tests/test_user_model.py` | User table defaults | 3 |
| `tests/test_session.py` | /me and logout cookie | 3 |
| `tests/test_items.py` | Report, browse, photos, validation | 12 |
| `tests/test_claims.py` | Claim, approve, decline, withdraw, returned, contact rules | 22 |
| `tests/test_myposts.py` | My Posts list, close report | 9 |
| `tests/test_password_reset.py` | Forgot and reset password, lockout clearing, session sign-out | 16 |
| `tests/test_images.py` | GPS and camera data removed, rotation, corrupt files | 9 |
| `tests/test_ratelimit.py` | Per-IP limits, proxy header rules, expiry | 8 |
| `tests/test_moderation.py` | Report a post, moderator queue, remove, restore, roles | 17 |
| `tests/test_profile.py` | Edit name, email, password, session kept | 12 |
| `tests/test_sms_reply.py` | Arkesel replies are read: low balance and rejections are logged, the key never is | 8 |
| `tests/test_terms.py` | Sign-up refused without accepting the Terms, time of acceptance saved | 5 |
| `tests/test_admin_users.py` | Admin-only access, totals, people list and search, suspend and restore | 21 |
| `tests/test_health.py` | Health check | 1 |

Total at the last full run: **162 tests, all passing** (run with `python -m pytest`).

The recorded results of every run are in [TEST_RESULTS.md](TEST_RESULTS.md).

## 3. Test cases for the most important rules

| ID | Rule | Test |
| --- | --- | --- |
| TC-1 | A code cannot be reused | `test_code_cannot_be_used_twice` |
| TC-2 | Five wrong guesses lock a code | `test_too_many_wrong_guesses_lock_the_code` |
| TC-3 | Owner phone is hidden until approval | `test_pending_claim_never_reveals_owner_phone` |
| TC-4 | Owner phone shows only if allowed | `test_owner_phone_shared_only_when_item_allows_contact` |
| TC-5 | Only the owner can decide a claim | `test_only_the_owner_can_decide` |
| TC-6 | Approving closes the other claims | `test_approve_updates_everything` |
| TC-7 | SMS text never contains the claim message or a phone number | `test_claim_sms_never_contains_the_claim_message_or_phones` |
| TC-8 | Photo GPS data is removed | `test_gps_and_camera_details_are_removed_from_jpeg` |
| TC-9 | Members cannot reach admin routes | `test_members_cannot_use_the_admin_routes` |
| TC-10 | Password change signs out older sessions | `test_reset_signs_out_older_sessions`, `test_password_change_keeps_this_browser_signed_in` |
| TC-11 | A failed SMS does not break the action | `test_a_failed_sms_does_not_break_the_claim` |
| TC-12 | Rate limit cannot be dodged with a fake forwarded address | `test_a_client_cannot_dodge_the_limit_by_adding_its_own_forwarded_entry` |

## 4. Browser checks run by hand

Run these with the test server and a stubbed SMS sender, then check the screenshots:

1. Claim flow: post item, claim it, approve it, mark returned.
2. My Posts: close a report and check the claimant's status changes.
3. Moderation: report a post, remove it as a moderator, restore it, and check a member cannot open the admin page.
4. Password reset: request a code, set a new password, log in with the new one.
5. Profile: save details, change password, stay signed in.
6. Admin overview: as an admin, suspend a person, check they cannot log in, restore them, and check a member cannot open the page.
7. Terms: try to register without ticking the box (it must refuse), then tick it and register. Open the Terms link from the form.

Not yet run and recorded on the final build. Record the date, tester and result in the sprint review notes each time they are run.

## 5. Manual checklist

- [ ] Dashboard looks right at 1366 px wide
- [ ] Every page works at 360 px wide (phone) without sideways scrolling
- [ ] Every button shows a clear message on success and on error
- [ ] Keyboard can reach every form field and button
- [ ] No page shows an error in the browser console

## 6. Defects and exit criteria

A release is ready when the automated suite passes on GitHub, all manual checks pass, and no open defect is rated high.

Defects are logged as GitHub issues with the label `bug` and a severity (high, medium, low).
