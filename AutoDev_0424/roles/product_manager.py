from metagpt.roles import Role

from actions.write_prd import WritePRD


class ProductManager(Role):
    def __init__(self) -> None:
        super().__init__(
            name="PM",
            profile="Product Manager",
            goal="分析已有项目与新需求，并产出可验收的 PRD",
            actions=[WritePRD()],
        )
