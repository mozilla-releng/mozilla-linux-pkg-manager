import argparse

# from datetime import datetime, timedelta


def delete_nightly_versions(retention_days):
    # Logic to delete old versions in the nightly channel based on retention days
    pass


def main():
    parser = argparse.ArgumentParser(description="mozilla-deb-pkg-manager")
    subparsers = parser.add_subparsers(dest="command")

    # Subparser for the 'clean-up' command
    clean_up_parser = subparsers.add_parser(
        "clean-up", help="Clean up package versions based on channel rules."
    )
    clean_up_parser.add_argument(
        "--channel",
        type=str,
        help="Channel of the packages (e.g., nightly, stable)",
        required=True,
    )
    clean_up_parser.add_argument(
        "--retention-days",
        type=int,
        help="Retention period in days for package deletion in the nightly channel",
    )

    args = parser.parse_args()

    if args.command == "clean-up":
        if args.channel == "nightly":
            if args.retention_days is None:
                raise ValueError(
                    "Retention days must be specified for the nightly channel"
                )
            delete_nightly_versions(args.retention_days)
        else:
            raise ValueError("Only the nightly channel is supported")
