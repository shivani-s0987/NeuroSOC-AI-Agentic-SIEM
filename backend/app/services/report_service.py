from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Report


def create_report(db: Session, title: str, report_type: str, format: str) -> Report:
    content = f"# {title}\n\nGenerated at {datetime.utcnow().isoformat()}\n\n## Executive Summary\nA synthesized investigation report.\n"
    report = Report(title=title, report_type=report_type, format=format, content=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
