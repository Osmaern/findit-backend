# Submission Checklist (Week 8)

Mapped to the group project brief. "Needs the team" means the file or action cannot be completed by the code alone.

## Scope

| Brief | Where | Status |
| --- | --- | --- |
| 3 to 5 core features | The five core features are listed in [SRS.md](SRS.md) section 1 | Done |
| At least one external service | Arkesel SMS | Done, working on a real phone |
| A database | MySQL with Alembic migrations | Done |
| Team of 4 to 5, roles rotating every 3 weeks | [SPRINT_PLAN.md](SPRINT_PLAN.md), rotation log | **Needs the team**: write names and dates in the log |

## Deliverables

| Brief item | Where | Status |
| --- | --- | --- |
| GitHub repository with commit history from every member | The repository, plus [MEMBER_TASKS.md](MEMBER_TASKS.md) | **Needs the team**: every member makes their own commits |
| Final SRS | [SRS.md](SRS.md) | Written. Documentation lead checks it against the running app |
| UML diagrams | [UML.md](UML.md) | Written (use case, class, state, two sequence diagrams) |
| Design document | [DESIGN.md](DESIGN.md) | Written. Documentation lead adds real screenshots |
| Test plan with results, at least one automated test | [TEST_PLAN.md](TEST_PLAN.md) and [TEST_RESULTS.md](TEST_RESULTS.md) | 162 automated tests pass. **Tester runs MT-6 to MT-15** and records results |
| Risk register | [RISK_REGISTER.md](RISK_REGISTER.md) | Written. Project manager keeps the status column current |
| Sprint plans | [SPRINT_PLAN.md](SPRINT_PLAN.md) | Written. **Needs the team**: real dates and what each sprint actually delivered |
| 10-minute demo and presentation | [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Script written. **Needs the team**: slides, rehearsal, who says what |
| Individual one-page reflection linking the project to at least two units | [REFLECTION_TEMPLATE.md](REFLECTION_TEMPLATE.md) | **Each member writes their own** |

## Before the demo

- [ ] Replace `[contact email to be added by the team]` on `frontend/terms.html`
- [ ] Change the database password and update `.env`
- [ ] Delete the old Arkesel API key in the Arkesel dashboard
- [ ] Check the Arkesel balance the day before
- [ ] Rehearse the script once with a timer
- [ ] `python -m pytest` passes on the machine used for the demo
