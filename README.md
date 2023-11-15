[![Task Status](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-deb-pkg-manager/main/badge.svg)](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-deb-pkg-manager/main/latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mozilla-releng/mozilla-deb-pkg-manager/main.svg)](https://results.pre-commit.ci/latest/github/mozilla-releng/mozilla-deb-pkg-manager/main)
[![Code Coverage](https://codecov.io/gh/mozilla-releng/mozilla-deb-pkg-manager/branch/main/graph/badge.svg?token=GJIV52ZQNP)](https://codecov.io/gh/mozilla-releng/mozilla-deb-pkg-manager)
[![Documentation Status](https://readthedocs.org/projects/mozilla-deb-pkg-manager/badge/?version=latest)](https://mozilla-deb-pkg-manager.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/license-MPL%202.0-orange.svg)](http://mozilla.org/MPL/2.0)

# mozilla-deb-pkg-manager

`mozilla-releng/mozilla-deb-pkg-manager` is a Python tool for managing Mozilla `.deb` packages. It can be used to clean-up obsolete Firefox Nightly versions from the Mozilla APT repository.

## Requirements
- Python 3.11 or higher
- Poetry (for dependency management)

## Installation
1. **Install Poetry**: If not already installed, install Poetry by following the instructions from the [official Poetry website](https://python-poetry.org/docs/).
2. **Clone the Repository**: Clone the `mozilla-deb-pkg-manager` repository using the command `git clone https://github.com/mozilla-releng/mozilla-deb-pkg-manager.git`.
3. **Install Dependencies**: Navigate to the repository's root directory and run `poetry install` to install the required dependencies.

### Running `mozilla-deb-pkg-manager`
To run `mozilla-deb-pkg-manager`, use Poetry with the following command:
```bash
poetry run mozilla-deb-pkg-manager clean-up --channel [CHANNEL] --retention-days [DAYS]
```
Replace `[CHANNEL]` with the specific package channel (e.g., `nightly`, `release`, `beta`) and `[DAYS]` with the number of days for the retention period.

### Parameters
- `--channel`: Specifies the package channel (e.g., `nightly`, `release`, `beta`). Currently, only `nightly` is supported.
- `--retention-days`: Sets the retention period in days for packages in the nightly channel. This parameter is only supported on the `nightly` channel.

### Example
To clean up nightly packages that are older than 7 days:

```bash
poetry run mozilla-deb-pkg-manager clean-up --channel nightly --retention-days 7
```

## Building and Installing a Python Wheel

The `mozilla-deb-pkg-manager` package can be packaged into a wheel file for distribution and installation.

### Building the Wheel
1. **Navigate to the Project Directory**: Open your terminal and navigate to the directory where your project is located.
2. **Build the Package**: Execute `poetry build` to create the wheel file. This will generate a `dist` folder in your project directory containing the `.whl` file, whose name may vary based on the version and build.

### Installing the Wheel File
1. **Navigate to the `dist` Directory**: Move to the `dist` directory where the `.whl` file is located.
2. **Install the Wheel File**: Use `pip install [wheel-file-name]` to install the package. Replace `[wheel-file-name]` with the actual name of the wheel file generated during the build process.

### Using the Installed Package
After installation, the package can be used from anywhere on your system, provided you are running the Python interpreter where it was installed. For example:

```bash
mozilla-deb-pkg-manager clean-up --channel nightly --retention-days 5
```
