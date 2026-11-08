# Demo Script: FindIt (about 10 minutes)

Run this on the final build. Use a real phone number for sign-up and the approved SMS sender. Have two browser windows ready: one for the owner and one for the finder. Have a moderator account ready (see README, `make_admin`).

## Before the demo (checklist)

- [ ] Arkesel balance is topped up
- [ ] Sender ID approval confirmed
- [ ] Database password and API key have been rotated, and `.env` is not in Git
- [ ] `python -m pytest` passes locally
- [ ] Two test accounts are verified and one moderator account exists
- [ ] Two sample photos with GPS data are ready to show that it is removed

## Script

| Time | Step | What to show | What to say |
| --- | --- | --- | --- |
| 0:00 | Open the site | Dashboard | "FindIt helps students at USTED find lost things and return found ones." |
| 1:00 | Sign up (owner) | Register, enter code from SMS | "Phone number is checked by SMS before the account works." |
| 2:00 | Post a found item | Report a found item, add a photo | "The photo's GPS data is removed before it is saved." |
| 3:00 | Browse and search | Browse, search by word, open the item | "Private details are hidden until the owner agrees." |
| 4:30 | Claim (finder) | Second window: sign in, claim with a message | "The owner gets an SMS. The finder's phone number is not shown yet." |
| 6:00 | Approve (owner) | My Posts, approve the claim | "Approving shares phone numbers and declines other claims." |
| 7:00 | Report a post | Finder reports a post that looks fake | "Reports go to a moderator queue." |
| 7:45 | Moderate | Moderator opens Moderation, removes the post, then restores it | "Removed posts disappear from Browse; the owner is told by SMS." |
| 8:45 | Forgot password | Reset with an SMS code | "Old sessions are signed out after a reset." |
| 9:30 | Close | Show the test results and the SRS | "Everything you saw is tested, and the SRS lists what we did not build." |

## If something goes wrong

- SMS is late: say so, show the sign-up code screen, and continue with a verified account made earlier.
- A page fails: refresh once; if it still fails, move to the next step and say it is a known issue.
- Never show secrets, `.env`, or the database on screen.

## Questions to expect

- **Is Google sign-in working?** No. The button is marked "coming soon".
- **What if someone posts something false?** Any member can report a post; a moderator decides within the queue.
- **Is this secure?** Passwords are hashed with Argon2, codes are stored hashed, login locks after repeated failures, and rate limits apply to sign-up, codes and posting. Limits are kept in memory, so they reset when the server restarts.
