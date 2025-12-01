from dotenv import load_dotenv
import os
import argparse

# Load environment variables
load_dotenv()

from medster.agent import Agent
from medster.utils.intro import print_intro
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Medster - Autonomous Clinical Case Analysis Agent")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Enable task output persistence (saves JSON logs to ./medster_outputs/)"
    )
    parser.add_argument(
        "--no-refinement",
        action="store_true",
        help="Disable simple refinement (no retry on incomplete tasks)"
    )
    args = parser.parse_args()

    print_intro()

    # Create agent with optional features
    agent = Agent(
        persist_outputs=args.persist,
        enable_simple_refinement=not args.no_refinement
    )

    # Create a prompt session with history
    session = PromptSession(history=InMemoryHistory())

    while True:
        try:
            # Prompt the user for input
            query = session.prompt("medster>> ")
            if query.lower() in ["exit", "quit"]:
                print("Session ended. Goodbye!")
                break
            if query:
                # Run the clinical analysis agent
                agent.run(query)
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended. Goodbye!")
            break


if __name__ == "__main__":
    main()
