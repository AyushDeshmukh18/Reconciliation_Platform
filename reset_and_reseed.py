import uuid
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.api.models.audit_log import AuditLog
from backend.api.models.bank_settlement import BankSettlement
from backend.api.models.platform_transaction import PlatformTransaction
from backend.api.models.reconciliation_result import ReconciliationResult
from backend.api.models.reconciliation_run import ReconciliationRun
from backend.api.models.resolution_note import ResolutionNote
from backend.api.models.rule_config import RuleConfig
from backend.api.models.user import User
from backend.config import get_settings
from backend.db.base import Base
from backend.db.seed import load_realistic_data


def reset_and_reseed():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_SYNC_URL, echo=False)

    # Drop all tables
    print("Dropping all existing tables...")
    Base.metadata.drop_all(engine)

    # Recreate tables
    print("Recreating tables...")
    Base.metadata.create_all(engine)

    # Now run the seed script
    print("\nStarting seed process...")
    load_realistic_data()
    print("\nReset and reseed complete!")


if __name__ == "__main__":
    reset_and_reseed()
