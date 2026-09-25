from metagpt.actions import Action

from tools.project_utils import FileChange, parse_file_changes


async def ask_nonempty(action: Action, prompt: str, attempts: int = 2) -> str:
    """Retry an occasional empty provider response; never accept an empty artifact."""
    for _ in range(attempts):
        response = await action._aask(prompt)
        if response.strip():
            return response
        prompt += "\n\n上一次响应为空。请务必按指定格式输出完整内容。"
    raise RuntimeError("LLM returned an empty response twice")


async def ask_file_changes(action: Action, prompt: str, attempts: int = 2) -> list[FileChange]:
    """Ask for structured file changes and retry malformed JSON once."""
    last_error = "empty response"
    for _ in range(attempts):
        response = await action._aask(prompt)
        try:
            return parse_file_changes(response)
        except ValueError as error:
            last_error = str(error)
            prompt += f"\n\n上一次输出无法解析：{last_error}。请只返回合法 JSON，并包含完整 files 列表。"
    raise RuntimeError(f"LLM did not return valid file changes: {last_error}")
