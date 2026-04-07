from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductSpec:
    requirement: str
    user_story: str
    acceptance_criteria: list[str]


@dataclass
class ArchitectureSpec:
    module_name: str
    function_name: str
    function_signature: str
    notes: list[str]


class ProductManagerAgent:
    role_name = "Product Manager"

    def analyze(self, requirement: str) -> ProductSpec:
        return ProductSpec(
            requirement=requirement,
            user_story=f"作为用户，我希望系统可以：{requirement}",
            acceptance_criteria=[
                "应提供清晰的函数接口",
                "应覆盖正向和边界场景测试",
                "实现代码必须通过自动化测试",
            ],
        )


class ArchitectAgent:
    role_name = "Architect"

    def design(self, product_spec: ProductSpec) -> ArchitectureSpec:
        req = product_spec.requirement.lower()
        if "加" in product_spec.requirement or "sum" in req or "add" in req:
            function_name = "add_numbers"
        else:
            function_name = "process_requirement"

        return ArchitectureSpec(
            module_name="tdd_target",
            function_name=function_name,
            function_signature=f"def {function_name}(a: int, b: int) -> int",
            notes=[
                "采用单一函数作为演示目标，便于 TDD 验证",
                "实现必须有类型注解和 docstring",
            ],
        )


class TesterAgent:
    role_name = "Tester"

    def generate_tests(self, architecture_spec: ArchitectureSpec) -> str:
        fn = architecture_spec.function_name
        return f'''import unittest

from src.{architecture_spec.module_name} import {fn}


class TestTddTarget(unittest.TestCase):
    def test_positive_numbers(self) -> None:
        self.assertEqual({fn}(1, 2), 3)

    def test_zero(self) -> None:
        self.assertEqual({fn}(0, 0), 0)

    def test_negative_numbers(self) -> None:
        self.assertEqual({fn}(-3, -2), -5)


if __name__ == "__main__":
    unittest.main()
'''


class DeveloperAgent:
    role_name = "Developer"

    def implement(self, architecture_spec: ArchitectureSpec) -> str:
        fn = architecture_spec.function_name
        return f'''def {fn}(a: int, b: int) -> int:
    """Return sum of two integers."""
    return a + b
'''
