# -*- encoding: utf-8 -*-
"""Compare copied operation-family names against the sibling KERIA source."""

from pathlib import Path
import re

import pytest


def test_operation_family_names_match_keria_spec_builder():
    from signify.keria_types import OPERATION_FAMILY_NAMES

    repo_root = Path(__file__).resolve().parents[2]
    specing = repo_root.parent / "keria" / "src" / "keria" / "app" / "specing.py"
    if not specing.exists():
        pytest.skip("sibling KERIA repo not present for drift check")

    text = specing.read_text()
    match = re.search(
        r'self\.spec\.components\.schemas\["Operation"\]\s*=\s*\{\s*"oneOf":\s*\[(.*?)\]\s*\}',
        text,
        re.DOTALL,
    )
    assert match is not None, "unable to find Operation oneOf block in keria app specing.py"

    names = tuple(re.findall(r"#/components/schemas/([A-Za-z]+Operation)", match.group(1)))
    assert names == OPERATION_FAMILY_NAMES
