# Voronoi-Maker
Python tool to apply advanced Voronoi patterns (surface, radial, multicenter) to STL models, with shell thickness control and PySide6 3D preview.
**Voronoi Maker** is an experimental Python tool for applying **Voronoi patterns** to 3D models in STL format.  
Unlike scripts that only generate surface Voronoi, this project explores advanced modes:

- **Surface**: Voronoi pattern carved on the mesh surface.  
- **Radial**: cells guided by a vector field radiating from the model’s topological center.  
- **Multicenter**: multiple user-defined centroids create local Voronoi regions.  
- **Shell thickness**: apply Voronoi only to the outer skin of the model, leaving the interior solid.  

The initial MVP is a compiled program for macOS (CLI + minimal GUI).  
Future milestones: a full **desktop app** and **webapp** powered by FastAPI.

---

## Screenshots (WIP)

*(Coming soon: before/after examples and the PySide6 frontend with interactive 3D preview.)*

---

## Recommended frontend

The recommended frontend is built with **PySide6 (Qt)** plus **vedo/pyvista** for interactive 3D preview:

- Native macOS app (packaged with PyInstaller).  
- 3D viewport to rotate, zoom, and toggle original vs voronized mesh.  
- Sliders and selectors for density, shell thickness, relief depth, and Voronoi mode.  
- One-click STL export.  

---

## Installation (development)

Requires Python 3.10+.

```bash
git clone https://github.com/your-username/voronoimaker.git
cd voronoimaker
pip install poetry
poetry install
```

Main dependencies:
- `trimesh`, `numpy`, `scipy`
- `PySide6` (frontend UI)
- `vedo`, `pyvista` (3D preview)
- `typer` (CLI)

---

## Command line usage (CLI)

```bash
poetry run voronoimaker run input.stl output.stl --mode radial --shell-thickness 1.2 --density 0.6 --relief-depth 0.6
```

Key options:
- `--mode`: `surface | radial | multicenter`
- `--shell-thickness`: skin thickness in mm (e.g. `1.2`)
- `--density`: relative density of Voronoi cells (0–1)
- `--relief-depth`: carving/perforation depth in mm
- `--seeds`: JSON list of centroids for multicenter mode

---

## GUI usage (PySide6)

```bash
poetry run python ui/main.py
```

Current features:
- Load STL via drag & drop or file dialog.  
- Adjust Voronoi parameters with sliders.  
- 3D preview (vedo/pyvista).  
- Integrated log console.  

---

## Build macOS binary

Using PyInstaller:

```bash
pyinstaller -w -n "Voronoi Maker" ui/main.py
# output: dist/Voronoi Maker.app
```

You can share this `.app` directly with other 3D printing enthusiasts.

---

## Roadmap

- [x] CLI with basic parameters  
- [x] PySide6 frontend skeleton with sliders and log  
- [ ] Integrated 3D preview (vedo/pyvista)  
- [ ] Boolean operations to carve Voronoi lines on mesh surface  
- [ ] Robust shell offset (true skin thickness)  
- [ ] Reliable STL export for printing  
- [ ] Universal macOS binary (arm64 + x86_64)  
- [ ] FastAPI backend and web frontend (React/Svelte + three.js)  

---

## Contributing

Contributions, bug reports, and feature requests are welcome!  
Areas where help is especially valuable:
- Boolean/mesh operations (robust carving)  
- Offset algorithms for shell thickness  
- UI/UX improvements  

---

## License

MIT © 2025  
Free to use, modify, and distribute.
