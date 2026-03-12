# Coding Agent

I need to lean into LLM agents coding for me or leave the industry.

If I don't enjoy this experience then I should quit tech.

### Commands

#### /agent-implement

The `/agent-implement` command triggers the coding agent to implement an issue. To use it, leave a comment on an issue with the following format:

```
/agent-implement please implement the above issue
```

The agent will:
- Checkout the issue repository
- Read information about the repository and the issue
- Gather context using tools about the files in the repository
- Generate a code patch that can be applied to the repository that addresses the issue

#### /agent-ask

The `/agent-ask` command triggers the agent to answer questions about the codebase. To use it, leave a comment on a PR (review comment or regular comment) with the following format:

```
/agent-ask what does the handle() method do in base_handler.py?
```

The agent will:
- Checkout the PR branch
- Read information about the repository structure and AGENTS.md if present
- Use tools to search files, list directories, and read file contents
- Respond with an answer to the question

This is useful for asking questions about code context during code review without needing to manually explore the repository.

#### /agent-update

The `/agent-update` command triggers the coding agent to make changes to an existing PR. To use it, leave a comment on a PR (review comment or regular comment) with the following format:

```
/agent-update fix the typo in the function name
```

The agent will:
- Checkout the PR branch
- Read information about the repository and the code context from the review comment
- Gather context using tools about the files in the repository
- Generate a code patch and commit it directly to the existing PR branch
- Comment on the PR with a summary of the changes

This is useful for requesting quick fixes or updates to a PR without creating a new branch.

### TODO

- Finally do an /agent-discuss flow where a chat in an app like Slack is passed to it along with the tools and project context. This agent can:
  - Discuss the project overall
  - Talk about architecture
  - Plan new features
  - Draft and add issues for the other agent to implement


### Future Features

- Run tests function (will need a run_tests.sh file, or Makefile command) -> return is success or failure with a message
- Run linting function (will need a run_lint.sh file, or Makefile command) -> return is success or failure with a message
- If performance is not 100% then try the planner/coder model where 1 model (maybe a thinking one) plans the approach to the solution and another model (a coding specific one) calls the replace, insert and delete functions
- Add guardrails in the form of another LLM that checks output and provides feedback before the patch is accepted
- Add benchmarks for code complexity, performance e.t.c and ask the model to optimise for it
