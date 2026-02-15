# Agents Guidelines For This Repository

### Overview Of The Project

This repository is the source code for a coding agent that responds to issues raised on 
git repositories (e.g. Github or Gitea).

It is a simple process that:

- Recieves webhooks for new comments on issues
- Checks out the issue repository
- Reads information about the repository and the issue
- Gathers context using tools about the files in the repository
- Generates a code patch that can be applied to the repository that addresses the issue

The purpose of this project is to create a coding helper that can aid an experienced programmer
compelete projects quicker.

### Architecture

- The project is written in python using `uv` and LTS python (the version is listed in pyproject.toml). 
- The entry point is `main.py`.
- It uses FastAPI to accept incoming webhook messages.
- The application is Dockerised so that it can be run in a virtual environment

### Coding Conventions

- Wherever possible prefer classes and typing to represent concepts and data in the application.
- Use Pydantic to parse and validate JSON with FastAPI.
- Simple is better than clever, for example, several lines of if statements are better than nested terneries.
- Follow the golden rule: negate ifs and return early where possible / use continue or break to keep nesting as low as possible.
- Prefer minimal and secure docker base images e.g. alpine or distroless.
