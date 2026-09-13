from metagpt.roles import Role

from actions.write_design import WriteDesign


class Architect(Role):
    def __init__(self) -> None:
        super().__init__(
            name="Architect",
            profile="Architect",
            goal="把 PRD 转换为简洁、可测试的技术设计",
            actions=[WriteDesign()],
        )
