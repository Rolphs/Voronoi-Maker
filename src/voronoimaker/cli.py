"""Command line interface for the Voronoi Maker package."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence

import typer

from .io import load_stl
from .pipeline import PipelineError, run_pipeline


class Mode(str, Enum):
    """Supported processing modes for Voronoi generation."""

    SURFACE = "surface"
    RADIAL = "radial"
    MULTICENTER = "multicenter"


app = typer.Typer(help="Generate Voronoi patterns for 3D models.")


SeedPoint = tuple[float, float, float]


def _parse_seeds(raw_seeds: Optional[str]) -> list[SeedPoint]:
    """Parse the ``--seeds`` option into a list of centroid coordinates."""

    if raw_seeds is None or raw_seeds.strip() == "":
        return []

    try:
        decoded = json.loads(raw_seeds)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise typer.BadParameter("seeds must be valid JSON.", param_hint="seeds") from exc

    if not isinstance(decoded, list):
        raise typer.BadParameter(
            "seeds must be a JSON array of coordinate triples.",
            param_hint="seeds",
        )

    parsed: list[SeedPoint] = []
    for index, entry in enumerate(decoded):
        if not isinstance(entry, (list, tuple)):
            raise typer.BadParameter(
                f"seeds[{index}] must be a list of three numeric coordinates.",
                param_hint="seeds",
            )

        if len(entry) != 3:
            raise typer.BadParameter(
                f"seeds[{index}] must contain exactly three coordinates.",
                param_hint="seeds",
            )

        if not all(isinstance(coord, (int, float)) for coord in entry):
            raise typer.BadParameter(
                f"seeds[{index}] must contain only numbers.",
                param_hint="seeds",
            )

        parsed.append(tuple(float(coord) for coord in entry))

    return parsed


def _default_output_path(input_path: Path) -> Path:
    """Return a sensible default output path based on ``input_path``."""

    suffix = input_path.suffix or ".stl"
    return input_path.with_name(f"{input_path.stem}_voronoi{suffix}")


def _ensure_positive(name: str, value: float) -> None:
    """Ensure ``value`` is strictly positive."""

    if value <= 0:
        raise typer.BadParameter(f"{name} must be greater than zero.", param_hint=name)


def _ensure_non_negative(name: str, value: float) -> None:
    """Ensure ``value`` is zero or positive."""

    if value < 0:
        raise typer.BadParameter(f"{name} must be zero or greater.", param_hint=name)


def _ensure_at_most(name: str, value: float, maximum: float, *, message: str | None = None) -> None:
    """Ensure ``value`` does not exceed ``maximum``."""

    if value > maximum:
        error_message = message or f"{name} must be {maximum} or less."
        raise typer.BadParameter(error_message, param_hint=name)


def _validate_parameters(
    mode: Mode,
    shell_thickness: float,
    density: float,
    relief_depth: float,
    seeds: Sequence[SeedPoint],
) -> None:
    """Perform lightweight validation for CLI parameters.

    This keeps the CLI usable before the full Voronoi pipeline is implemented.
    """

    _ensure_positive("shell_thickness", shell_thickness)
    _ensure_non_negative("density", density)
    _ensure_at_most(
        "density",
        density,
        1.0,
        message="density must be between 0 and 1 (inclusive).",
    )
    _ensure_non_negative("relief_depth", relief_depth)
    if mode is not Mode.MULTICENTER and seeds:
        raise typer.BadParameter(
            "seeds can only be provided when using multicenter mode.",
            param_hint="seeds",
        )

    if mode is Mode.MULTICENTER and not seeds:
        raise typer.BadParameter(
            "seeds must provide at least one centroid when using multicenter mode.",
            param_hint="seeds",
        )

    if mode is Mode.SURFACE and relief_depth == 0:
        raise typer.BadParameter(
            "relief_depth must be greater than zero when using surface mode.",
            param_hint="relief_depth",
        )
    # Additional domain-specific validation rules can be added as the
    # geometric processing implementation evolves.


@app.command()
def run(
    input: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        resolve_path=True,
        help="Path to the source mesh file (e.g. STL).",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        resolve_path=True,
        help="Destination for the generated Voronoi mesh.",
    ),
    mode: Mode = typer.Option(
        Mode.SURFACE,
        "--mode",
        "-m",
        case_sensitive=False,
        help="Processing mode to use for Voronoi generation (surface, radial, or multicenter).",
    ),
    shell_thickness: float = typer.Option(
        2.0,
        "--shell-thickness",
        help="Thickness of the Voronoi skin when using surface mode.",
    ),
    density: float = typer.Option(
        0.5,
        "--density",
        help="Relative density of Voronoi cells (higher = more cells).",
    ),
    relief_depth: Optional[float] = typer.Option(
        None,
        "--relief-depth",
        help="Depth of relief carving applied in surface mode.",
    ),
    seeds_json: Optional[str] = typer.Option(
        None,
        "--seeds",
        help="JSON array of centroid coordinates for multicenter mode (e.g. '[[0,0,0],[10,5,2]]').",
    ),
) -> None:
    """Generate Voronoi patterns for 3D models."""

    output_path = output or _default_output_path(input)

    seeds = _parse_seeds(seeds_json)

    if relief_depth is None:
        relief_depth_value = 1.0 if mode is Mode.SURFACE else 0.0
    else:
        relief_depth_value = relief_depth

    _validate_parameters(mode, shell_thickness, density, relief_depth_value, seeds)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        mesh = load_stl(input)
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc), param_hint="input") from exc

    try:
        processed_mesh = run_pipeline(
            mode=mode.value,
            mesh=mesh,
            shell_thickness=shell_thickness,
            density=density,
            relief_depth=relief_depth_value,
            seeds=seeds,
        )
    except PipelineError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    try:
        processed_mesh.export(output_path)
    except Exception as exc:  # pragma: no cover - filesystem or exporter failure
        typer.echo(f"Failed to write mesh to '{output_path}': {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Voronoi mesh saved to {output_path}")
