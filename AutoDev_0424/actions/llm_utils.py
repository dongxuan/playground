from metagpt.actions import Action


async def ask_nonempty(action: Action, prompt: str, attempts: int = 2) -> str:
    """Retry an occasional empty provider response; never accept an empty artifact."""
    for _ in range(attempts):
        response = await action._aask(prompt)
        if response.strip():
            return response
        prompt += "\n\n上一次响应为空。请务必按指定格式输出完整内容。"
    raise RuntimeError("LLM returned an empty response twice")
