import json
from pathlib import Path
from typing import Dict

from app.config import get_settings
from app.rag.pipelines.query import answer_question


def _load_questions(path: Path):
    if not path.exists():
        return []
    questions = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            questions.append(json.loads(line))
    return questions


def run_eval() -> int:
    settings = get_settings()
    questions_path = settings.eval_dir / "questions.jsonl"
    results_path = settings.eval_dir / "results.jsonl"

    questions = _load_questions(questions_path)
    if not questions:
        print(f"No eval questions found at {questions_path}")
        return 0

    settings.eval_dir.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8") as handle:
        for item in questions:
            question = item.get("question", "").strip()
            expected = item.get("expected", "")
            if not question:
                continue
            answer, docs = answer_question(question)
            record: Dict[str, object] = {
                "question": question,
                "expected": expected,
                "answer": answer,
                "sources": [doc.metadata.get("source", "unknown") for doc in docs],
            }
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    print(f"Wrote eval results to {results_path}")
    return len(questions)
