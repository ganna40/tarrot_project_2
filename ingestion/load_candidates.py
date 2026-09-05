#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import apply_additive_migrations
from app.models import Base, CardCorrespondence, CardMeaning, RelationRule, TarotCard
from app.seed import seed_public_domain_knowledge


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the validated public-domain tarot dataset into PostgreSQL.")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "sqlite:///./tarot.db"),
        help="SQLAlchemy database URL. Defaults to DATABASE_URL or sqlite:///./tarot.db.",
    )
    args = parser.parse_args()

    engine = create_engine(args.database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    apply_additive_migrations(engine)
    with Session(engine) as session:
        seed_public_domain_knowledge(session)
        session.commit()
        counts = {
            "cards": session.scalar(select(func.count()).select_from(TarotCard)),
            "meanings": session.scalar(select(func.count()).select_from(CardMeaning)),
            "correspondences": session.scalar(select(func.count()).select_from(CardCorrespondence)),
            "relation_rules": session.scalar(select(func.count()).select_from(RelationRule)),
        }
    engine.dispose()
    print("Curated tarot dataset loaded: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
