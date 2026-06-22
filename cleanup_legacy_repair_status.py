from __future__ import annotations

import argparse

from app.core.database import SessionLocal, engine
from app.shared.models import BaseModel

# Import models so SQLAlchemy knows about the tables
from app.modules.users.model import User  # noqa: F401
from app.modules.roles.model import Role  # noqa: F401
from app.modules.permissions.model import Permission  # noqa: F401
from app.modules.employee.model import Employee  # noqa: F401
from app.modules.branch.model import Branch  # noqa: F401
from app.modules.department.model import OrgUnitType  # noqa: F401
from app.modules.attendance.model import Attendance  # noqa: F401
from app.modules.leave.model import LeaveRequest  # noqa: F401
from app.modules.holiday.model import Holiday  # noqa: F401
from app.modules.shifts.model import Shift  # noqa: F401
from app.modules.asset_mgmt.model import Asset, AssetCategory, AssetAssignment, AssetRequest, AssetRepairRequest, AssetMaintenance, AssetHistory, BulkJob  # noqa: F401


def cleanup_legacy_repair_status(target_status: str) -> int:
    BaseModel.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        rows = (
            db.query(AssetRepairRequest)
            .filter(AssetRepairRequest.status == "REPLACEMENT_REQUIRED")
            .all()
        )

        count = 0
        for row in rows:
            row.status = target_status
            db.add(row)
            count += 1

        db.commit()
        return count
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize legacy repair request statuses left over from the old replacement flow."
    )
    parser.add_argument(
        "--status",
        default="UNREPAIRABLE",
        choices=["UNREPAIRABLE", "CANCELLED", "SENT_BACK_TO_USER"],
        help="Replacement status to use for legacy REPLACEMENT_REQUIRED rows.",
    )
    args = parser.parse_args()

    updated = cleanup_legacy_repair_status(args.status)
    print(f"Updated {updated} legacy repair request row(s) to {args.status}.")


if __name__ == "__main__":
    main()
