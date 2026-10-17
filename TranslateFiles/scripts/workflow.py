"""Shared workflow CLI with this project's literal marker adapter installed."""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT.parents[1] / 'Tools/localization'))
import translation_workflow as shared
from viking_term_adapter import install

install(shared.bridge)

if __name__ == '__main__':
    raise SystemExit(shared.main())
