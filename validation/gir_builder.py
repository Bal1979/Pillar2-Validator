"""
Golden-base for valideringssuiten: den komplette, skemagyldige GIR der skal
forblive REN (ingen fund). Genbruger tests/fixtures/gir_valid_rich.xml, så
suiten og enhedstestene deler præcis samme facit.
"""

from __future__ import annotations

import os

_FIXTURE = os.path.join(
    os.path.dirname(__file__), "..", "tests", "fixtures", "gir_valid_rich.xml"
)


def build_base() -> bytes:
    """Returnér den rene golden-GIR som bytes."""
    with open(_FIXTURE, "rb") as fh:
        return fh.read()
