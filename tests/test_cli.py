from typer.testing import CliRunner

from scraper.cli import app


runner = CliRunner()


def test_cli_help_lists_command_groups() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "collect" in result.stdout
    assert "analyze" in result.stdout
