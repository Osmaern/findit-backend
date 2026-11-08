from app.models.user import User  # noqa: F401
from app.models.otp import OTPCode  # noqa: F401
from app.models.item import Item, ItemPrivate, ItemPhoto  # noqa: F401
from app.models.claim import Claim  # noqa: F401

# Any other module in this package (a new feature's models) is imported automatically,
# so its table is registered for Alembic without editing this file.
import importlib  # noqa: E402
import pkgutil  # noqa: E402

for _module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_module.name}")
