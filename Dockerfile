# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install Poetry
RUN apt-get update \
    && apt-get upgrade \
    && pip install poetry==1.5.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a new user and group (e.g., 'worker')
# and set the home directory for the user
RUN groupadd -r -g 15731 worker && useradd -r -u 15731 -g worker -d /home/worker -m worker

# Set the home directory as an environment variable
ENV HOME=/home/worker

# Set the working directory in the container
WORKDIR $HOME/app

# Copy the project files into the container
COPY . $HOME/app

# Change the ownership of the working directory to the new user
RUN chown -R worker:worker $HOME/app

# Switch to the non-root user
USER worker

# Install dependencies using Poetry
# The virtualenv will be created in the user's home directory
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --only main

# Run mozilla-linux-pkg-manager when the container launches
ENTRYPOINT ["poetry", "run", "mozilla-linux-pkg-manager"]
