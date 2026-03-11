from model.issue import Issue
from model.pull_review_comment import PullReviewComment
from model.repository import Repository
from utils.file import find_file, generate_top_level_file_tree
from utils.logger import get_logger

logger = get_logger(__name__)


def build_implement_user_prompt(
    repository: Repository,
    local_path: str,
    agent_command: str,
    issue: Issue | None = None,
    code_contexts: list[PullReviewComment] | None = None,
) -> str:
    with open("./agent_implement_user_prompt_template.txt", "r") as f:
        user_prompt = f.read()

    user_prompt = user_prompt.replace("{{repo_name}}", repository.name)

    file_tree = generate_top_level_file_tree(local_path)
    user_prompt = user_prompt.replace("{{file_tree}}", file_tree)

    agents_path = find_file(local_path, "AGENTS.md")
    if agents_path is not None:
        logger.info("Found AGENTS.md, adding to user prompt.")
        with open(agents_path, "r") as f:
            agents_content = f.read()
            user_prompt = user_prompt.replace("{{agents_md_content}}", agents_content)
    else:
        user_prompt = user_prompt.replace(
            "{{agents_md_content}}", "No AGENTS.md provided."
        )

    user_prompt = user_prompt.replace(
        "{{issue_title}}", f"Goal Title: {issue.title}" if issue is not None else ""
    )
    user_prompt = user_prompt.replace(
        "{{issue_body}}", f"Goal Info: {issue.body}" if issue is not None else ""
    )

    if code_contexts is not None:
        context_blocks = []
        for c in code_contexts:
            context_blocks.append(f"File: {c.path}\n```diff\n{c.diff_hunk}\n```")
        user_prompt = user_prompt.replace(
            "{{code_diffs}}",
            "\nCode context from source review comment:\n"
            + "\n\n".join(context_blocks),
        )
    else:
        user_prompt = user_prompt.replace("{{code_diffs}}", "")

    agent_command = agent_command.strip()
    user_prompt = user_prompt.replace("{{agent_command}}", agent_command)

    return user_prompt
