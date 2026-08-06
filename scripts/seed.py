#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.database import engine
from backend.db.seed import run_seed
from backend.models.base import Base


def main() -> None:
    Base.metadata.create_all(bind=engine)
    run_seed()


if __name__ == "__main__":
    main()
