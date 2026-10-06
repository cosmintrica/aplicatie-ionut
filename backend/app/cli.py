import argparse
import json
from .ingest import seed_database
from .settings import default_settings


def main():
    parser = argparse.ArgumentParser(description="Prețuri achiziții · instrumente offline")
    parser.add_argument("command", choices=["seed", "check"])
    args = parser.parse_args()
    result = seed_database(default_settings())
    print(json.dumps({"command": args.command, "mode": "offline_snapshot", **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
