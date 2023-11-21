[![Task Status](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-linux-pkg-manager/main/badge.svg)](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-linux-pkg-manager/main/latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mozilla-releng/mozilla-linux-pkg-manager/main.svg)](https://results.pre-commit.ci/latest/github/mozilla-releng/mozilla-linux-pkg-manager/main)
[![Code Coverage](https://codecov.io/gh/mozilla-releng/mozilla-linux-pkg-manager/branch/main/graph/badge.svg?token=GJIV52ZQNP)](https://codecov.io/gh/mozilla-releng/mozilla-linux-pkg-manager)
[![Documentation Status](https://readthedocs.org/projects/mozilla-linux-pkg-manager/badge/?version=latest)](https://mozilla-linux-pkg-manager.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/license-MPL%202.0-orange.svg)](http://mozilla.org/MPL/2.0)

# mozilla-linux-pkg-manager

`mozilla-releng/mozilla-linux-pkg-manager` is a Python tool for managing Mozilla product packages hosted in Linux software repositories on Google cloud.
It can be used to clean-up obsolete Firefox Nightly versions.

## Requirements
- Python 3.11 or higher
- Poetry (for dependency management)

## Development

### Installing `mozilla-linux-pkg-manager`
1. **Install Poetry**: If not already installed, install Poetry by following the instructions from the [official Poetry website](https://python-poetry.org/docs/).
2. **Clone the Repository**: Clone the `mozilla-linux-pkg-manager` repository using the command `git clone https://github.com/mozilla-releng/mozilla-linux-pkg-manager.git`.
3. **Install Dependencies**: Navigate to the repository's root directory and run `poetry install` to install the required dependencies.

### Setup Authentication
The easiest way to authenticate is using the Google Cloud SDK:

```bash
gcloud auth application-default login
```
Note that this command generates credentials for client libraries. To authenticate the CLI itself, use:

```bash
gcloud auth login
```

### Setup the Development Environment
To set up the environment for running `mozilla-linux-pkg-manager` set the following variables:

```bash
# defaults to /path/to/home/.config/gcloud/application_default_credentials.json
export GOOGLE_APPLICATION_CREDENTIALS=path/to/home/.config/gcloud/[FILENAME].json
export GOOGLE_CLOUD_PROJECT=[PROJECT_NAME]
```

### Running `mozilla-linux-pkg-manager`
To run `mozilla-linux-pkg-manager`, use Poetry with the following command:
```bash
poetry run mozilla-linux-pkg-manager clean-up [-h] --product PRODUCT --channel CHANNEL --format FORMAT --repository REPOSITORY --region REGION [--retention-days RETENTION_DAYS] [--dry-run]
```
#### Parameters
- `--product`: Specifies the Mozilla product to manage (e.g. `nightly`, `release`, `beta`). Currently, only `firefox` is supported.
- `--channel`: Specifies the package channel (e.g. `nightly`, `release`, `beta`). Currently, only `nightly` is supported.
- `--format`: The package format (i.e. deb). Currently, only `deb` is supported.
- `--retention-days`: Sets the retention period in days for packages in the nightly channel. This parameter is only supported on the `nightly` channel.
- `--dry-run`: Tells the script to do a no-op run and print out a summary of the operations that will be executed.
- `--repository`: The repository to perform maintenance operations on.
- `--region`: The cloud region the repository is hosted in.

#### Example
To clean up the nightly .deb packages that are older than 7 days:

```bash
poetry run mozilla-linux-pkg-manager clean-up --product firefox --channel nightly --format deb --retention-days 7 --repository mozilla --region us
```

## Building and Installing a Python Wheel

The `mozilla-linux-pkg-manager` package can be packaged into a wheel file for distribution and installation.

### Building the Wheel
1. **Navigate to the Project Directory**: Open your terminal and navigate to the directory where your project is located.
2. **Build the Package**: Execute `poetry build` to create the wheel file. This will generate a `dist` folder in your project directory containing the `.whl` file, whose name may vary based on the version and build.

### Installing the Wheel File
1. **Navigate to the `dist` Directory**: Move to the `dist` directory where the `.whl` file is located.
2. **Install the Wheel File**: Use `pip install [wheel-file-name]` to install the package. Replace `[wheel-file-name]` with the actual name of the wheel file generated during the build process.

### Using the Installed Package
After installation, the package can be used from anywhere on your system, provided you are running the Python interpreter where it was installed.

#### Example
To clean up nightly .deb packages that are older than 3 days:

```bash
mozilla-linux-pkg-manager clean-up --product firefox --channel nightly --format deb --retention-days 3 --repository mozilla --region us
```

## Docker

The `mozilla-linux-pkg-manager` can also be run as a Docker container. This section guides you through building a Docker image and running the container.

### Building the Docker Image

First, export the desired image name as an environment variable:

```bash
export IMAGE_NAME=mozilla-linux-pkg-manager
```

Then, build the Docker image:

```bash
docker build -t $IMAGE_NAME .
```

This command builds a Docker image with the tag specified in `$IMAGE_NAME`, based on the instructions in your Dockerfile.

### Running the Docker Container

To run the `mozilla-linux-pkg-manager` in a Docker container, you need to set the Google Application Credentials and mount them as a volume in the container. Replace `[FILE_NAME].json` with the name of your Google Application Credentials file and ensure the path to the credentials file is correctly set in the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/google/application/credentials/[FILE_NAME].json
docker run \
-e GOOGLE_CLOUD_PROJECT=[PROJECT_NAME] \
-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/[FILE_NAME].json \
-v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/keys/[FILE_NAME].json:ro \
$IMAGE_NAME \
--product firefox \
--channel nightly \
--format deb \
--retention-days 3 \
--repository mozilla \
--region us
```

In this command:
- The `-e` flag sets the `GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_CLOUD_PROJECT` environment variables inside the container.
- The `-v` flag mounts the credentials file from your host system to the container.
- The last line specifies the command and its arguments to be executed inside the container.
