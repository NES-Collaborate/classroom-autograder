"""Entry point for classroom-autograder CLI."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from cli.main import main


def run():
    """Run the CLI application."""
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\nErro: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run()
