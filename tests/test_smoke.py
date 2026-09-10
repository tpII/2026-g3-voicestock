"""Smoke tests that verify the project can be imported."""


def test_voicestock_can_be_imported() -> None:
    import voicestock

    assert voicestock.__version__ == "0.1.0"
