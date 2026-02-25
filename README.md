# Coding Agent

I need to lean into LLM agents coding for me or leave the industry.

If I don't enjoy this experience then I should quit tech.

### TODO

- Update Dockerfile to use SYSTEM_PYTHON and BYTEDCODE e.t.c. and then copy .venv over and see
- Tidy up a bit and isolate the tools to tools files e.t.c
- Fix the post a comment query - the request is failing - test using cURL
- Auto create an MR when it is complete
- Ask the agent to implement an ask the agent flow where we can do:
  - /agent-implement {command} - one shot implement the issue
  - /agent-ask {question} - in MRs, comments left with /agent-ask respond to the comment with details
  - /agent-update {command} - in MRs, comments left with /agent-update trigger a new flow that updates the existing MR

- Finally do an /agent-discuss flow where a chat in an app like Slack is passed to it along with the tools and project context. This agent can:
  - Discuss the project overall
  - Talk about architecture
  - Plan new features
  - Draft and add issues for the other agent to implement
