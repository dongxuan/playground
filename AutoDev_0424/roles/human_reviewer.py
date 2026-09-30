import asyncio
from dataclasses import dataclass

from metagpt.roles import Role


@dataclass(frozen=True)
class HumanReview:
    approved: bool
    feedback: str = ""


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

    async def review(self, stage: str, artifact: str) -> HumanReview:
        if self.auto_approve:
            return HumanReview(True)
        while True:
            prompt = f"\n[Human Reviewer] {stage} 已产出 {artifact}。批准继续？[Y/n] "
            answer = (await asyncio.to_thread(input, prompt)).strip().lower()
            if answer in {"", "y", "yes"}:
                return HumanReview(True)
            if answer in {"n", "no"}:
                feedback = await asyncio.to_thread(input, "请输入修改意见（可留空，回车后重做当前步骤）：")
                return HumanReview(False, feedback.strip())
            print("请输入 y 或 n；也可按 Ctrl+C 终止。")
