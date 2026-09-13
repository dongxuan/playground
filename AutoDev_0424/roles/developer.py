from metagpt.roles import Role

from actions.code_review import CodeReview
from actions.write_code import WriteCode


class Developer(Role):
    def __init__(self) -> None:
        super().__init__(
            name="Developer",
            profile="Developer",
            goal="实现最小代码并根据测试反馈修复",
            actions=[WriteCode(), CodeReview()],
        )
