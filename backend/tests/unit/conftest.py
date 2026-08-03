from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _noop() -> None:
    pass
