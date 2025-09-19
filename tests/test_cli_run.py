from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from voronoimaker.cli import app


_FIXTURES = Path(__file__).parent / "fixtures"
_PROG_NAME = "voronoimaker run"


def _copy_fixture(tmp_path: Path, filename: str = "triangle.stl") -> Path:
    destination = tmp_path / filename
    shutil.copy(_FIXTURES / filename, destination)
    return destination


def test_run_command_creates_output_file(tmp_path: Path) -> None:
    runner = CliRunner()
    input_path = _copy_fixture(tmp_path)
    output_path = tmp_path / "triangle_voronoi.stl"

    result = runner.invoke(
        app,
        [
            "--output",
            str(output_path),
            "--mode",
            "surface",
            "--shell-thickness",
            "1.5",
            "--density",
            "0.3",
            "--relief-depth",
            "0.2",
            str(input_path),
        ],
        prog_name=_PROG_NAME,
    )

    assert result.exit_code == 0, result.stderr or result.stdout
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert f"Voronoi mesh saved to {output_path}" in result.stdout


def test_run_command_reports_missing_input(tmp_path: Path) -> None:
    runner = CliRunner()
    missing_input = tmp_path / "missing.stl"

    result = runner.invoke(app, [str(missing_input)], prog_name=_PROG_NAME)

    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_run_command_rejects_invalid_seeds_json(tmp_path: Path) -> None:
    runner = CliRunner()
    input_path = _copy_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["--mode", "multicenter", "--seeds", "not json", str(input_path)],
        prog_name=_PROG_NAME,
    )

    assert result.exit_code == 2
    assert "valid JSON" in result.stderr


def test_run_command_rejects_density_out_of_range(tmp_path: Path) -> None:
    runner = CliRunner()
    input_path = _copy_fixture(tmp_path)

    result = runner.invoke(
        app,
        ["--density", "1.5", str(input_path)],
        prog_name=_PROG_NAME,
    )

    assert result.exit_code == 2
    assert "between 0 and 1" in result.stderr
