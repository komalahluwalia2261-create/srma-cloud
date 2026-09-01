"""
Command-line entrypoint.

    srma-cloud screen \
        --config config/example_review.yaml \
        --source-folder <drive_folder_id> \
        --log-sheet <spreadsheet_id> \
        --backend anthropic
"""

from __future__ import annotations

import argparse
import logging
import sys

import yaml

from .adapters.google_drive import GoogleDriveAdapter
from .pipeline import run_full_text_screen
from .prompts.engine import get_client
from .prompts.templates import ReviewCriteria


def main() -> None:
    parser = argparse.ArgumentParser(prog="srma-cloud")
    sub = parser.add_subparsers(dest="command", required=True)

    screen = sub.add_parser("screen", help="Run full-text screening on a watched folder")
    screen.add_argument("--config", required=True, help="Path to review criteria YAML")
    screen.add_argument("--source-folder", required=True, help="Drive folder ID to watch")
    screen.add_argument("--log-sheet", required=True, help="Drive Sheet ID to write decisions to")
    screen.add_argument("--client-secrets", default="client_secrets.json")
    screen.add_argument("--token-cache", default=".srma_cloud_token.json")
    screen.add_argument("--backend", default="anthropic", choices=["anthropic", "openai"])
    screen.add_argument("--since", default=None, help="ISO 8601 timestamp; only screen files modified after this")
    screen.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    if args.command == "screen":
        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        criteria = ReviewCriteria(
            objectives=cfg["objectives"],
            inclusion_criteria=cfg["inclusion_criteria"],
            exclusion_criteria=cfg["exclusion_criteria"],
        )

        adapter = GoogleDriveAdapter.from_oauth_flow(args.client_secrets, args.token_cache)
        client = get_client(args.backend)

        decisions = run_full_text_screen(
            adapter=adapter,
            model_client=client,
            criteria=criteria,
            source_folder_ref=args.source_folder,
            log_destination_ref=args.log_sheet,
            since=args.since,
        )
        included = sum(1 for d in decisions if d.decision == "include")
        print(f"Screened {len(decisions)} files: {included} included, {len(decisions) - included} not.")


if __name__ == "__main__":
    sys.exit(main())
