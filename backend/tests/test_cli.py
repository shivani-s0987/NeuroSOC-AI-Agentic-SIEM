from typer.testing import CliRunner

from app.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "NeuroSOC 0.1.0" in result.stdout
