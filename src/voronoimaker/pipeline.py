"""Voronoi processing pipeline primitives."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Tuple

import numpy as np
import trimesh

from .io import load_stl

SeedPoint = Tuple[float, float, float]


class PipelineError(RuntimeError):
    """Raised when the Voronoi processing pipeline encounters an error."""


def load_mesh(path: Path) -> trimesh.Trimesh:
    """Load a mesh from ``path`` using the package's STL loader."""

    return load_stl(path)


def _copy_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Return a defensive copy of ``mesh``."""

    result = mesh.copy()
    if not isinstance(result, trimesh.Trimesh):  # pragma: no cover - defensive guard
        raise PipelineError("Failed to duplicate mesh for processing.")
    return result


def apply_surface_voronoi(
    mesh: trimesh.Trimesh,
    *,
    shell_thickness: float,
    density: float,
    relief_depth: float,
) -> trimesh.Trimesh:
    """Apply a lightweight surface Voronoi transformation."""

    result = _copy_mesh(mesh)

    scale_factor = 1.0 + max(density, 0.0) * 0.05 + max(shell_thickness, 0.0) * 0.01
    result.apply_scale(scale_factor)

    if relief_depth > 0:
        offset_vector = np.array([0.0, 0.0, relief_depth * 0.1])
        result.vertices = result.vertices + offset_vector

    result.metadata = {
        **getattr(mesh, "metadata", {}),
        "voronoi_mode": "surface",
        "voronoi_shell_thickness": shell_thickness,
        "voronoi_density": density,
        "voronoi_relief_depth": relief_depth,
    }
    return result


def apply_radial_voronoi(
    mesh: trimesh.Trimesh,
    *,
    shell_thickness: float,
    density: float,
    relief_depth: float,
) -> trimesh.Trimesh:
    """Apply a lightweight radial Voronoi transformation."""

    result = _copy_mesh(mesh)

    rotation_angle = max(density, 0.0) * (np.pi / 4.0) + relief_depth * 0.05
    axis = np.array([0.0, 0.0, 1.0])
    transform = trimesh.transformations.rotation_matrix(
        rotation_angle,
        axis,
        point=result.centroid,
    )
    result.apply_transform(transform)

    radial_scale = 1.0 + max(shell_thickness, 0.0) * 0.01
    result.apply_scale(radial_scale)

    result.metadata = {
        **getattr(mesh, "metadata", {}),
        "voronoi_mode": "radial",
        "voronoi_shell_thickness": shell_thickness,
        "voronoi_density": density,
        "voronoi_relief_depth": relief_depth,
    }
    return result


def apply_multicenter_voronoi(
    mesh: trimesh.Trimesh,
    *,
    shell_thickness: float,
    density: float,
    relief_depth: float,
    seeds: Sequence[SeedPoint],
) -> trimesh.Trimesh:
    """Apply a lightweight multi-centre Voronoi transformation."""

    if not seeds:
        raise PipelineError("multicenter mode requires at least one seed point.")

    result = _copy_mesh(mesh)

    seeds_array = np.asarray(seeds, dtype=float)
    centroid = seeds_array.mean(axis=0)
    offset = (centroid - result.centroid) * (max(density, 0.0) + relief_depth * 0.1)
    result.vertices = result.vertices + offset

    thickness_scale = 1.0 + max(shell_thickness, 0.0) * 0.005 * len(seeds)
    result.apply_scale(thickness_scale)

    result.metadata = {
        **getattr(mesh, "metadata", {}),
        "voronoi_mode": "multicenter",
        "voronoi_shell_thickness": shell_thickness,
        "voronoi_density": density,
        "voronoi_relief_depth": relief_depth,
        "voronoi_seed_count": len(seeds),
    }
    return result


def run_pipeline(
    *,
    mode: str,
    mesh: trimesh.Trimesh,
    shell_thickness: float,
    density: float,
    relief_depth: float,
    seeds: Iterable[SeedPoint],
) -> trimesh.Trimesh:
    """Execute the Voronoi pipeline for ``mesh`` using ``mode``."""

    mode_normalised = mode.lower()
    seeds_sequence = tuple(seeds)

    if mode_normalised == "surface":
        return apply_surface_voronoi(
            mesh,
            shell_thickness=shell_thickness,
            density=density,
            relief_depth=relief_depth,
        )

    if mode_normalised == "radial":
        return apply_radial_voronoi(
            mesh,
            shell_thickness=shell_thickness,
            density=density,
            relief_depth=relief_depth,
        )

    if mode_normalised == "multicenter":
        return apply_multicenter_voronoi(
            mesh,
            shell_thickness=shell_thickness,
            density=density,
            relief_depth=relief_depth,
            seeds=seeds_sequence,
        )

    raise PipelineError(f"Unsupported Voronoi mode: {mode}.")
