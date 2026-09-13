import asyncio

from metagpt.roles import Role


class HumanReviewer(Role):
    auto_approve: bool = False

    def __init__(self, auto_approve: bool = False) -> None:
        super().__init__(
            name="Reviewer",
            profile="Human Reviewer",
            goal="在每个 AI 阶段后审阅产出",
            is_human=True,
            auto_approve=auto_approve,
        )

    async def review(self, stage: str, artifact: str) -> bool:
        if self.auto_approve:
            return True
        prompt = f"\n[Human Reviewer] {stage} 已产出 {artifact}。批准继续？[Y/n] "
        answer = await asyncio.to_thread(input, prompt)
        return answer.strip().lower() in {"", "y", "yes"}
