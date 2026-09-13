from metagpt.roles import Role

from actions.write_test import WriteTest


class QAEngineer(Role):
    def __init__(self) -> None:
        super().__init__(
            name="QA",
            profile="QA Engineer",
            goal="遵循 TDD，先通过公开接口定义验收测试",
            actions=[WriteTest()],
        )
