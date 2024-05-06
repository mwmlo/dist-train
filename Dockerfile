FROM python:3.8

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="~/.local/bin:$PATH" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /code

# Copy dependencies
COPY poetry.lock pyproject.toml /code/

# Project initialization
RUN poetry install

# Creating folders, and files for a project
COPY . /code