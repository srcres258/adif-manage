import unittest

from src.adif_manage.commands import parse_command_line, parse_delete_target
from src.adif_manage.errors import CommandError


class TestCommandParsing(unittest.TestCase):
    def test_parse_path_with_spaces(self) -> None:
        command = parse_command_line("read /tmp/a b c.adi")
        self.assertEqual(command.name, "read")
        self.assertEqual(command.argument, "/tmp/a b c.adi")

    def test_unknown_command(self) -> None:
        with self.assertRaises(CommandError):
            parse_command_line("unknown")

    def test_delete_single(self) -> None:
        target = parse_delete_target("3", 10)
        self.assertEqual(target.start, 3)
        self.assertEqual(target.end, 3)

    def test_delete_range(self) -> None:
        target = parse_delete_target("2-5", 10)
        self.assertEqual(target.start, 2)
        self.assertEqual(target.end, 5)

    def test_delete_invalid_range(self) -> None:
        with self.assertRaises(CommandError):
            parse_delete_target("9-12", 10)


if __name__ == "__main__":
    unittest.main()
