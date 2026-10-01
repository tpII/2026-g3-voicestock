"""GPIO Zero mock pins for physical-input tests.

The pin factory is process-wide. Each test that requests ``mock_pin_factory``
installs a fresh mock factory and restores the previous one afterwards.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import pytest
from gpiozero.pins.mock import MockFactory, MockPin

# The button module imports gpiozero on load. This has to be set before that
# import, which happens while pytest collects the tests in this folder.
os.environ["GPIOZERO_PIN_FACTORY"] = "mock"


class DebouncedMockPin(MockPin):
    """Mock pin that honors ``bounce``, which stock ``MockPin`` only stores.

    GPIO Zero's native backend ignores an edge until more than ``bounce``
    seconds after the last accepted edge. ``MockPin._set_bounce`` is still
    marked unimplemented, so this subclass applies that same rule. Tests drive
    it through ``gpiozero.Button``. ``PushToTalkButton`` does not contain it.
    """

    def __init__(self, factory: MockFactory, info: Any) -> None:
        super().__init__(factory, info)
        self._last_call: float | None = None

    def _call_when_changed(self) -> None:
        ticks = self._last_change
        bounce = self._bounce
        if (
            bounce is None
            or self._last_call is None
            or self.factory.ticks_diff(ticks, self._last_call) > bounce
        ):
            super()._call_when_changed()
            self._last_call = ticks


class SimulatedClock:
    """Monotonic clock that tests can move without sleeping."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def mock_pin_factory() -> Iterator[MockFactory]:
    """Provide a GPIO Zero ``MockFactory`` for one test.

    ``GPIOZERO_PIN_FACTORY`` is set before importing gpiozero so a default
    hardware factory is not chosen on import. ``Device.pin_factory`` is also
    assigned because the library may already have been imported.
    """
    os.environ["GPIOZERO_PIN_FACTORY"] = "mock"

    from gpiozero import Device

    previous = Device.pin_factory
    factory = MockFactory(pin_class=DebouncedMockPin)
    Device.pin_factory = factory
    try:
        yield factory
    finally:
        Device.pin_factory = previous
        factory.close()


@pytest.fixture
def simulated_clock(monkeypatch: pytest.MonkeyPatch) -> SimulatedClock:
    """Replace the mock pin clock so bounce windows are deterministic."""
    clock = SimulatedClock()
    monkeypatch.setattr("gpiozero.pins.mock.monotonic", clock.monotonic)
    return clock
