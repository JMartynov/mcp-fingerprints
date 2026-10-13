import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from mcp_fingerprints.wizard import run_init_wizard


class TestWizard(unittest.TestCase):
    @patch("sys.stdin.isatty")
    @patch("sys.exit")
    @patch("sys.stderr.write")
    def test_non_tty_environment(self, mock_stderr_write, mock_exit, mock_isatty):
        mock_isatty.return_value = False

        run_init_wizard()

        mock_stderr_write.assert_called_with(
            "Interactive setup wizard requires a TTY. Aborting.\n"
        )
        mock_exit.assert_called_with(1)

    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input")
    @patch("builtins.print")
    def test_interactive_flow(self, mock_print, mock_input, mock_isatty):
        # Simulate user inputs: Yes for Claude and Cursor, No for Cline, Zed, Windsurf, Yes for semantic search.
        mock_input.side_effect = ["y", "y", "n", "n", "n", "y"]

        m = mock_open()
        with patch("builtins.open", m):
            run_init_wizard()

        m.assert_called_once_with(Path.home() / ".mcp_fingerprints.toml", "w")

        handle = m()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)

        self.assertIn("[mcp_fingerprints]", written_content)
        self.assertIn('clients = ["Claude", "Cursor"]', written_content)
        self.assertIn("semantic_search = true", written_content)

    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input")
    @patch("builtins.print")
    def test_interactive_flow_no_clients(self, mock_print, mock_input, mock_isatty):
        # Simulate user inputs: No to all clients, No to semantic search
        mock_input.side_effect = ["n", "n", "n", "n", "n", "n"]

        m = mock_open()
        with patch("builtins.open", m):
            run_init_wizard()

        handle = m()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)

        self.assertIn("[mcp_fingerprints]", written_content)
        self.assertIn("clients = []", written_content)
        self.assertIn("semantic_search = false", written_content)

    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input")
    @patch("sys.stderr.write")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_interactive_flow_write_error(
        self, mock_print, mock_exit, mock_stderr_write, mock_input, mock_isatty
    ):
        mock_input.side_effect = ["n", "n", "n", "n", "n", "n"]

        m = mock_open()
        m.side_effect = PermissionError("Permission denied")

        with patch("builtins.open", m):
            run_init_wizard()

        mock_stderr_write.assert_called_with(
            "\nFailed to write configuration: Permission denied\n"
        )
        mock_exit.assert_called_with(1)


if __name__ == "__main__":
    unittest.main()
