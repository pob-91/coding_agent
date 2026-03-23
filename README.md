# Coding Agent

### Overview

This is an experiment in completely hands off coding.

- On the go.
- Write.
- Speak.
- Snap (coming soon).

### Getting Set Up

This coding agent is built around the following flow:

- Plan a feature with a chat app (currently Slack but could be another with some tweaking)
- Planning agent posts an issue on your git repo (currently Gitea but could become GitHub or GitLab e.t.c with some tweaking)
- User comments on the issue with one of the supported commands (see below)
- Coding agent picks up the issue and creates a PR
- User can comment on the PR with ask or update commands
- When the PR is completed to the user's satisfaction, merge it in and ahoy!

If you want to use this project as is then you need to:

- Host this agent on your infra somewhere, all you need is a public endpoint into the coding agent (e.g. AWS LoadBalancer or K8s ingress)
- Create a slack app and connect it to your workspace
- Register your slack app for the following event susbscriptions with the url `https://your-domain.com/slack/events`:
  - channel_id_changed
  - file_created
  - message.channels
- Register your repo (assuming Gitea) for the following webhooks with the url `https://your-domain.com/{SLACK_TEAM_ID}/gitea/events`:
  - Issue Comment
  - Pull Request Comment
  - Pull Request Reviewed

Then you should be good to go. Ensure you set the environment variables required below and set the auth header for Gitea (Slack has it's own OAuth flow that is handled once connected). The Gitea header is in the form `Bearer {token}` where token is set as an env var. 

> Other Inputs

The agent workflow is not currently set up to support input from any other sources but it would not take much to support WhatsApp, Text, Telegram e.t.c and also integrate with GitHub, GitLab e.t.c. If you would like this then raise an issue or even better, raise a PR!

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

### Modalities

This agent supports the following input modalities:

#### Text

Text messages are the primary input method. The agent processes text-based commands and questions through the various `/agent-*` commands documented above.

#### Audio

The agent can also process audio file attachments with the following constraints:

- **Single file limit**: Only 1 audio file can be processed at a time. If multiple files are attached, the agent will request that files be sent one at a time.
- **Allowed MIME types**: Currently only `mp3` or `wav` file types are supported.
  - `audio/mpeg` (MP3)
  - `audio/mp3` (MP3)
  - `audio/wav` (WAV)
- **Non-audio files**: Other file types (images, documents, etc.) are not currently supported.

Audio files are transcribed and processed as text input alongside any accompanying message text.

### Slack Integration

This coding agent integrates with Slack for notifications and interactions. Slack configuration is required for the application to function. See the "Environment Variables" section for configuration details.

### Database (CouchDB)

CouchDB is the required database for this application. The following environment variables must be configured: `DB_URL`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`. See the "Environment Variables" section for CouchDB configuration details.

### Configuring Git Webhooks

The Git webhook must include the Slack workspace ID in the path: `/{workspace_id}/gitea/events`.

For example, if your Slack workspace ID is `T123456`, the webhook URL becomes `https://your-domain.com/T123456/gitea/events`.

This is required for Slack integration to work properly.

### Environment Variables

| Name | Description | Is Required |
| :-- | :-- | :-- |
| `REPO_BASE_URL` | Base URL for the Git repository. Used to build clone URLs and repository API endpoints. | Yes |
| `AGENT_TOKEN` | Git authentication token used in clone URLs. | Yes |
| `AGENT_SECRET` | Bearer token used to authenticate incoming webhook requests. | Yes |
| `AGENT_USERNAME` | Git username used in clone URLs with `AGENT_TOKEN`. | Yes |
| `OPEN_ROUTER_API_KEY` | API key used to authenticate requests to OpenRouter for chat and transcription calls. | Yes |
| `AGENT_MODELS` | Comma-separated list of available agent/coding models. | No |
| `PLANNING_MODELS` | Comma-separated list of available planning models. | No |
| `AUDIO_MODELS` | Comma-separated list of available audio transcription models. | No |
| `DB_URL` | CouchDB host and port used to construct the database base URL. | Yes |
| `DB_USER` | CouchDB username used for database authentication. | Yes |
| `DB_PASSWORD` | CouchDB password used for database authentication. | Yes |
| `DB_NAME` | CouchDB database name used for storing workspace, channel, and message data. | Yes |
| `SLACK_SIGNING_SECRET` | Slack signing secret used to verify Slack event request signatures. | No |
| `SLACK_CLIENT_ID` | Slack OAuth client ID used during workspace installation. | No |
| `SLACK_CLIENT_SECRET` | Slack OAuth client secret used during workspace installation. | No |
| `ADMIN_SECRET` | Bearer token used to protect admin endpoints. | No |
| `COMPACT_ON_POST` | Enables automatic compaction after a successful post when set to `true`. | No |

Slack configuration is required: `SLACK_SIGNING_SECRET`, `SLACK_CLIENT_ID`, and `SLACK_CLIENT_SECRET` must be set for the application to function.

### Future Features

- If you want to naturally chat with the agent then `openai/gpt-audio` is the way forward. However, it is verrrryy expensive.
- Run tests function (will need a run_tests.sh file, or Makefile command) -> return is success or failure with a message
- Run linting function (will need a run_lint.sh file, or Makefile command) -> return is success or failure with a message
- Add guardrails in the form of another LLM that checks output and provides feedback before the patch is accepted
- Add benchmarks for code complexity, performance e.t.c and ask the model to optimise for it
