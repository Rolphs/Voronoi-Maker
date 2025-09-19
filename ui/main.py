"""PySide6 desktop frontend entry point.

This module defines the Qt application bootstrap and the placeholder widgets
for Voronoi Maker's forthcoming GUI.  The goal of this skeleton is to provide
clear extension points for the 3D preview integration (vedo/pyvista) and the
logging console so follow-up work can focus on functionality instead of UI
scaffolding.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStackedLayout,
    QPushButton,
    QPlainTextEdit,
    QSlider,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

import trimesh

from voronoimaker.io import load_stl


@dataclass(frozen=True)
class ParameterSpec:
    """Describe a numeric Voronoi parameter for the UI."""

    label: str
    minimum: float
    maximum: float
    default: float
    step: float
    suffix: str = ""


class FloatParameterControl(QWidget):
    """Couple a slider and spin box to edit floating point values."""

    def __init__(self, spec: ParameterSpec, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._spec = spec

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._slider = QSlider(Qt.Horizontal, self)
        self._slider.setFocusPolicy(Qt.StrongFocus)
        self._slider.setSingleStep(1)
        self._slider.setPageStep(5)
        steps = int(round((spec.maximum - spec.minimum) / spec.step))
        self._slider.setRange(0, steps)

        self._spin = QDoubleSpinBox(self)
        self._spin.setDecimals(3)
        self._spin.setRange(spec.minimum, spec.maximum)
        self._spin.setSingleStep(spec.step)
        if spec.suffix:
            self._spin.setSuffix(f" {spec.suffix}")

        layout.addWidget(self._slider)
        layout.addWidget(self._spin)

        self._slider.valueChanged.connect(self._slider_to_spin)
        self._spin.valueChanged.connect(self._spin_to_slider)

        self.set_value(spec.default)

    # ------------------------------------------------------------------
    # value synchronisation helpers
    def _slider_to_spin(self, slider_value: int) -> None:
        new_value = self._spec.minimum + slider_value * self._spec.step
        self._spin.blockSignals(True)
        self._spin.setValue(round(new_value, 6))
        self._spin.blockSignals(False)

    def _spin_to_slider(self, spin_value: float) -> None:
        slider_value = int(round((spin_value - self._spec.minimum) / self._spec.step))
        self._slider.blockSignals(True)
        self._slider.setValue(slider_value)
        self._slider.blockSignals(False)

    # ------------------------------------------------------------------
    def value(self) -> float:
        """Return the current floating-point value."""

        return self._spin.value()

    def set_value(self, value: float) -> None:
        """Programmatically update the control value."""

        self._spin.setValue(value)


class PreviewPlaceholder(QFrame):
    """Embed a vedo/VTK viewport to preview meshes inside the UI."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("previewPlaceholder")

        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self._message_label = QLabel("Initialising 3D preview…", self)
        self._message_label.setAlignment(Qt.AlignCenter)
        self._message_label.setWordWrap(True)
        self._stack.addWidget(self._message_label)

        self._preview_container = QWidget(self)
        self._preview_layout = QVBoxLayout(self._preview_container)
        self._preview_layout.setContentsMargins(0, 0, 0, 0)
        self._preview_layout.setSpacing(0)
        self._stack.addWidget(self._preview_container)

        self._vtk_widget: QWidget | None = None
        self._plotter: "Plotter" | None = None
        self._disabled_reason: str | None = None

        self._initialise_plotter()

    # ------------------------------------------------------------------
    def _initialise_plotter(self) -> None:
        """Attempt to create the vedo plotter inside the Qt widget."""

        try:
            from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
            from vedo import Plotter
        except Exception as exc:  # pragma: no cover - environment dependent
            self._disabled_reason = str(exc)
            self._show_message(
                "3D preview unavailable on this system.\n"
                "Ensure VTK/vedo and OpenGL drivers are installed.\n"
                f"Details: {exc}"
            )
            return

        try:
            self._vtk_widget = QVTKRenderWindowInteractor(self)
            self._preview_layout.addWidget(self._vtk_widget)
            self._plotter = Plotter(
                qt_widget=self._vtk_widget,
                bg="white",
                axes=1,
                interactive=False,
            )
            self._vtk_widget.Initialize()
            self._plotter.initialize_interactor()
            # Render once so the widget initialises correctly even with no mesh.
            self._plotter.render(resetcam=True)
            self._stack.setCurrentWidget(self._preview_container)
        except Exception as exc:  # pragma: no cover - environment dependent
            self._disabled_reason = str(exc)
            self._plotter = None
            self._vtk_widget = None
            self._show_message(
                "3D preview could not be initialised.\n"
                f"Details: {exc}"
            )

    def _show_message(self, message: str) -> None:
        self._message_label.setText(message)
        self._stack.setCurrentWidget(self._message_label)

    def _render(self, reset_camera: bool = False) -> None:
        if self._plotter is None:
            return
        try:
            self._plotter.render(resetcam=reset_camera)
        except Exception:  # pragma: no cover - defensive guard for VTK
            if self._plotter.interactor is not None:
                try:
                    self._plotter.interactor.Render()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    def update_scene(self, mesh_data: object | None) -> None:
        """Render ``mesh_data`` inside the embedded vedo viewport."""

        if self._plotter is None or self._vtk_widget is None:
            reason = self._disabled_reason or "3D preview backend is unavailable."
            self._show_message(reason)
            raise RuntimeError(reason)

        if mesh_data is None:
            self._plotter.clear(deep=True)
            self._render(reset_camera=True)
            self._stack.setCurrentWidget(self._preview_container)
            return

        try:
            from vedo.utils import trimesh2vedo
        except Exception as exc:  # pragma: no cover - optional dependency path
            message = f"3D preview conversion unavailable: {exc}"
            self._show_message(message)
            raise RuntimeError(message) from exc

        try:
            actor = trimesh2vedo(mesh_data)
        except Exception as exc:
            self._show_message(f"Failed to convert mesh for preview: {exc}")
            raise

        self._plotter.clear(deep=True)
        try:
            self._plotter.add(actor)
        except Exception as exc:  # pragma: no cover - vedo rendering guard
            self._show_message(f"Failed to display mesh: {exc}")
            raise

        self._stack.setCurrentWidget(self._preview_container)
        self._render(reset_camera=True)


class LogConsole(QPlainTextEdit):
    """Read-only log display that can later integrate with ``logging``."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("logConsole")
        self.setPlaceholderText("Log output will appear here.")
        self._handler: Optional[logging.Handler] = None

    # ------------------------------------------------------------------
    def install_logging_handler(
        self, logger: Optional[logging.Logger] = None
    ) -> logging.Handler:
        """Attach a logging handler that forwards records to the console.

        Returns the handler so callers can customise level and formatting.
        """

        if logger is None:
            logger = logging.getLogger()

        handler = _QtLogHandler(self)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        self._handler = handler
        return handler

    def remove_logging_handler(self, logger: Optional[logging.Logger] = None) -> None:
        """Detach the previously installed logging handler, if any."""

        if self._handler is None:
            return
        if logger is None:
            logger = logging.getLogger()
        logger.removeHandler(self._handler)
        self._handler.close()
        self._handler = None

    def append_message(self, message: str) -> None:
        """Append plain text to the console in a thread-safe manner."""

        self.appendPlainText(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class _QtLogHandler(logging.Handler):
    """Forward logging records to a :class:`LogConsole`."""

    def __init__(self, console: LogConsole) -> None:
        super().__init__()
        self._console = console

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - UI only
        message = self.format(record)
        self._console.append_message(message)


class MainController:
    """Coordinate mesh loading, preview updates, and export actions."""

    def __init__(
        self,
        preview: PreviewPlaceholder,
        process_button: QPushButton,
        export_button: QPushButton,
        status_bar: QStatusBar,
    ) -> None:
        self._preview = preview
        self._process_button = process_button
        self._export_button = export_button
        self._status_bar = status_bar
        self._logger = logging.getLogger(__name__)

        self._source_path: Path | None = None
        self._source_mesh: trimesh.Trimesh | None = None
        self._processed_mesh: trimesh.Trimesh | None = None

    # ------------------------------------------------------------------
    def load_mesh(self, path: Path) -> trimesh.Trimesh:
        """Load an STL file from ``path`` and update the preview."""

        mesh = load_stl(path)
        self._source_path = Path(path)
        self._source_mesh = mesh
        self._processed_mesh = None

        try:
            self._preview.update_scene(mesh)
        except RuntimeError as exc:  # pragma: no cover - preview optional
            self._logger.warning("Preview unavailable: %s", exc)
        except Exception as exc:
            self._logger.exception("Failed to update preview for %s", path)
            raise

        self._process_button.setEnabled(True)
        self._export_button.setEnabled(False)
        self._status_bar.showMessage(f"Loaded {self._source_path.name}")
        self._logger.info("Loaded STL file: %s", self._source_path)
        return mesh

    # ------------------------------------------------------------------
    def apply_voronoi(self, parameters: Mapping[str, float], mode: str) -> None:
        """Invoke the Voronoi pipeline and refresh the preview."""

        if self._source_mesh is None or self._source_path is None:
            raise RuntimeError("Load an STL file before applying Voronoi.")

        self._status_bar.showMessage("Applying Voronoi…")
        self._logger.info(
            "Applying Voronoi: mode=%s parameters=%s", mode, dict(parameters)
        )

        processed_mesh = self._run_pipeline(self._source_mesh, parameters, mode)
        self._processed_mesh = processed_mesh

        try:
            self._preview.update_scene(processed_mesh)
        except RuntimeError as exc:  # pragma: no cover - preview optional
            self._logger.warning("Preview unavailable: %s", exc)
        except Exception:
            self._logger.exception("Failed to update preview after processing.")
            raise

        self._export_button.setEnabled(True)
        self._status_bar.showMessage("Voronoi preview updated.")

    # ------------------------------------------------------------------
    def export_processed_mesh(self, destination: Path) -> None:
        """Write the processed mesh to ``destination`` as STL."""

        if self._processed_mesh is None:
            raise RuntimeError("Generate a Voronoi mesh before exporting.")

        output_path = Path(destination)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._processed_mesh.export(output_path)
        self._status_bar.showMessage(f"Exported {output_path.name}")
        self._logger.info("Exported Voronoi STL to %s", output_path)

    # ------------------------------------------------------------------
    def default_export_path(self) -> Path:
        """Return a sensible default path for STL exports."""

        if self._source_path is None:
            return Path.home() / "voronoi_output.stl"
        return self._source_path.with_name(self._source_path.stem + "_voronoi.stl")

    @property
    def has_processed_mesh(self) -> bool:
        return self._processed_mesh is not None

    # ------------------------------------------------------------------
    def _run_pipeline(
        self,
        mesh: trimesh.Trimesh,
        parameters: Mapping[str, float],
        mode: str,
    ) -> trimesh.Trimesh:
        """Placeholder hook for the real Voronoi generation pipeline."""

        self._logger.info("Voronoi pipeline placeholder invoked (mode=%s)", mode)
        processed = mesh.copy()
        processed.metadata = processed.metadata or {}
        processed.metadata.update(
            {
                "voronoi_mode": mode,
                "voronoi_parameters": dict(parameters),
            }
        )
        return processed

class MainWindow(QMainWindow):
    """Primary application window with parameter controls and placeholders."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Voronoi Maker")
        self.setMinimumSize(1100, 700)
        self.setAcceptDrops(True)

        self._parameter_controls: dict[str, FloatParameterControl] = {}
        self._preview = PreviewPlaceholder(self)
        self._log_console = LogConsole(self)
        self._process_button: QPushButton | None = None
        self._export_button: QPushButton | None = None
        self._status_bar: QStatusBar | None = None
        self._controller: MainController | None = None

        self._init_actions()
        self._init_ui()
        if self._process_button is None or self._export_button is None:
            raise RuntimeError("Controller buttons were not initialised correctly.")
        if self._status_bar is None:
            raise RuntimeError("Status bar was not initialised correctly.")
        self._controller = MainController(
            preview=self._preview,
            process_button=self._process_button,
            export_button=self._export_button,
            status_bar=self._status_bar,
        )
        self._init_logging()

    # ------------------------------------------------------------------
    def _init_actions(self) -> None:
        """Create global actions (menus, toolbars can hook into these later)."""

        self._open_action = QAction("Open STL…", self)
        self._open_action.setShortcut("Ctrl+O")
        self._open_action.triggered.connect(self._open_file_dialog)

    def _init_ui(self) -> None:
        """Assemble the central widget hierarchy."""

        central = QWidget(self)
        self.setCentralWidget(central)

        main_splitter = QSplitter(Qt.Horizontal, central)

        controls_panel = self._build_controls_panel(main_splitter)
        preview_splitter = self._build_preview_panel(main_splitter)

        main_splitter.addWidget(controls_panel)
        main_splitter.addWidget(preview_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(central)
        layout.addWidget(main_splitter)

        self._status_bar = QStatusBar(self)
        self._status_bar.showMessage("Ready")
        self.setStatusBar(self._status_bar)

        self.addAction(self._open_action)

    def _init_logging(self) -> None:
        """Connect the log console to the root logger."""

        logging.basicConfig(level=logging.INFO)
        self._log_console.install_logging_handler()
        logging.getLogger(__name__).info("Voronoi Maker UI initialised.")

    # ------------------------------------------------------------------
    def _build_controls_panel(self, parent: QWidget) -> QWidget:
        panel = QWidget(parent)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        load_button = QPushButton("Load STL…", panel)
        load_button.clicked.connect(self._open_file_dialog)
        layout.addWidget(load_button)

        layout.addWidget(self._create_parameter_group(panel))
        layout.addWidget(self._create_mode_group(panel))

        self._process_button = QPushButton("Apply Voronoi", panel)
        self._process_button.setEnabled(False)
        self._process_button.setToolTip(
            "Apply the configured Voronoi parameters to the loaded mesh."
        )
        self._process_button.clicked.connect(self._apply_voronoi)
        layout.addWidget(self._process_button)

        self._export_button = QPushButton("Export STL…", panel)
        self._export_button.setEnabled(False)
        self._export_button.setToolTip("Save the processed Voronoi mesh to disk.")
        self._export_button.clicked.connect(self._export_stl)
        layout.addWidget(self._export_button)

        layout.addStretch(1)
        return panel

    def _build_preview_panel(self, parent: QWidget) -> QWidget:
        splitter = QSplitter(Qt.Vertical, parent)
        splitter.addWidget(self._preview)
        splitter.addWidget(self._log_console)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        return splitter

    # ------------------------------------------------------------------
    def _load_mesh_from_path(self, path: Path) -> None:
        if self._controller is None:
            return

        logger = logging.getLogger(__name__)
        try:
            self._controller.load_mesh(path)
        except FileNotFoundError as exc:
            QMessageBox.critical(self, "File not found", str(exc))
        except ValueError as exc:
            QMessageBox.critical(self, "Failed to load STL", str(exc))
        except Exception as exc:  # pragma: no cover - UI only
            logger.exception("Unexpected error while loading %s", path)
            QMessageBox.critical(self, "Failed to load STL", str(exc))
        else:
            logger.info("Loaded STL file: %s", path)

    def _gather_parameters(self) -> dict[str, float]:
        return {label: control.value() for label, control in self._parameter_controls.items()}

    def _apply_voronoi(self) -> None:  # pragma: no cover - UI only
        if self._controller is None:
            return

        parameters = self._gather_parameters()
        mode = self._mode_selector.currentText()
        logger = logging.getLogger(__name__)
        try:
            self._controller.apply_voronoi(parameters, mode)
        except RuntimeError as exc:
            QMessageBox.warning(self, "Voronoi Maker", str(exc))
        except Exception as exc:
            logger.exception("Voronoi processing failed")
            QMessageBox.critical(self, "Voronoi processing failed", str(exc))

    def _export_stl(self) -> None:  # pragma: no cover - UI only
        if self._controller is None:
            return

        suggested = self._controller.default_export_path()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Voronoi STL",
            str(suggested),
            "STL files (*.stl);;All files (*)",
        )
        if not path:
            return

        logger = logging.getLogger(__name__)
        try:
            self._controller.export_processed_mesh(Path(path))
        except RuntimeError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
        except Exception as exc:
            logger.exception("Failed to export STL to %s", path)
            QMessageBox.critical(self, "Export failed", str(exc))
        else:
            QMessageBox.information(self, "Export complete", f"Voronoi mesh saved to {path}")

    # ------------------------------------------------------------------
    def _create_parameter_group(self, parent: QWidget) -> QGroupBox:
        group = QGroupBox("Voronoi Parameters", parent)
        form = QFormLayout(group)

        specs = [
            ParameterSpec("Density", 0.0, 1.0, 0.6, 0.05),
            ParameterSpec("Shell thickness", 0.0, 5.0, 1.2, 0.1, "mm"),
            ParameterSpec("Relief depth", 0.0, 5.0, 0.6, 0.1, "mm"),
        ]

        for spec in specs:
            control = FloatParameterControl(spec, group)
            form.addRow(spec.label + ":", control)
            self._parameter_controls[spec.label] = control

        return group

    def _create_mode_group(self, parent: QWidget) -> QGroupBox:
        group = QGroupBox("Voronoi Mode", parent)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(9, 9, 9, 9)

        self._mode_selector = QComboBox(group)
        self._mode_selector.addItems(["Surface", "Radial", "Multicenter"])
        self._mode_selector.setCurrentText("Radial")

        layout.addWidget(QLabel("Select the Voronoi generation mode:"))
        layout.addWidget(self._mode_selector)

        centroid_hint = QLabel(
            "Multicenter seeds can be configured in a future release."
        )
        centroid_hint.setWordWrap(True)
        centroid_hint.setObjectName("modeHint")
        layout.addWidget(centroid_hint)

        return group

    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # pragma: no cover - UI only
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # pragma: no cover - UI only
        if self._controller is None:
            return

        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        stl_files = [path for path in paths if path.suffix.lower() == ".stl"]
        if not stl_files:
            QMessageBox.warning(self, "Unsupported file", "Please drop STL files only.")
            event.ignore()
            return

        event.acceptProposedAction()
        for path in stl_files:
            self._load_mesh_from_path(path)

    # ------------------------------------------------------------------
    def _open_file_dialog(self) -> None:
        """Prompt the user to pick an STL file."""

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open STL file",
            str(Path.home()),
            "STL files (*.stl);;All files (*)",
        )
        if not path:
            return

        self._load_mesh_from_path(Path(path))

    # ------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # pragma: no cover - UI only
        self._log_console.remove_logging_handler()
        super().closeEvent(event)


def iter_qapplication(argv: Optional[Iterable[str]] = None) -> QApplication:
    """Create (or reuse) a :class:`QApplication` instance.

    Separating this logic makes it easier to unit-test widgets in isolation.
    """

    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else [])
    return app


def main() -> None:
    """Entry point for the ``poetry run python ui/main.py`` command."""

    app = iter_qapplication()
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover - manual invocation only
    main()
