import argparse

from app.rag.pipelines.eval import run_eval
from app.rag.pipelines.index import build_index
from app.rag.pipelines.query import answer_question
from app.bot.telegram import run_telegram_bot


def _cmd_ingest(_args: argparse.Namespace) -> None:
    count = build_index()
    print(f"Indexed {count} chunks")


def _cmd_query(args: argparse.Namespace) -> None:
    answer, docs = answer_question(args.question)
    print(answer)
    if docs:
        print("\nSources:")
        for doc in docs:
            source = doc.metadata.get("source", "unknown")
            print(f"- {source}")


def _cmd_eval(_args: argparse.Namespace) -> None:
    run_eval()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Load, chunk, and index docs from data/raw")
    ingest.set_defaults(func=_cmd_ingest)

    query = sub.add_parser("query", help="Ask a question")
    query.add_argument("question")
    query.set_defaults(func=_cmd_query)

    eval_cmd = sub.add_parser("eval", help="Run eval set")
    eval_cmd.set_defaults(func=_cmd_eval)

    telegram = sub.add_parser("telegram-bot", help="Start Telegram bot with aiogram")
    telegram.set_defaults(func=lambda _: run_telegram_bot())

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
