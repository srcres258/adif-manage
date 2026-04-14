import os
import tempfile
import unittest

from src.adif_manage.cli import run_app, run_cli
from src.adif_manage.models import SessionState


class TestIntegrationCli(unittest.TestCase):
    def test_unknown_command_to_stderr(self) -> None:
        output: list[str] = []
        errors: list[str] = []
        inputs = iter(["bad\n", "quit-force\n"])

        exit_code = run_cli(
            state=SessionState(),
            stdin_readline=lambda: next(inputs),
            stdout_write=lambda s: output.append(s),
            stderr_write=lambda s: errors.append(s),
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("命令输入错误。用 help 命令查看所有命令", "".join(errors))

    def test_startup_missing_file_exit_one(self) -> None:
        code = run_app("/tmp/this-file-should-not-exist.adi")
        self.assertEqual(code, 1)

    def test_write_force_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "a", "b", "log.adi")
            state = SessionState()
            state.records = []
            output: list[str] = []
            errors: list[str] = []
            inputs = iter([f"write-force {target}\n", "quit-force\n"])

            code = run_cli(
                state=state,
                stdin_readline=lambda: next(inputs),
                stdout_write=lambda s: output.append(s),
                stderr_write=lambda s: errors.append(s),
            )

            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(target))
            self.assertIn("软件已递归自动创建目录", "".join(output))
            self.assertEqual("".join(errors), "")


if __name__ == "__main__":
    unittest.main()
