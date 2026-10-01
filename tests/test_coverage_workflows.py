"""Regression contracts for coverage generation and main-branch uploads."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.mark.parametrize("workflow", ["ci.yml", "coverage-main.yml"])
def test_coverage_action_preserves_failure_outputs(workflow: str) -> None:
    """Both coverage lanes use the release with failure-safe artefact naming."""
    path = Path(__file__).resolve().parents[1] / ".github/workflows" / workflow
    text = path.read_text()
    refs = re.findall(
        r"uses: leynos/shared-actions/\.github/actions/generate-coverage@([0-9a-f]+)",
        text,
    )
    assert refs == ["a5765019912a8ab6882b12db049c7cde635f3a85"], (
        "coverage lanes must retain the action's output-on-failure and name fallback"
    )
    assert "with-ratchet: 'true'" in text, "coverage regressions must remain gated"


def test_main_upload_uses_manifest_verified_cli() -> None:
    """Main uploads use the approved CLI manifest rather than the old installer."""
    path = Path(__file__).resolve().parents[1] / ".github/workflows/coverage-main.yml"
    text = path.read_text()
    assert (
        "upload-codescene-coverage@a5765019912a8ab6882b12db049c7cde635f3a85" in text
    ), "the main upload must use the manifest-verified action"
    assert "installer-checksum:" not in text, (
        "the updated upload action rejects the deprecated installer checksum"
    )


def test_main_coverage_uses_upload_mode() -> None:
    """The analysed branch receives an upload rather than a pull-request check."""
    path = Path(__file__).resolve().parents[1] / ".github/workflows/coverage-main.yml"
    text = path.read_text()
    assert "mode: upload" in text, "main coverage must upload to the analysed branch"


def test_main_coverage_dispatch_limits_upload_branch() -> None:
    """A manual dispatch from a feature branch cannot upload main's coverage."""
    path = Path(__file__).resolve().parents[1] / ".github/workflows/coverage-main.yml"
    text = path.read_text()
    assert "github.ref == 'refs/heads/main'" in text, (
        "a dispatch from another branch must not upload main coverage"
    )
