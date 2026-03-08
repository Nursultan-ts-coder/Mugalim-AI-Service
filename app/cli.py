import argparse

from app.pipelines.eval import run_eval
from app.pipelines.index import build_index
from app.pipelines.query import answer_question
from app.whatsapp_bot import run_whatsapp_bot


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


def _cmd_whatsapp_bot(args: argparse.Namespace) -> None:
    run_whatsapp_bot(session_name=args.session_name, database=args.database)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Load, chunk, and index docs")
    ingest.set_defaults(func=_cmd_ingest)

    query = sub.add_parser("query", help="Ask a question")
    query.add_argument("question")
    query.set_defaults(func=_cmd_query)

    eval_cmd = sub.add_parser("eval", help="Run eval set")
    eval_cmd.set_defaults(func=_cmd_eval)

    whatsapp = sub.add_parser("whatsapp-bot", help="Start WhatsApp bot with Neonize")
    whatsapp.add_argument(
        "--session-name",
        default="rag_whatsapp_bot",
        help="Neonize client session name",
    )
    whatsapp.add_argument(
        "--database",
        default="data/neonize.db",
        help="Path to Neonize session database",
    )
    whatsapp.set_defaults(func=_cmd_whatsapp_bot)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
