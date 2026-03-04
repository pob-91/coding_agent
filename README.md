# Coding Agent

I need to lean into LLM agents coding for me or leave the industry.

If I don't enjoy this experience then I should quit tech.

### TODO

- Wrap more of the functions in try catch so that agents cannot bork it up.
- Find the best agent to generate patch files and look for other methods as some of them seem to really struggle.
- Tidy up a bit and isolate the tools to tools files e.t.c
- Ask the agent to implement an ask the agent flow where we can do:
  - /agent-implement {command} - one shot implement the issue
  - /agent-ask {question} - in MRs, comments left with /agent-ask respond to the comment with details
  - /agent-update {command} - in MRs, comments left with /agent-update trigger a new flow that updates the existing MR

- Finally do an /agent-discuss flow where a chat in an app like Slack is passed to it along with the tools and project context. This agent can:
  - Discuss the project overall
  - Talk about architecture
  - Plan new features
  - Draft and add issues for the other agent to implement


### Future Features

- Run tests function (will need a run_tests.sh file, or Makefile command)
- Run linting function (will need a run_lint.sh file, or Makefile command)
- Add guardrails in the form of another LLM that checks output and provides feedback before the patch is accepted
- Add benchmarks for code complexity, performance e.t.c and ask the model to optimise for it
