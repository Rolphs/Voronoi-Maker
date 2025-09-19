from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from typer.testing import CliRunner

from voronoimaker.cli import app
from voronoimaker.pipeline import run_pipeline


_FIXTURES = Path(__file__).parent / "fixtures"


def _load_mesh(path: Path) -> trimesh.Trimesh:
    return trimesh.load(path, file_type="stl", force="mesh")


def test_cli_surface_pipeline_writes_transformed_mesh(tmp_path: Path) -> None:
    runner = CliRunner()
    input_path = _FIXTURES / "triangle.stl"
    output_path = tmp_path / "surface_output.stl"

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
    )

    assert result.exit_code == 0, result.output
    assert output_path.exists()
    assert "Voronoi mesh saved" in result.stdout

    original_mesh = _load_mesh(input_path)
    processed_mesh = _load_mesh(output_path)
    expected_mesh = run_pipeline(
        mode="surface",
        mesh=_load_mesh(input_path),
        shell_thickness=1.5,
        density=0.3,
        relief_depth=0.2,
        seeds=[],
    )

    assert not np.allclose(original_mesh.vertices, processed_mesh.vertices)
    assert np.allclose(processed_mesh.vertices, expected_mesh.vertices)
    assert np.array_equal(processed_mesh.faces, expected_mesh.faces)


def test_cli_radial_pipeline_uses_dynamic_relief_default(tmp_path: Path) -> None:
    runner = CliRunner()
    input_path = _FIXTURES / "triangle.stl"
    output_path = tmp_path / "radial_output.stl"

    result = runner.invoke(
        app,
        [
            "--output",
            str(output_path),
            "--mode",
            "radial",
            "--shell-thickness",
            "2.0",
            "--density",
            "0.4",
            str(input_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_path.exists()
    assert "Voronoi mesh saved" in result.stdout

    original_mesh = _load_mesh(input_path)
    processed_mesh = _load_mesh(output_path)
    expected_mesh = run_pipeline(
        mode="radial",
        mesh=_load_mesh(input_path),
        shell_thickness=2.0,
        density=0.4,
        relief_depth=0.0,
        seeds=[],
    )

    assert not np.allclose(original_mesh.vertices, processed_mesh.vertices)
    assert np.allclose(processed_mesh.vertices, expected_mesh.vertices)
    assert np.array_equal(processed_mesh.faces, expected_mesh.faces)
