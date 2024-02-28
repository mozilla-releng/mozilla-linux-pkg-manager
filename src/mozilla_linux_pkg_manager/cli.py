import argparse
import asyncio
import logging
import os
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from fnmatch import fnmatch
from itertools import islice
from pprint import pformat

import requests
import requests.exceptions as requests_exceptions
from google.api_core import exceptions as api_exceptions
from google.api_core import retry_async
from google.auth import exceptions as auth_exceptions
from google.cloud import artifactregistry_v1

logging.basicConfig(
    format="%(asctime)s - mozilla-linux-pkg-manager - %(levelname)s - %(message)s",
    level=logging.INFO,
)

RETRYABLE_TYPES = (
    api_exceptions.TooManyRequests,  # 429
    api_exceptions.InternalServerError,  # 500
    api_exceptions.BadGateway,  # 502
    api_exceptions.ServiceUnavailable,  # 503
    api_exceptions.GatewayTimeout,  # 504
    ConnectionError,
    requests.ConnectionError,
    requests_exceptions.ChunkedEncodingError,
    requests_exceptions.Timeout,
)

# Some retriable errors don't have their own custom exception in api_core.
ADDITIONAL_RETRYABLE_STATUS_CODES = (408,)


def should_retry(exc):
    """Predicate for determining when to retry."""
    if isinstance(exc, RETRYABLE_TYPES):
        return True
    elif isinstance(exc, api_exceptions.GoogleAPICallError):
        return exc.code in ADDITIONAL_RETRYABLE_STATUS_CODES
    elif isinstance(exc, auth_exceptions.TransportError):
        return should_retry(exc.args[0])
    else:
        return False


ASYNC_RETRY = retry_async.AsyncRetry(predicate=should_retry)


async def batch_delete_versions(targets, args):
    client = artifactregistry_v1.ArtifactRegistryAsyncClient()
    for package in targets:
        batches = batched(targets[package], 50)
        for batch in batches:
            logging.info(
                f"Deleting {format(len(batch), ',')} expired package versions for {package}"
            )
            request = artifactregistry_v1.BatchDeleteVersionsRequest(
                parent=package,
                names=batch,
                validate_only=args.dry_run,
            )
            operation = await client.batch_delete_versions(
                request=request, retry=ASYNC_RETRY
            )
            await operation.result()


async def get_repository(args):
    client = artifactregistry_v1.ArtifactRegistryAsyncClient()
    parent = f"projects/{os.environ['GOOGLE_CLOUD_PROJECT']}/locations/{args.region}/repositories/{args.repository}"
    get_repository_request = artifactregistry_v1.GetRepositoryRequest(
        name=parent,
    )
    repository = await client.get_repository(
        request=get_repository_request, retry=ASYNC_RETRY
    )
    return repository


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    batch = tuple(islice(it, n))
    while batch:
        yield batch
        batch = tuple(islice(it, n))


async def list_packages(repository):
    client = artifactregistry_v1.ArtifactRegistryAsyncClient()
    request = artifactregistry_v1.ListPackagesRequest(
        parent=repository.name,
        page_size=1000,
    )
    packages = await client.list_packages(request=request, retry=ASYNC_RETRY)
    return packages


async def list_versions(package):
    client = artifactregistry_v1.ArtifactRegistryAsyncClient()
    request = artifactregistry_v1.ListVersionsRequest(
        parent=package.name,
        page_size=1000,
    )
    versions = await client.list_versions(request=request, retry=ASYNC_RETRY)
    return versions


async def clean_up(args):
    logging.info("Pinging repository...")
    repository = await get_repository(args)
    logging.info(f"Found repository: {repository.name}")
    packages = await list_packages(repository)
    now = datetime.now(UTC)
    targets = defaultdict(set)
    async for package in packages:
        name = os.path.basename(package.name)
        if fnmatch(name, args.package):
            versions = await list_versions(package)
            async for version in versions:
                if now - version.create_time > timedelta(days=args.retention_days):
                    targets[package.name].add(version.name)
    logging.info(f"Found {len(targets)} packages matching {args.package}")
    for target in targets:
        logging.info(
            f"Found {len(targets[target])} expired versions of {os.path.basename(target)}"
        )

    if not target:
        logging.info("No expired packages, nothing to do!")
        exit(0)

    await batch_delete_versions(targets, args)


def main():
    parser = argparse.ArgumentParser(description="mozilla-linux-pkg-manager")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help='Sub-commands (currently only "clean-up" is supported)',
    )

    # Subparser for the 'clean-up' command
    clean_up_parser = subparsers.add_parser(
        "clean-up", help="Clean up package versions."
    )
    clean_up_parser.add_argument(
        "--package",
        type=str,
        help='The name of the packages to clean-up (ex. "firefox-nightly-*")',
        required=True,
    )
    clean_up_parser.add_argument(
        "--repository",
        type=str,
        help="",
        required=True,
    )
    clean_up_parser.add_argument(
        "--region",
        type=str,
        help="",
        required=True,
    )
    clean_up_parser.add_argument(
        "--retention-days",
        type=int,
        required=True,
        help="Retention period in days for the selected packages",
    )
    clean_up_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do a no-op run and print out a summary of the operations that will be executed",
        default=False,
    )

    args = parser.parse_args()
    logging.info(f"args:\n{pformat(vars(args))}")

    if args.command == "clean-up":
        if args.dry_run:
            logging.info("The dry-run mode is enabled. Doing a no-op run!")
        asyncio.run(clean_up(args))
        logging.info("Done cleaning up!")
