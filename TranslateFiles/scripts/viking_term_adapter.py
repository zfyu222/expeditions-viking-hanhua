"""Project-only literal treatment of actual frozen square-bracket game markers.

The frozen source strings are game text, including variable markers. AINiee's
regex inference treats colon/slash markers as character classes. Keep the pinned
helper and every other inferred regex unchanged; install this before workflow use.
"""
import json
from pathlib import Path
import re


PROJECT = Path(__file__).resolve().parents[2]
FROZEN = PROJECT / 'TranslateFiles/glossary/r8/freeze_731eced6/built/glossary_reviewed.json'
MARKER = re.compile(r'\[(?:[A-Za-z][A-Za-z0-9]*(?::[A-Za-z][A-Za-z0-9 /:]*)?|[A-Za-z]+/[A-Za-z]+)\]')


def install(bridge):
    if getattr(bridge.helper, '_viking_literal_adapter', False):
        return bridge.helper()
    original = bridge.helper()
    data = json.loads(FROZEN.read_text(encoding='utf-8'))
    literal_sources = frozenset(row['source'] for table in ('characters', 'terms', 'non_translate')
                               for row in data.get(table, []) if MARKER.fullmatch(row['source']))

    class VikingGlossaryHelper(original):
        @classmethod
        def get_source_state(cls, source_text):
            if source_text in literal_sources:
                return cls.STATE_VALID
            return super().get_source_state(source_text)

    def project_helper():
        return VikingGlossaryHelper

    project_helper._viking_literal_adapter = True
    bridge.helper = project_helper
    return VikingGlossaryHelper
