[![Task Status](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-linux-pkg-manager/main/badge.svg)](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-linux-pkg-manager/main/latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mozilla-releng/mozilla-linux-pkg-manager/main.svg)](https://results.pre-commit.ci/latest/github/mozilla-releng/mozilla-linux-pkg-manager/main)
[![Code Coverage](https://codecov.io/gh/mozilla-releng/mozilla-linux-pkg-manager/branch/main/graph/badge.svg?token=GJIV52ZQNP)](https://codecov.io/gh/mozilla-releng/mozilla-linux-pkg-manager)

# mozilla-linux-pkg-manager

`mozilla-releng/mozilla-linux-pkg-manager` is a Python tool for managing packages stored in Linux software repositories hosted on Google Cloud Platform.

## Requirements
- Python 3.11 or higher
- uv (for dependency management)

## Development

### Installing `mozilla-linux-pkg-manager`
1. **Install uv**: If not already installed, install uv by following the instructions from the [official uv website](https://docs.astral.sh/uv/).
2. **Clone the Repository**: Clone the `mozilla-linux-pkg-manager` repository using the command `git clone https://github.com/mozilla-releng/mozilla-linux-pkg-manager.git`.
3. **Install Dependencies**: Navigate to the repository's root directory and run `uv sync` to install the required dependencies.

### Setup Authentication
The easiest way to authenticate is using the Google Cloud SDK:

```bash
gcloud auth application-default login
```
Note that this command generates credentials for the Google Cloud Platform client libraries.

### Setup the Development Environment
To set up the environment for running `mozilla-linux-pkg-manager` set the following variables:

```bash
# defaults to /path/to/home/.config/gcloud/application_default_credentials.json
export GOOGLE_APPLICATION_CREDENTIALS=[/path/to/google/application/credentials/file.json]
export GOOGLE_CLOUD_PROJECT=[PROJECT_NAME]
```

### Running `mozilla-linux-pkg-manager`
To run `mozilla-linux-pkg-manager`, use uv with the following command:
```bash
uv run mozilla-linux-pkg-manager clean-up [-h] --package PACKAGE --repository REPOSITORY [REPOSITORY ...] --region REGION --retention-days RETENTION_DAYS [--dry-run]
```

#### Parameters
- `--package`: A regular expression matching the name of the packages to clean-up.
- `--retention-days`: Sets the retention period in days for packages that match the `package` regex.
- `--dry-run`: Tells the script to do a no-op run and print out a summary of the operations that will be executed.
- `--repository`: One or more repositories to perform maintenance operations on.
- `--region`: The cloud region the repository is hosted in.

#### Examples
Clean up firefox and firefox l10n packages that are older than 365 days:
```bash
mozilla-linux-pkg-manager \
clean-up \
--package "^firefox(-l10n-.+)?$" \
--retention-days 365 \
--repository mozilla \
--region us
```

Clean up firefox-nightly and firefox-nightly l10n packages that are older than a day:
```bash
mozilla-linux-pkg-manager \
clean-up \
--package "^firefox-nightly(-l10n-.+)?$" \
--retention-days 1 \
--repository mozilla \
--region us
```

Clean up firefox-devedition and firefox-devedition l10n packages that are older than 60 days:
```bash
mozilla-linux-pkg-manager \
clean-up \
--package "^firefox-(devedition|beta)(-l10n-.+)?$" \
--retention-days 60 \
--repository mozilla \
--region us
```

## Docker

The `mozilla-linux-pkg-manager` tool can also be run as a Docker container using the [mozillareleases/mozilla-linux-pkg-manager](https://hub.docker.com/r/mozillareleases/mozilla-linux-pkg-manager/tags) image.

```bash
export GOOGLE_CLOUD_PROJECT=[GOOGLE_CLOUD_PROJECT]
export GOOGLE_APPLICATION_CREDENTIALS=[/path/to/google/application/credentials/file.json]
docker run --rm \
-e GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT \
-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/google/key.json \
-v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/keys/google/key.json:ro \
mozillareleases/mozilla-linux-pkg-manager:0.7.0 \
clean-up \
--package "^firefox(-l10n-.+)?$" \
--retention-days 3 \
--repository [REPOSITORY] \
--region [REGION] \
--dry-run
```

### Building the Docker Image

You can build the Docker image locally with:

```bash
taskgraph build-image pkg-manager
```

This command builds a Docker image with the tag `pkg-manager:latest`.

### Running the Docker Container

To run the `mozilla-linux-pkg-manager` in a Docker container, you need to set the Google Application Credentials and mount them as a volume in the container. Replace `[FILE_NAME].json` with the name of your Google Application Credentials file and ensure the path to the credentials file is correctly set in the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

```bash
# defaults to /path/to/home/.config/gcloud/application_default_credentials.json
export GOOGLE_APPLICATION_CREDENTIALS=[/path/to/google/application/credentials/file.json]
export GOOGLE_CLOUD_PROJECT=[PROJECT_NAME]

docker run \
-e GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT \
-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/google/key.json \
-v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/keys/google/key.json:ro \
$IMAGE_NAME \
clean-up \
--package "^firefox(-l10n-.+)?$" \
--retention-days 3 \
--repository mozilla \
--region us \
--dry-run
```

In this command:
- The `-e` flag sets the `GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_CLOUD_PROJECT` environment variables inside the container.
- The `-v` flag mounts the credentials file from your host system to the container.
- The last line specifies the command and its arguments to be executed inside the container.

## Building and Installing a Python Wheel

The `mozilla-linux-pkg-manager` package can be packaged into a wheel file for distribution and installation.

### Building the Wheel
1. **Navigate to the Project Directory**: Open your terminal and navigate to the directory where your project is located.
2. **Build the Package**: Execute `uv tool run hatch build` to create the wheel file. This will generate a `dist` folder in your project directory containing the `.whl` file, whose name may vary based on the version and build.

### Installing the Wheel File
1. **Navigate to the `dist` Directory**: Move to the `dist` directory where the `.whl` file is located.
2. **Install the Wheel File**: Use `pip install [wheel-file-name]` to install the package. Replace `[wheel-file-name]` with the actual name of the wheel file generated during the build process.

### Using the Installed Package
After installation, the package can be used from anywhere on your system, provided you are running the Python interpreter where it was installed.

# Publish a new docker image

After bumping the version and tagging it, find the `docker-image-pkg-manager` task for that commit, note it down as `TASK_ID`.
You can then do:

```
taskgraph load-image --task-id=<TASK_ID> -t mozillareleases/mozilla-linux-pkg-manager:<VERSION>
docker push mozillareleases/mozilla-linux-pkg-manager:<VERSION>
```
