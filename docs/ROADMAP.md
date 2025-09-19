# Roadmap

This roadmap highlights the major workstreams required to deliver a feature-complete Voronoi Maker across CLI, desktop, and future web experiences. Milestones are grouped by theme and ordered roughly by dependency.

## Geometry and processing engine

- [ ] Implement Voronoi cell generation across surface, radial, and multicenter modes.
- [ ] Add configurable seed generators (auto radial sampling, manual JSON ingestion, adaptive density).
- [ ] Perform boolean carving and mesh cleanup to inscribe Voronoi cavities while preserving shell integrity.
- [ ] Provide shell offsetting algorithms that maintain user-defined thickness.
- [ ] Export validated STL files and add regression tests to ensure slicer compatibility.

## Command-line interface

- [ ] Replace `_run_placeholder_pipeline` with calls into the real processing engine.
- [ ] Emit progress and metrics (timings, face counts) for completed jobs.
- [ ] Support batch processing of multiple input files.
- [ ] Surface presets and configuration files for repeatable parameter sets.

## Desktop application (PySide6)

- [ ] Wire the Apply Voronoi button to the processing engine and stream status updates to the log console.
- [ ] Integrate vedo/pyvista (or Qt3D) to render interactive previews with orbit, pan, zoom, and before/after toggles.
- [ ] Implement drag-and-drop queues so multiple meshes can be processed sequentially.
- [ ] Allow saving/exporting the processed mesh directly from the GUI.
- [ ] Persist user preferences (recent files, default parameters).

## Testing and quality

- [ ] Expand unit tests to cover CLI validation, geometry utilities, and UI logic (via Qt test harnesses).
- [ ] Add golden-model tests with sample STL fixtures to catch regressions.
- [ ] Integrate continuous integration workflows (linting, tests, packaging).

## Distribution and platform support

- [ ] Package signed binaries for macOS (arm64/x86_64) using PyInstaller or Briefcase.
- [ ] Provide Windows and Linux builds with consistent functionality.
- [ ] Publish the Python package on PyPI once the API stabilises.

## Web and backend expansion

- [ ] Develop a FastAPI backend that exposes Voronoi processing as a REST job API.
- [ ] Build a lightweight web frontend (React/Svelte) with STL upload, parameter controls, and download links.
- [ ] Investigate WebAssembly/offloading strategies for client-side previews.

## Community and documentation

- [ ] Capture before/after showcases and animated demos for the README and website.
- [ ] Document developer onboarding, coding standards, and contribution guidelines.
- [ ] Maintain an up-to-date changelog and release notes.
