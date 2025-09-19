import pytest
from typer import BadParameter

from voronoimaker.cli import Mode, _validate_parameters


def test_density_zero_allowed() -> None:
    _validate_parameters(Mode.SURFACE, shell_thickness=1.0, density=0.0, relief_depth=1.0, seeds=1)


def test_density_one_allowed() -> None:
    _validate_parameters(Mode.SURFACE, shell_thickness=1.0, density=1.0, relief_depth=1.0, seeds=1)


def test_density_above_one_rejected() -> None:
    with pytest.raises(BadParameter) as exc_info:
        _validate_parameters(
            Mode.SURFACE,
            shell_thickness=1.0,
            density=1.1,
            relief_depth=1.0,
            seeds=1,
        )

    assert "between 0 and 1" in str(exc_info.value)
