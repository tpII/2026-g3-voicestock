"""Smoke tests that verify the project can be imported."""

from importlib.metadata import version


def test_packages_can_be_imported() -> None:
    import pc
    import pi
    import shared

    assert {pc.__name__, pi.__name__, shared.__name__} == {"pc", "pi", "shared"}


def test_distribution_is_installed() -> None:
    assert version("voicestock") == "0.1.0"
