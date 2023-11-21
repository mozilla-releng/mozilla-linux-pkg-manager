# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install Poetry
RUN apt-get update \
    && apt-get upgrade \
    && pip install poetry==1.5.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the project files into the container
COPY . .

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --only main

# Run mozilla-linux-pkg-manager when the container launches
ENTRYPOINT ["poetry", "run", "mozilla-linux-pkg-manager"]
