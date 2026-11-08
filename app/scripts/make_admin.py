"""Gives a registered person a moderator or admin role.

Run it on the server, from the project folder, with the virtual environment on:

    python -m app.scripts.make_admin 0244123456 admin
    python -m app.scripts.make_admin 0244123456 moderator
    python -m app.scripts.make_admin 0244123456 member      (takes the role away)

Roles are never changed through the website, so nobody can promote themselves.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.auth import normalize_phone

ROLES = ("member", "moderator", "admin")


def set_role(db: Session, phone: str, role: str) -> User:
    if role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}")
    user = db.scalar(select(User).where(User.phone == normalize_phone(phone)))
    if user is None:
        raise LookupError("No account has that phone number")
    user.role = role
    db.commit()
    return user


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    with SessionLocal() as db:
        try:
            user = set_role(db, argv[1], argv[2])
            # Read the fields while the session is still open: the commit expires them.
            summary = f"{user.full_name} ({user.phone}) is now: {user.role}"
        except (ValueError, LookupError) as error:
            print(f"Error: {error}")
            return 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
