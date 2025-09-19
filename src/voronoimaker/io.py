"""Input/output helpers for Voronoi Maker."""

from __future__ import annotations

from pathlib import Path

import trimesh


def load_stl(path: Path) -> trimesh.Trimesh:
    """Load an STL mesh from ``path``.

    Args:
        path: Location of the STL file on disk.

    Returns:
        A :class:`trimesh.Trimesh` instance containing the parsed mesh.

    Raises:
        FileNotFoundError: If ``path`` does not exist or is not a file.
        ValueError: If the path is not an STL file or could not be parsed.
    """

    file_path = Path(path)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"STL file not found: {file_path}")

    if file_path.suffix.lower() != ".stl":
        raise ValueError(
            f"Unsupported mesh format for '{file_path.name}'. Expected an STL file."
        )

    try:
        mesh = trimesh.load(file_path, file_type="stl", force="mesh")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"STL file not found: {file_path}") from exc
    except ValueError as exc:
        raise ValueError(f"Failed to parse STL file '{file_path}': {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive guard for trimesh loaders
        raise ValueError(f"Failed to parse STL file '{file_path}': {exc}") from exc

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(
            f"Failed to load STL file '{file_path}': unsupported mesh contents."
        )

    if mesh.is_empty:
        raise ValueError(f"STL file '{file_path}' does not contain any geometry.")

    return mesh
