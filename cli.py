"""
Quick way to test the RAG pipeline without running the API server.
Usage: python cli.py "How can I apply for revaluation?"
"""
import sys

from backend.rag.pipeline import answer_question


def main():
    if len(sys.argv) < 2:
        print('Usage: python cli.py "your question"')
        return

    question = " ".join(sys.argv[1:])
    answer, sources = answer_question(question)

    print("\nAnswer:", answer)
    if sources:
        print("\nSources:")
        for s in sources:
            page = f", p.{s['page']}" if s.get("page") else ""
            print(f"  - {s['document']}{page}  (score {s['score']})")


if __name__ == "__main__":
    main()
