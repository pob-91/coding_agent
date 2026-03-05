# Coding Agent

I need to lean into LLM agents coding for me or leave the industry.

If I don't enjoy this experience then I should quit tech.

### TODO

- TEST TOOL!
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

- Run tests function (will need a run_tests.sh file, or Makefile command) -> return is success or failure with a message
- Run linting function (will need a run_lint.sh file, or Makefile command) -> return is success or failure with a message
- If performance is not 100% then try the planner/coder model where 1 model (maybe a thinking one) plans the approach to the solution and another model (a coding specific one) calls the replace, insert and delete functions
- Add guardrails in the form of another LLM that checks output and provides feedback before the patch is accepted
- Add benchmarks for code complexity, performance e.t.c and ask the model to optimise for it
