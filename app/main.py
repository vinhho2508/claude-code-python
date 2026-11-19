import argparse

from app.agent import run_agent
from app.config import Settings
from app.llm import LLM
from app.skills import registry

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", required=True, help="prompt")
    args = parser.parse_args()

    settings = Settings.from_env()
    registry.register_skills()

    print(run_agent(LLM(settings), args.p))

if __name__ == "__main__":
    main()