# Voronoi Maker UI Skeleton

The `ui/` package contains the PySide6 application that mirrors the workflow
described in the project README.  The code separates the main window, parameter
controls, vedo-powered preview viewport, and logging console so new features can
focus on functionality instead of UI scaffolding.

## Modules

- `ui/main.py` – Bootstrap script used by `poetry run python ui/main.py`.  It
  defines `MainWindow`, helper widgets, and utility functions for creating a
  `QApplication` instance.
- `ui/__init__.py` – Convenience exports for reusing the UI components in tests
  or alternative launchers.

## Extension points

### 3D preview

The `PreviewPlaceholder` widget in `main.py` embeds a VTK
`QVTKRenderWindowInteractor` and configures a vedo `Plotter`.  Meshes passed to
`update_scene(mesh_data)` are converted from `trimesh.Trimesh` instances via
`vedo.utils.trimesh2vedo` and rendered inside the Qt application.  When VTK or
OpenGL drivers are missing (common on headless CI systems) the widget shows a
status message explaining how to enable the preview instead of crashing.

### Logging console

The `LogConsole` widget already knows how to register itself as a logging
handler.  Additional formatters or log filtering logic can be added by
configuring the returned handler (`LogConsole.install_logging_handler`).  For
example:

```python
console = LogConsole()
handler = console.install_logging_handler(logging.getLogger("voronoimaker"))
handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
```

### Parameter controls

The `FloatParameterControl` helper couples a slider with a spin box.  If future
features need more parameters (for example, anisotropy controls or randomness
seeds), create a new `ParameterSpec` instance and add it to the form inside
`MainWindow._create_parameter_group`.

## Resources

Place icons, Qt Designer `.ui` files, or style sheets inside a `ui/resources/`
folder.  The launcher does not depend on those assets yet, but the directory is
reserved so new assets can be referenced consistently across platforms.

## Manual preview testing

Automated GUI tests are not wired up yet.  Developers can exercise the preview
manually with the following steps:

1. Install dependencies (including VTK/vedo) with `poetry install`.
2. Launch the UI via `poetry run python ui/main.py`.
3. Load an STL mesh using **Load STL…** or by dragging a `.stl` file onto the
   window.  The controller parses the mesh with `voronoimaker.io.load_stl` and
   forwards it to the preview.
4. Adjust Voronoi parameters and press **Apply Voronoi** to refresh the preview.
   The current implementation stores the parameters on the mesh metadata until
   the full pipeline is available.
5. Use **Export STL…** to write the (placeholder) Voronoi mesh to disk.  The UI
   proposes a filename derived from the source STL.

If the preview reports that OpenGL is unavailable, verify that a suitable GPU
driver and VTK runtime are installed on the host system.  Offscreen/headless
environments typically require VirtualGL or similar tooling to enable rendering.
