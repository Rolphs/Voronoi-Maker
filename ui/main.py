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
from typing import Iterable, Optional

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
    QPushButton,
    QPlainTextEdit,
    QSlider,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


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
    """Minimal stub that reserves space for the interactive 3D preview."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("previewPlaceholder")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("3D Preview")
        title.setObjectName("previewTitle")
        description = QLabel(
            "Interactive preview coming soon.\n"
            "Connect vedo/pyvista to :py:meth:`PreviewPlaceholder.update_scene`."
        )
        description.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(description)

    # ------------------------------------------------------------------
    def update_scene(self, mesh_data: object | None) -> None:
        """Placeholder hook to render mesh data in the future.

        Parameters
        ----------
        mesh_data:
            Any object representing the geometry to visualise.  Future work can
            accept `vedo.Plotter` actors, `pyvista.PolyData`, or a custom
            domain object.  This method intentionally does nothing for now.
        """

        _ = mesh_data  # pragma: no cover - placeholder method


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

        self._init_actions()
        self._init_ui()
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

        status_bar = QStatusBar(self)
        status_bar.showMessage("Ready")
        self.setStatusBar(status_bar)

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

        process_button = QPushButton("Apply Voronoi", panel)
        process_button.setEnabled(False)
        process_button.setToolTip("Processing pipeline to be implemented.")
        layout.addWidget(process_button)

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
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        stl_files = [path for path in paths if path.suffix.lower() == ".stl"]
        if not stl_files:
            QMessageBox.warning(self, "Unsupported file", "Please drop STL files only.")
            return

        for path in stl_files:
            logging.getLogger(__name__).info("Queued STL via drag & drop: %s", path)

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

        logging.getLogger(__name__).info("Selected STL file: %s", path)

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
