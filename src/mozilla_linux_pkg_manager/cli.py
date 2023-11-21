import argparse
import asyncio
import logging
import os
import random
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime, timedelta
from itertools import islice
from pprint import pformat
from typing import (
    Any,
    Optional,
    Union,
)
from urllib.parse import urljoin

import aiohttp
import yaml
from google.cloud import artifactregistry_v1
from mozilla_version.gecko import GeckoVersion

logging.basicConfig(
    format="%(asctime)s - mozilla-linux-pkg-manager - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def calculate_sleep_time(
    attempt, delay_factor=5.0, randomization_factor=0.5, max_delay=120
):
    """Calculate the sleep time between retries, in seconds.

    Based off of `taskcluster.utils.calculateSleepTime`, but with kwargs instead
    of constant `delay_factor`/`randomization_factor`/`max_delay`.  The taskcluster
    function generally slept for less than a second, which didn't always get
    past server issues.
    Args:
        attempt (int): the retry attempt number
        delay_factor (float, optional): a multiplier for the delay time.  Defaults to 5.
        randomization_factor (float, optional): a randomization multiplier for the
            delay time.  Defaults to .5.
        max_delay (float, optional): the max delay to sleep.  Defaults to 120 (seconds).
    Returns:
        float: the time to sleep, in seconds.
    """
    if attempt <= 0:
        return 0

    # We subtract one to get exponents: 1, 2, 3, 4, 5, ..
    delay = float(2 ** (attempt - 1)) * float(delay_factor)
    # Apply randomization factor.  Only increase the delay here.
    delay = delay * (randomization_factor * random.random() + 1)
    # Always limit with a maximum delay
    return min(delay, max_delay)


async def retry_async(
    func: Callable[..., Awaitable[Any]],
    attempts: int = 5,
    sleeptime_callback: Callable[..., Any] = calculate_sleep_time,
    retry_exceptions: Union[
        type[BaseException], tuple[type[BaseException], ...]
    ] = Exception,
    args: Sequence[Any] = (),
    kwargs: Optional[dict[str, Any]] = None,
    sleeptime_kwargs: Optional[dict[str, Any]] = None,
) -> Any:
    """Retry ``func``, where ``func`` is an awaitable.

    Args:
        func (function): an awaitable function.
        attempts (int, optional): the number of attempts to make.  Default is 5.
        sleeptime_callback (function, optional): the function to use to determine
            how long to sleep after each attempt.  Defaults to ``calculateSleepTime``.
        retry_exceptions (list or exception, optional): the exception(s) to retry on.
            Defaults to ``Exception``.
        args (list, optional): the args to pass to ``func``.  Defaults to ()
        kwargs (dict, optional): the kwargs to pass to ``func``.  Defaults to
            {}.
        sleeptime_kwargs (dict, optional): the kwargs to pass to ``sleeptime_callback``.
            If None, use {}.  Defaults to None.
    Returns:
        object: the value from a successful ``function`` call
    Raises:
        Exception: the exception from a failed ``function`` call, either outside
            of the retry_exceptions, or one of those if we pass the max
            ``attempts``.
    """
    kwargs = kwargs or {}
    attempt = 1
    while True:
        try:
            return await func(*args, **kwargs)
        except retry_exceptions:
            attempt += 1
            check_number_of_attempts(attempt, attempts, func, "retry_async")
            await asyncio.sleep(
                define_sleep_time(
                    sleeptime_kwargs, sleeptime_callback, attempt, func, "retry_async"
                )
            )


def check_number_of_attempts(
    attempt: int, attempts: int, func: Callable[..., Any], retry_function_name: str
) -> None:
    if attempt > attempts:
        logging.warning(f"{retry_function_name}: {func.__name__}: too many retries!")
        raise


def define_sleep_time(
    sleeptime_kwargs: Optional[dict[str, Any]],
    sleeptime_callback: Callable[..., int],
    attempt: int,
    func: Callable[..., Any],
    retry_function_name: str,
) -> float:
    sleeptime_kwargs = sleeptime_kwargs or {}
    sleep_time = sleeptime_callback(attempt, **sleeptime_kwargs)
    logging.debug(
        "{}: {}: sleeping {} seconds before retry".format(
            retry_function_name, func.__name__, sleep_time
        )
    )
    return sleep_time


async def batch_delete_versions(versions, dry_run):
    client = artifactregistry_v1.ArtifactRegistryAsyncClient()
    request = artifactregistry_v1.BatchDeleteVersionsRequest(
        names=versions,
    )
    display_versions = [
        await retry_async(
            client.get_version,
            kwargs={"request": artifactregistry_v1.GetVersionRequest(name=version)},
        )
        for version in random.sample(versions, 3)
    ]
    if not dry_run:
        logging.info(
            f"Deleting {format(len(versions), ',')} expired package versions similar to:\n{str(display_versions)}"
        )
        operation = client.batch_delete_versions(request=request)
        result = (await operation).result()
        logging.info(f"result: {str(result)}")
    logging.info(
        f"batch_delete_versions is a no-op in dry-run mode!\nDeleting {format(len(versions), ',')} expired package versions similar to:\n{str(display_versions)}"
    )


async def get_repository(args):
    client = artifactregistry_v1.ArtifactRegistryAsyncClient()
    parent = f"projects/{os.environ['GOOGLE_CLOUD_PROJECT']}/locations/{args.region}/repositories/{args.repository}"
    get_repository_request = artifactregistry_v1.GetRepositoryRequest(
        name=parent,
    )
    repository = await client.get_repository(request=get_repository_request)
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


async def fetch_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch data: HTTP Status {response.status}")

            content = await response.text()
            return content


def parse_key_value_block(block):
    package = {}
    for line in block.split("\n"):
        if line:
            key, value = line.split(": ", 1)
            package[key.strip()] = value.strip()
            if key == "Version":
                version, postfix = value.split("~")
                package["Gecko-Version"] = GeckoVersion.parse(version)
                if package["Gecko-Version"].is_nightly:
                    package["Build-ID"] = postfix
                    package["Moz-Build-Date"] = datetime.strptime(
                        package["Build-ID"], "%Y%m%d%H%M%S"
                    )
                else:
                    package["Build-Number"] = postfix[len("build") :]
    return package


async def delete_nightly_versions(args):
    url = f"https://{args.region}-apt.pkg.dev/projects/{os.environ['GOOGLE_CLOUD_PROJECT']}/dists/{args.repository}"
    normalized_url = f"{url}/" if not url.endswith("/") else url
    release_url = urljoin(normalized_url, "Release")
    try:
        logging.info(f"Fetching raw_release_data at {url}")
        raw_release_data = await retry_async(
            fetch_url,
            args=[release_url],
            attempts=3,
        )
        parsed_release_data = yaml.safe_load(raw_release_data)
        logging.info(f"parsed_release_data:\n{pformat(parsed_release_data)}")
        architectures = parsed_release_data["Architectures"].split()
        package_data_promises = []
        for architecture in architectures:
            pkg_url = f"{normalized_url}main/binary-{architecture}/Packages"
            package_data_promises.append(
                retry_async(
                    fetch_url,
                    args=[pkg_url],
                    attempts=3,
                )
            )
        package_data_results = await asyncio.gather(*package_data_promises)
        package_data = []
        for architecture, package_data_result in zip(
            architectures, package_data_results
        ):
            parsed_package_data = [
                parse_key_value_block(raw_package_data)
                for raw_package_data in package_data_result.split("\n\n")
            ]
            package_data.extend(parsed_package_data)
        nightly_package_data = [
            package for package in package_data if package["Gecko-Version"].is_nightly
        ]
        now = datetime.now()
        expired_nightly_packages = [
            package
            for package in nightly_package_data
            if now - package["Moz-Build-Date"] > timedelta(days=args.retention_days)
        ]
        logging.info(
            f"Found {format(len(expired_nightly_packages), ',')} expired nightly packages. Keeping {format(len(nightly_package_data) - len(expired_nightly_packages), ',')} nightly packages created < {args.retention_days} days ago"
        )
        targets = [
            f"projects/{os.environ['GOOGLE_CLOUD_PROJECT']}/locations/{args.region}/repositories/{args.repository}/packages/{package['Package']}/versions/{package['Version']}"
            for package in expired_nightly_packages
        ]
        repository = await get_repository(args)
        logging.info(f"repository:\n{str(repository)}")
        batches = batched(targets, 10000)
        for batch in batches:
            await batch_delete_versions(batch, args.dry_run)
    except Exception as e:
        logging.error(f"An error occurred: {e}")


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
        "--product",
        type=str,
        help="Product in the packages (i.e. firefox)",
        required=True,
    )
    clean_up_parser.add_argument(
        "--channel",
        type=str,
        help="Channel of the packages (e.g. nightly, release, beta)",
        required=True,
    )
    clean_up_parser.add_argument(
        "--format",
        type=str,
        help="The package format (i.e. deb)",
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
        help="Retention period in days for packages in the nightly channel",
    )
    clean_up_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do a no-op run and print out a summary of the operations that will be executed",
        default=False,
    )

    args = parser.parse_args()

    if args.dry_run:
        logging.info("The dry-run mode is enabled. Doing a no-op run!")

    logging.info(f"args:\n{pformat(vars(args))}")

    if args.command == "clean-up":
        if args.product != "firefox":
            raise ValueError("firefox is the only supported product")
        if args.format != "deb":
            raise ValueError("deb is the only supported format")
        if args.channel == "nightly":
            if args.retention_days is None:
                raise ValueError(
                    "Retention days must be specified for the nightly channel"
                )
            asyncio.run(delete_nightly_versions(args))
            logging.info("Done cleaning up")
        else:
            raise ValueError("Only the nightly channel is supported")
