"""Command line interface for the Voronoi Maker package."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer


class Mode(str, Enum):
    """Supported processing modes for Voronoi generation."""

    SHELL = "shell"
    SOLID = "solid"
    RELIEF = "relief"


app = typer.Typer(help="Generate Voronoi patterns for 3D models.")


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


def _ensure_positive_int(name: str, value: int) -> None:
    """Ensure ``value`` is a positive integer."""

    if value <= 0:
        raise typer.BadParameter(f"{name} must be a positive integer.", param_hint=name)


def _validate_parameters(
    mode: Mode,
    shell_thickness: float,
    density: float,
    relief_depth: float,
    seeds: int,
) -> None:
    """Perform lightweight validation for CLI parameters.

    This keeps the CLI usable before the full Voronoi pipeline is implemented.
    """

    _ensure_positive("shell_thickness", shell_thickness)
    _ensure_positive("density", density)
    _ensure_non_negative("relief_depth", relief_depth)
    _ensure_positive_int("seeds", seeds)

    if mode is Mode.RELIEF and relief_depth == 0:
        raise typer.BadParameter(
            "relief_depth must be greater than zero when using relief mode.",
            param_hint="relief_depth",
        )
    # TODO: Add domain-specific validation rules for mode combinations once
    #       the Voronoi-processing pipeline is available.


def _run_placeholder_pipeline(
    input_path: Path,
    output_path: Path,
    mode: Mode,
    shell_thickness: float,
    density: float,
    relief_depth: float,
    seeds: int,
) -> None:
    """Placeholder pipeline execution.

    The real Voronoi processing pipeline will replace this implementation.
    """

    typer.echo("Voronoi Maker (placeholder)")
    typer.echo(f"  Input:  {input_path}")
    typer.echo(f"  Output: {output_path}")
    typer.echo(f"  Mode:   {mode.value}")
    typer.echo(f"  Shell thickness: {shell_thickness}")
    typer.echo(f"  Density:         {density}")
    typer.echo(f"  Relief depth:    {relief_depth}")
    typer.echo(f"  Seeds:           {seeds}")
    # TODO: Replace with real Voronoi generation logic when available.


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
        Mode.SHELL,
        "--mode",
        "-m",
        case_sensitive=False,
        help="Processing mode to use for Voronoi generation.",
    ),
    shell_thickness: float = typer.Option(
        2.0,
        "--shell-thickness",
        help="Thickness of the shell when using shell mode.",
    ),
    density: float = typer.Option(
        0.5,
        "--density",
        help="Relative density of Voronoi cells (higher = more cells).",
    ),
    relief_depth: float = typer.Option(
        1.0,
        "--relief-depth",
        help="Depth of relief carving when using relief mode.",
    ),
    seeds: int = typer.Option(
        500,
        "--seeds",
        help="Number of seed points to use for Voronoi generation.",
    ),
) -> None:
    """Generate Voronoi patterns for 3D models."""

    output_path = output or _default_output_path(input)

    _validate_parameters(mode, shell_thickness, density, relief_depth, seeds)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    _run_placeholder_pipeline(
        input_path=input,
        output_path=output_path,
        mode=mode,
        shell_thickness=shell_thickness,
        density=density,
        relief_depth=relief_depth,
        seeds=seeds,
    )
    # TODO: Replace placeholder execution with the actual Voronoi pipeline.
