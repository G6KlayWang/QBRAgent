from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from agentic_app.agent import SymmonsAgent
from agentic_app.api_client import from_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with the Symmons WTW agent."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="User request to send to the agent. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI chat model to use.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=6,
        help="Maximum tool-calling loops allowed for a response.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    prompt = args.prompt or sys.stdin.read().strip()
    if not prompt:
        print("Provide a user prompt either as an argument or via stdin.", file=sys.stderr)
        return 1

    api_client = from_env()
    agent = SymmonsAgent(
        api_client,
        model=args.model,
        max_turns=args.max_turns,
    )

    reply = agent.run(prompt)
    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

