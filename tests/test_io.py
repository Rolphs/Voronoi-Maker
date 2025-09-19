from pathlib import Path

import pytest
import trimesh

from voronoimaker.io import load_stl


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_load_stl_success() -> None:
    mesh = load_stl(FIXTURE_DIR / "triangle.stl")

    assert isinstance(mesh, trimesh.Trimesh)
    assert not mesh.is_empty
    assert len(mesh.faces) == 1
    assert len(mesh.vertices) == 3


def test_load_stl_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.stl"

    with pytest.raises(FileNotFoundError) as exc_info:
        load_stl(missing)

    assert str(missing) in str(exc_info.value)


def test_load_stl_invalid_data(tmp_path: Path) -> None:
    broken = tmp_path / "broken.stl"
    broken.write_text("this is not a valid STL file", encoding="utf8")

    with pytest.raises(ValueError) as exc_info:
        load_stl(broken)

    assert str(broken) in str(exc_info.value)


def test_load_stl_unsupported_format(tmp_path: Path) -> None:
    other = tmp_path / "mesh.obj"
    other.write_text("o example", encoding="utf8")

    with pytest.raises(ValueError) as exc_info:
        load_stl(other)

    assert "Unsupported mesh format" in str(exc_info.value)
