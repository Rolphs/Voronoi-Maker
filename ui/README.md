# Voronoi Maker UI Skeleton

The `ui/` package contains the PySide6 application shell that mirrors the
workflow described in the project README.  The code purposefully separates the
main window, parameter controls, preview placeholder, and logging console so
that future work can plug in rendering and logging back-ends without refactoring
existing widgets.

## Modules

- `ui/main.py` – Bootstrap script used by `poetry run python ui/main.py`.  It
  defines `MainWindow`, helper widgets, and utility functions for creating a
  `QApplication` instance.
- `ui/__init__.py` – Convenience exports for reusing the UI components in tests
  or alternative launchers.

## Extension points

### 3D preview

The `PreviewPlaceholder` widget in `main.py` reserves screen real estate for the
interactive viewport.  Implementors can subclass it or replace the placeholder
with an object exposing an `update_scene(mesh_data)` method.  When integrating
`vedo`/`pyvista`, a good approach is to embed their OpenGL widgets inside the
placeholder frame and reimplement `update_scene` to handle `PolyData` or custom
mesh structures.

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
