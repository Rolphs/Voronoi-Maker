import pytest
from typer import BadParameter

from voronoimaker.cli import Mode, _parse_seeds, _validate_parameters


def test_density_zero_allowed() -> None:
    _validate_parameters(
        Mode.SURFACE,
        shell_thickness=1.0,
        density=0.0,
        relief_depth=1.0,
        seeds=[],
    )


def test_density_one_allowed() -> None:
    _validate_parameters(
        Mode.SURFACE,
        shell_thickness=1.0,
        density=1.0,
        relief_depth=1.0,
        seeds=[],
    )


def test_density_above_one_rejected() -> None:
    with pytest.raises(BadParameter) as exc_info:
        _validate_parameters(
            Mode.SURFACE,
            shell_thickness=1.0,
            density=1.1,
            relief_depth=1.0,
            seeds=[],
        )

    assert "between 0 and 1" in str(exc_info.value)


def test_multicenter_requires_at_least_one_seed() -> None:
    with pytest.raises(BadParameter):
        _validate_parameters(
            Mode.MULTICENTER,
            shell_thickness=1.0,
            density=0.5,
            relief_depth=1.0,
            seeds=[],
        )


def test_seeds_not_allowed_for_non_multicenter_modes() -> None:
    with pytest.raises(BadParameter) as exc_info:
        _validate_parameters(
            Mode.SURFACE,
            shell_thickness=1.0,
            density=0.5,
            relief_depth=1.0,
            seeds=[(0.0, 0.0, 0.0)],
        )

    assert "multicenter" in str(exc_info.value)


def test_parse_seeds_valid_json() -> None:
    assert _parse_seeds("[[0, 0, 0], [1.5, 2.5, 3.5]]") == [
        (0.0, 0.0, 0.0),
        (1.5, 2.5, 3.5),
    ]


@pytest.mark.parametrize(
    "payload, message",
    [
        ("", ""),
        ("[]", ""),
        ("not json", "valid JSON"),
        ("{}", "array"),
        ("[1, 2]", "three"),
        ("[[1, 2, \"a\"]]", "numbers"),
    ],
)
def test_parse_seeds_invalid_inputs(payload: str, message: str) -> None:
    if payload in {"", "[]"}:
        assert _parse_seeds(payload) == []
        return

    with pytest.raises(BadParameter) as exc_info:
        _parse_seeds(payload)

    assert message in str(exc_info.value)
