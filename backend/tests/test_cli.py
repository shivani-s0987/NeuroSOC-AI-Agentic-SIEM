from typer.testing import CliRunner
from unittest.mock import Mock

from app import cli
from app.config import settings

from app.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "NeuroSOC 0.1.0" in result.stdout


def test_postgres_backup_resolves_absolute_pg_dump(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", "postgresql://user:pass@localhost/neurosoc")
    monkeypatch.setattr(settings, "backup_dir", tmp_path)
    monkeypatch.setattr("app.cli.shutil.which", lambda name: f"/usr/bin/{name}")
    completed = Mock(returncode=0, stderr="")
    run = Mock(return_value=completed)
    monkeypatch.setattr("app.cli.subprocess.run", run)

    destination = tmp_path / "verified.dump"
    destination.write_bytes(b"backup")

    cli.backup(str(destination))

    command = run.call_args.args[0]
    assert command[0] == "/usr/bin/pg_dump"
    assert command[-1] == settings.database_url
