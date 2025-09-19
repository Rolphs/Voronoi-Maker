# User Stories

## Legend
- **Done** – Implemented and working today.
- **WIP** – Partially implemented, placeholder-backed, or blocked by dependencies.
- **TODO** – Planned but not yet started.
- **Proposed** – Suggested ideas pending triage.

## Command-line workflow

### CLI generates Voronoi jobs — **Status: WIP**
As a command-line user, I want to run `voronoimaker run` with my preferred mode and parameters so that I can generate a processed STL on demand. The Typer-based CLI exposes arguments, validates parameters, derives output filenames, and invokes a placeholder pipeline. Actual Voronoi processing is still under development.

### CLI validates numeric parameters — **Status: Done**
As a command-line user, I want immediate feedback when I provide invalid numeric parameters so that I can correct mistakes before processing. The CLI performs range checks, mode-specific guards, and emits actionable error messages.

### CLI auto-derives output filenames — **Status: Done**
As a command-line user, I want the tool to pick a sensible destination when I omit `--output` so that I can iterate quickly. The CLI derives a `_voronoi` filename next to the source mesh and creates parent directories on demand.

### Multicenter seed ingestion accepts JSON payloads — **Status: TODO**
As a multicenter user, I want to pass an explicit list of centroid coordinates so that the Voronoi regions follow my chosen anchors. The CLI currently accepts only numeric counts and validates structure, but the downstream pipeline ignores seed data until the geometry engine arrives.

## Desktop application

### PySide6 main window exposes controls — **Status: Done**
As a desktop user, I want a main window with grouped parameter sliders, mode selectors, and room for previews so that tuning settings feels approachable. The `MainWindow` assembles parameter widgets, a mode selector, and a split layout that reserves space for preview and logs.

### STL selection and drag & drop queue files — **Status: WIP**
As a desktop user, I want to add STL files via buttons or drag-and-drop so that I can start processing without leaving the GUI. The UI logs file selections but still routes processing through stubs.

### 3D preview renders interactive meshes — **Status: WIP**
As a desktop user, I want to inspect meshes in-app so that I can verify the Voronoi effect before exporting. A placeholder frame and update hooks exist, yet no rendering backend is wired in; integrating vedo/pyvista remains open.

### Apply Voronoi action runs the pipeline — **Status: TODO**
As a desktop user, I want the “Apply Voronoi” button to generate a new mesh so that the GUI completes the workflow. The button is present but disabled with a tooltip explaining that the pipeline is not ready.

### Embedded log console captures application messages — **Status: Done**
As a desktop user, I want to see progress and warnings in-app so that I know what the tool is doing. The log console registers a Qt-aware logging handler, auto-scrolls new messages, and is initialized with the window.

## Voronoi processing pipeline

### Boolean Voronoi carving on meshes — **Status: TODO**
As a mesh-processing engineer, I want robust boolean operations that inscribe Voronoi cells onto STL surfaces so that the output geometry reflects the selected pattern. The CLI and GUI are waiting on this core functionality.

### Shell offset control matches requested thickness — **Status: TODO**
As a maker focused on printability, I want the Voronoi skin to maintain a reliable shell thickness so that the final part is structurally sound. This remains a roadmap item with no implementation in the current codebase.

### Export produces printer-ready STL files — **Status: TODO**
As a user preparing prints, I want the tool to emit valid STL files directly so that I can slice them immediately. Reliable export is still on the roadmap.

## Distribution and platform

### Packaged macOS application — **Status: TODO**
As a macOS user, I want a signed binary I can launch without a Python environment so that sharing the tool is easy. Build instructions mention PyInstaller packaging, but producing a universal binary is still planned.

## Web and backend expansion

### FastAPI backend with web client — **Status: TODO**
As a remote user, I want to run Voronoi processing from a web interface so that I can use the tool without installing desktop software. A FastAPI backend and web frontend are future milestones with no supporting code yet.

## Proposed ideas awaiting triage

### Rich 3D viewport interactions — **Status: Proposed**
As a power user, I want to rotate, zoom, and compare original versus voronized meshes inside the UI so that I can judge quality visually. These capabilities are described as part of the recommended frontend but have no implementation yet.

### One-click STL export from the UI — **Status: Proposed**
As a desktop user, I want to export the processed mesh with a single action so that I can quickly move to slicing. This convenience feature is suggested alongside other UI ideas and still needs design and implementation discussions.

### Showcase before/after screenshots — **Status: Proposed**
As a prospective user, I want to see example results so that I understand the project’s value. The README promises upcoming screenshots, indicating that collecting and publishing them is still on the wish list.
