# Risk Register: FindIt

Scoring: likelihood and impact each 1 (low) to 5 (high). Score = likelihood × impact.

| ID | Risk | Likelihood | Impact | Score | Mitigation | Owner (role) | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-1 | SMS sender name not approved by Arkesel, so codes do not reach all networks | 4 | 5 | 20 | Sender name "FindIt" was approved by Arkesel on 8 November 2026 and texts arrive within seconds. Still test on each network (MTN, Telecel, AirtelTigo) before the demo. | Project manager | Mitigated |
| R-2 | An API key or database password is exposed (it was pasted into a chat during development) | 4 | 5 | 20 | The Arkesel key was replaced on 8 November 2026 (the old one must also be deleted in Arkesel). Still to do: change the database password. Keep `.env` out of Git. | Project manager | Open |
| R-3 | Arkesel balance runs out during testing or the demo | 3 | 4 | 12 | Top up before the demo. Check the balance on the dashboard the day before. | Project manager | Open |
| R-4 | Students share fake or inappropriate posts | 3 | 3 | 9 | Reporting, moderator queue, rate limits on reporting and posting. | Lead developer | Mitigated |
| R-5 | Hidden GPS data in phone photos reveals where an item was found | 4 | 3 | 12 | Photos are re-saved with hidden data removed. Test covers it. | Lead developer | Mitigated |
| R-6 | Brute-force attacks on login or codes | 3 | 4 | 12 | Account lockout, code attempt limit, per-IP rate limits. | Lead developer | Mitigated |
| R-7 | Rate limits are kept in memory, so they reset on restart and do not share across several servers | 3 | 3 | 9 | Acceptable for one server. Move to a shared store (Redis) before scaling out. | Lead developer | Accepted |
| R-8 | Team members commit at different times and clash in shared files | 4 | 3 | 12 | One feature per branch, pull requests, the README contribution steps. | Project manager | Open |
| R-9 | Database schema changes conflict between team members | 3 | 4 | 12 | Migrations in Git, agreed order of `alembic upgrade head`. | Lead developer | Open |
| R-10 | Team member leaves or cannot finish their part | 2 | 4 | 8 | Role rotation every 3 weeks; each feature has a second person who can read it. | Project manager | Open |
| R-11 | Phone-screen layout breaks on small devices | 3 | 2 | 6 | Manual phone-width checklist in the test plan. | Tester | Open |
| R-12 | SMS delivery is slow, so users wait for codes | 3 | 2 | 6 | Show clear message while waiting; allow one resend per minute. | Lead developer | Accepted |
| R-13 | Users forget their password and have no other way back in | 3 | 3 | 9 | SMS password reset. Email reset is not built. | Lead developer | Mitigated |
| R-14 | Legal or privacy concern about storing phone numbers and photos | 2 | 4 | 8 | Phone numbers shown only when allowed. Terms and Privacy page is built and accepted at sign-up. Before launch: add the contact email to the page and have it reviewed by a qualified person. | Project manager | Open |
| R-15 | Google sign-in not built, so a promised login method is missing | 4 | 2 | 8 | A "Google sign-in is coming soon" note is shown on the login and register pages. Decide before launch. | Tester | Open |
