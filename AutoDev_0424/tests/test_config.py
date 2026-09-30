import inspect
import tempfile
import unittest
from pathlib import Path

from main import parse_args, resolve_max_fix_rounds
from team import AutoDevTeam


class ConfigTests(unittest.TestCase):
    def test_uses_configured_max_fix_rounds_when_cli_option_is_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("tdd:\n  max_fix_rounds: 5\n", encoding="utf-8")

            args = parse_args(["--config", str(config_path), "project", "requirement"])

            self.assertEqual(resolve_max_fix_rounds(args), 5)

    def test_cli_max_fix_rounds_overrides_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text("tdd:\n  max_fix_rounds: 5\n", encoding="utf-8")

            args = parse_args(
                [
                    "--config",
                    str(config_path),
                    "--max-fix-rounds",
                    "7",
                    "project",
                    "requirement",
                ]
            )

            self.assertEqual(resolve_max_fix_rounds(args), 7)

    def test_team_does_not_hide_a_hard_coded_fix_round_default(self) -> None:
        parameter = inspect.signature(AutoDevTeam.__init__).parameters["max_fix_rounds"]

        self.assertIs(parameter.default, inspect.Parameter.empty)


if __name__ == "__main__":
    unittest.main()
