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
- Consider performance Olog(n) is better than On. Make heavy use of sets and optimised algorithms.
- Leave comments only when needed (e.g. # using this function as as it is optimised over for...). Good code should not need comments by and large.

### Formatting

When writing code please consider formatting and readability. Examples are:

- Leave newlines between concepts - 20 lines of code all bunched together is not very readable. This includes Dockerfiles e.t.c.
- Early returns - in iterations perfer control flow statements like continue to make the code more readable
- Avoid nesting - use the "golden path" (early returns) to avoid nesting ifs e.t.c

### Agent Behaviour

You should assume that the target audience for ay code patch are experienced software egineers. Do not try to do anything superflous to requirements and keep contributions small, performant and clean.
