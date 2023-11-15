[![Task Status](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-deb-pkg-manager/main/badge.svg)](https://firefox-ci-tc.services.mozilla.com/api/github/v1/repository/mozilla-releng/mozilla-deb-pkg-manager/main/latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mozilla-releng/mozilla-deb-pkg-manager/main.svg)](https://results.pre-commit.ci/latest/github/mozilla-releng/mozilla-deb-pkg-manager/main)
[![Code Coverage](https://codecov.io/gh/mozilla-releng/mozilla-deb-pkg-manager/branch/main/graph/badge.svg?token=GJIV52ZQNP)](https://codecov.io/gh/mozilla-releng/mozilla-deb-pkg-manager)
[![Documentation Status](https://readthedocs.org/projects/mozilla-deb-pkg-manager/badge/?version=latest)](https://mozilla-deb-pkg-manager.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/license-MPL%202.0-orange.svg)](http://mozilla.org/MPL/2.0)

# mozilla-deb-pkg-manager

`mozilla-releng/mozilla-deb-pkg-manager` is a Python tool for managing Mozilla `.deb` packages. It can be used to clean-up obsolete Firefox Nightly versions from the Mozilla APT repository.

## Requirements
- Python > 3.11
- Poetry (for dependency management)

## Installation
1. **Install Poetry**: If not already installed, install Poetry following the instructions from the [official Poetry website](https://python-poetry.org/docs/).
2. **Clone the Repository**: Clone the `mozilla-deb-pkg-manager` repository.
3. **Install Dependencies**: Navigate to the repository's root directory and run `poetry install` to install the required dependencies.

### Running `mozilla-deb-pkg-manager`
Poetry can run the `mozilla-deb-pkg-manager` package like this:
```bash
poetry run mozilla-deb-pkg-manager clean-up --channel [CHANNEL] --retention-days [DAYS]
```

### Parameters
- `--channel`: Specifies the package channel (e.g., `nightly`, `release`, `beta`). Currently, only `nightly` is supported.
- `--retention-days`: Sets the retention period in days for packages in the nightly channel. This parameter is only supported on the `nightly` channel.

### Example
To clean up nightly packages that are older than 7 days:

```bash
poetry run mozilla-deb-pkg-manager clean-up --channel nightly --retention-days 7
```

## Building and Installing a Python Wheel

The `mozilla-deb-pkg-manager` package can be packaged into a wheel file, making it easy to distribute and install. Here's how to build the wheel file using Poetry and then install it using pip.

### Building the Wheel
To build a `.whl` file, you first need to use Poetry's build system. This process will package your application and its dependencies into a wheel file, which is a built distribution format for Python packages.

1. **Navigate to the Project Directory**: Open your terminal and navigate to the directory where your project is located.

2. **Build the Package**: Run the following command to build the wheel file:
    ```bash
    poetry build
    ```
    This command will create a `dist` folder in your project directory containing the wheel file (`.whl`).

### Installing the Wheel File
Once the wheel file is built, you can install it using pip. This makes your CLI tool available system-wide (or within your virtual environment if you have one activated).

1. **Navigate to the `dist` Directory**: Change to the `dist` directory where your `.whl` file is located.
    ```bash
    cd dist
    ```

2. **Install the Wheel File**: Use pip to install the wheel file. Assuming your wheel file is named `mozilla_deb_pkg_manager-0.1.0-py3-none-any.whl`, you would use the following command:
    ```bash
    pip install mozilla_deb_pkg_manager-0.1.0-py3-none-any.whl
    ```
    Replace `mozilla_deb_pkg_manager-0.1.0-py3-none-any.whl` with the actual name of your wheel file.

### Using the Installed Package
After installation, you can use the package from anywhere on your system, as long as you are running the Python interpreter where it was installed.

For example, to run the cleanup operation for nightly packages older than 5 days, execute:

```bash
mozilla-deb-pkg-manager clean-up --channel nightly --retention-days 5
```
