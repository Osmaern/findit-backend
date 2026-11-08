# Software Requirements Specification: FindIt

Version 1.0 · Covers the system as built through Sprint 4.

## 1. Purpose and scope

FindIt is a web application where people on campus report lost items and found items, search for them, and claim them. It sends SMS messages through Arkesel at the key points: sign-up, password reset, claims and moderation decisions.

In scope: accounts, item reports, search, claims, My Posts, moderation, admin overview, profile, SMS notifications.

The five **core features** (as the course brief asks for 3 to 5):

1. Accounts with SMS verification and password reset.
2. Report and browse lost and found items, with photos.
3. Claim an item and return it to its owner (My Posts and My Claims).
4. Moderation: report a post, review the queue, remove or restore.
5. Admin overview: site totals, all people, suspend and restore.

Supporting features: profile and password change, Terms and Privacy at sign-up, photo clean-up, rate limits.

**External service:** Arkesel SMS. **Database:** MySQL.

Out of scope for this version: email delivery, Google sign-in (the button is shown disabled), in-app chat, payments, native mobile apps, and a public API for third parties.

## 2. Users

| User | Description |
| --- | --- |
| Member | Any verified person with a Ghana phone number. Can report, browse, claim and report posts. |
| Moderator | A member given the moderator role by the team. Reviews reports and can remove or restore posts. |
| Admin | Same as moderator, plus the Admin overview: site totals, the list of all people, and suspending or restoring accounts. Set with the same command-line tool. |
| Visitor | Not logged in. Can browse open items and read item pages. |

## 3. Functional requirements

### 3.1 Accounts

| ID | Requirement |
| --- | --- |
| FR-1 | A person registers with full name, Ghana phone number, password and optional email. |
| FR-2 | Phone numbers are stored in the form 233XXXXXXXXX and must be valid Ghana numbers. |
| FR-3 | A 6-digit code is texted to the phone. The code expires after 10 minutes and allows 5 wrong guesses. |
| FR-4 | A new code cannot be requested within 60 seconds of the last one. Each new code cancels the previous one. |
| FR-5 | Login needs a verified phone. After 5 wrong passwords the account is locked for 15 minutes. |
| FR-6 | A logged-in session lasts 30 minutes. Logout clears it. |
| FR-7 | Forgot password sends a reset code by SMS. The reply is the same for every number, so nobody can learn which numbers have accounts. |
| FR-8 | A password change or reset signs out every other session. |
| FR-9 | A member can change name and email. Phone numbers are not editable on the site. |
| FR-10 | A member can change password by giving the current password. |
| FR-39 | Registration requires ticking "I have read and accept the Terms and Privacy Policy", which links to the Terms page. Without it no account is created and no SMS is sent. The time of acceptance is saved on the account. Accounts made before this rule have no saved time. |

### 3.2 Items

| ID | Requirement |
| --- | --- |
| FR-11 | A member can report a lost item or a found item with title, category, location, date, description. |
| FR-12 | A found-item report requires a private detail that only the finder knows (for example, the lock screen). It is never shown publicly. |
| FR-13 | A report can have up to 2 photos, each up to 3 MB, in JPEG, PNG or WEBP. |
| FR-14 | Uploaded photos are re-saved without hidden data (GPS location, camera, time). |
| FR-15 | Reports expire after 60 days and then stop appearing in search. |
| FR-16 | Anyone can browse and search open reports by text, kind, category and location. |
| FR-17 | The owner can close a report. Closing declines any waiting claims and texts those claimants. |
| FR-18 | The owner can see all their own reports, with counts of waiting claims, on My Posts. |

### 3.3 Claims

| ID | Requirement |
| --- | --- |
| FR-19 | A logged-in member can claim another member's open item with a message of at least 10 characters. |
| FR-20 | The owner is texted when a claim arrives. The text does not contain the claim message or any phone number. |
| FR-21 | Only the owner can approve or decline a claim. A decided claim cannot be decided again. |
| FR-22 | Approving a claim texts the claimant, closes all other waiting claims, and takes the item off the public list. |
| FR-23 | The owner's phone number is shown to the claimant only after approval, and only when the owner allowed contact. The claimant's phone number is shown to the owner only after approval. |
| FR-24 | A claimant can withdraw a waiting claim. |
| FR-25 | The owner can mark an approved item as returned. |
| FR-26 | A member can hold at most 10 waiting claims at a time. |

### 3.4 Moderation

| ID | Requirement |
| --- | --- |
| FR-27 | A member can report a post with a reason (spam, inappropriate, fake, other) and optional details. Each member can report a post once. |
| FR-28 | Moderators see waiting reports, with the count of people who reported the same post. |
| FR-29 | A moderator can remove a post. This closes every waiting report on it, declines waiting claims, and texts the owner and claimants. |
| FR-30 | A moderator can dismiss a report, or restore a removed post. |
| FR-31 | Members cannot reach moderation pages or routes. |

### 3.5 Notifications

| ID | Requirement |
| --- | --- |
| FR-32 | SMS is sent for: verification codes, reset codes, password changes, new claims, claim decisions, closed reports, removed posts, account suspension and restoring. |
| FR-33 | A failed SMS never undoes the action that caused it. |

### 3.6 Administration

| ID | Requirement |
| --- | --- |
| FR-34 | Only admins can open the Admin overview and its routes. Members and moderators get 403. |
| FR-35 | The overview shows totals for people (all, verified, suspended, staff), posts (open lost, open found, returned, closed, removed, expired), claims (by status) and waiting reports. |
| FR-36 | An admin can list all people and search by name, email or phone (a phone can be typed as 0244... or 233244...). A filter shows only suspended people. |
| FR-37 | An admin can suspend an account. The person is signed out at once, cannot log in (the message says the account is suspended), and gets an SMS. Admins cannot suspend themselves or another admin. |
| FR-38 | An admin can restore a suspended account. The person can log in again with a fresh login; sessions from before the suspension stay signed out. |

## 4. Non-functional requirements

| ID | Category | Requirement |
| --- | --- | --- |
| NFR-1 | Security | Passwords are stored with Argon2id. Tokens are signed (HS256) and kept in httpOnly cookies. |
| NFR-2 | Security | One-time codes are stored as keyed hashes (HMAC-SHA256), never in plain text. |
| NFR-3 | Security | Rate limits apply to login, sign-up, code requests and reporting, per IP address. |
| NFR-4 | Privacy | Private details and phone numbers are returned only to the people allowed to see them. |
| NFR-5 | Privacy | Logs never contain the SMS API key, passwords or codes. |
| NFR-6 | Reliability | The app keeps working when the SMS provider is down. Failed texts are logged and the action still succeeds. |
| NFR-7 | Scalability | Routes and models are added as one file per feature. Database access goes through SQLAlchemy with pooled connections. |
| NFR-8 | Usability | Pages are designed for phone screens with a 16 px side margin. Phone-width checks are still to be done (see Test Plan). |
| NFR-9 | Maintainability | Automated tests cover the API. They run on every push through GitHub Actions. |
| NFR-10 | Compatibility | Target: current Chrome and Edge. Tested in Chromium and Edge on Windows so far; Firefox is not yet tested. |

## 5. Constraints

- SMS goes through Arkesel. The sender name must be approved by Arkesel before messages reach all networks.
- The database is MySQL 8.0. The tests use SQLite in memory.
- The team builds with Python 3.13 on Windows.

## 6. Acceptance

The system is accepted when every FR is covered by a passing automated test or a recorded manual test, and the demo script in `docs/DEMO_SCRIPT.md` runs without errors.
