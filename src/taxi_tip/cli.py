"""Small command interface, shared by notebooks and shell reproduction."""
import argparse
from .workflow import develop, final_evaluate


def main():
    parser = argparse.ArgumentParser(description="NYC taxi tip study")
    parser.add_argument("stage", choices=["develop", "final", "docs"])
    parser.add_argument("--bootstrap", type=int, default=500)
    args = parser.parse_args()
    if args.stage == "develop":
        develop()
    elif args.stage == "final":
        final_evaluate(args.bootstrap)
    else:
        from .reporting import build_docs
        build_docs()


if __name__ == "__main__":
    main()
