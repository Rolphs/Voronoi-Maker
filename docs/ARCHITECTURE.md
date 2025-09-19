# Architecture Overview

Voronoi Maker is structured as a Python project that exposes both a command-line interface (CLI) and a desktop GUI shell. The core Voronoi processing engine is still under construction, so the current architecture emphasises modular frontends that can be wired into the forthcoming geometry pipeline.

## Source layout

```
src/
  voronoimaker/
    __init__.py
    cli.py
ui/
  main.py
```

- **`src/voronoimaker`** hosts the distributable Python package. It is configured with a `src` layout via `pyproject.toml` so that tooling (Poetry, test runners) imports the package consistently.
- **`cli.py`** defines the Typer-based entry point published as the `voronoimaker` console script. Today it performs argument validation and dispatches to a placeholder pipeline. When the geometry engine is ready, it will orchestrate preprocessing, Voronoi carving, and STL export.
- **`ui/main.py`** contains the PySide6 application bootstrap and widget definitions. The GUI is currently a skeleton designed to surface parameter controls, drag-and-drop for STL files, logging, and a reserved area for the upcoming 3D preview.

## Command-line flow

1. Users invoke `voronoimaker run` with an input STL, optional output path, processing mode, and numeric parameters.
2. The CLI derives the destination path when `--output` is omitted (`_default_output_path`).
3. Seeds for multicenter mode are parsed from JSON, validated, and returned as coordinate triples.
4. `_validate_parameters` enforces numeric ranges and mode-specific rules (e.g., relief depth cannot be zero in surface mode, multicenter mode requires at least one seed).
5. A placeholder `_run_placeholder_pipeline` echoes the configuration; this will eventually delegate to the real Voronoi engine.

The CLI module is intentionally self-contained and does not yet import geometry libraries. This keeps the interface stable while the backend evolves.

## Desktop application flow

1. `ui/main.py` boots a `QApplication`, constructs the `MainWindow`, and enters the Qt event loop.
2. `MainWindow` assembles three major regions:
   - A **parameter sidebar** with `FloatParameterControl` widgets that pair sliders with spin boxes for responsive numeric tuning.
   - A **preview placeholder** (`PreviewPlaceholder`) that will host vedo/pyvista integrations. Its `update_scene` hook is ready for future mesh rendering code.
   - A **log console** (`LogConsole`) that integrates with Python's `logging` module through a lightweight `_QtLogHandler`.
3. File input actions are exposed via menu entries, toolbar buttons, and drag-and-drop handlers. They currently record file selections in the console but defer processing until the backend is complete.
4. The “Apply Voronoi” action exists in the UI state machine but remains disabled until the geometry pipeline is implemented.

## Planned backend integration

The eventual Voronoi pipeline will likely introduce additional modules to:

- Load and normalise STL meshes (via `trimesh` or `pyvista`).
- Generate Voronoi seeds (surface, radial, multicenter) and compute cell boundaries.
- Perform boolean operations to carve Voronoi cavities while respecting shell thickness targets.
- Export validated STL geometry ready for slicing.

These capabilities will live alongside the existing package and be consumed by both the CLI and GUI. The separation between frontends (CLI/UI) and the yet-to-be-built geometry core keeps the architecture flexible: new delivery channels (e.g., FastAPI backend) can reuse the same processing layer with minimal duplication.
