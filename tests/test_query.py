import os
from pathlib import Path

import pytest

from app.config import get_settings
from app.pipelines.query import answer_question


def _has_index(chroma_dir: Path) -> bool:
    return chroma_dir.exists() and any(chroma_dir.iterdir())


@pytest.mark.skipif(
    not _has_index(get_settings().chroma_dir),
    reason="No Chroma index found",
)
def test_answer_question_smoke():
    answer, _docs = answer_question("What files are in this knowledge base?")
    assert isinstance(answer, str)
    assert len(answer) > 0
