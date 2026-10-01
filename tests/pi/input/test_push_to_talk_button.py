"""Tests for the physical push-to-talk button.

GPIO Zero mock pins stand in for the Raspberry Pi. With the internal pull-up,
a press is electrical low (``MockPin.drive_low``) and a release is electrical
high (``MockPin.drive_high``).
"""

from collections.abc import Callable

from gpiozero import Button
from gpiozero.pins.mock import MockFactory, MockPin
from tests.pi.input.conftest import SimulatedClock

from pi.input.push_to_talk_button import PushToTalkButton

# Arbitrary BCM pin that exists on the mock Pi. The product pin is undecided.
PIN = 17
BOUNCE_TIME = 0.05
# GPIO Zero accepts the next edge only when the elapsed time is greater than
# bounce_time, so the simulated clock moves slightly past that instant.
_PAST_BOUNCE = BOUNCE_TIME + 1e-6


def _callbacks() -> tuple[list[str], Callable[[], None], Callable[[], None]]:
    events: list[str] = []

    def on_pressed() -> None:
        events.append("pressed")

    def on_released() -> None:
        events.append("released")

    return events, on_pressed, on_released


def _configured_pin(factory: MockFactory) -> MockPin:
    """Return the mock pin reserved for ``PIN``.

    ``MockFactory.pin`` returns the pin already created for that number, so the
    assertions observe the ``Button`` GPIO Zero built rather than a stand-in.
    """
    return factory.pin(PIN)


def _open_button(
    on_pressed: Callable[[], None],
    on_released: Callable[[], None],
) -> PushToTalkButton:
    return PushToTalkButton(
        PIN,
        BOUNCE_TIME,
        on_pressed=on_pressed,
        on_released=on_released,
    )


def test_constructs_on_mock_pin_with_pull_up_and_bounce(
    mock_pin_factory: MockFactory,
) -> None:
    """The button can be built without hardware and keeps the given pin setup."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    try:
        pin = _configured_pin(mock_pin_factory)
        assert pin.info.name == f"GPIO{PIN}"
        assert pin.pull == "up"
        assert pin.state is True
        assert pin.bounce == BOUNCE_TIME
        assert events == []
    finally:
        button.close()


def test_press_notifies_pressed_once(mock_pin_factory: MockFactory) -> None:
    """Driving the pin from high to low notifies pressed once."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    try:
        _configured_pin(mock_pin_factory).drive_low()
        assert events == ["pressed"]
    finally:
        button.close()


def test_release_notifies_released_once_after_press(
    mock_pin_factory: MockFactory,
    simulated_clock: SimulatedClock,
) -> None:
    """After a press, driving the pin from low to high notifies released once."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    try:
        pin = _configured_pin(mock_pin_factory)
        pin.drive_low()
        simulated_clock.advance(_PAST_BOUNCE)
        pin.drive_high()
        assert events == ["pressed", "released"]
    finally:
        button.close()


def test_press_then_release_notifies_in_semantic_order(
    mock_pin_factory: MockFactory,
    simulated_clock: SimulatedClock,
) -> None:
    """A full press and release cycle notifies pressed, then released."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    try:
        pin = _configured_pin(mock_pin_factory)
        pin.drive_low()
        simulated_clock.advance(_PAST_BOUNCE)
        pin.drive_high()
        assert events == ["pressed", "released"]
    finally:
        button.close()


def test_repeated_cycles_notify_each_valid_transition(
    mock_pin_factory: MockFactory,
    simulated_clock: SimulatedClock,
) -> None:
    """Each real edge notifies once. Holding a level does not repeat it."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    try:
        pin = _configured_pin(mock_pin_factory)
        for _ in range(3):
            pin.drive_low()
            simulated_clock.advance(_PAST_BOUNCE)
            pin.drive_high()
            simulated_clock.advance(_PAST_BOUNCE)
        pin.drive_low()
        pin.drive_low()
        simulated_clock.advance(_PAST_BOUNCE)
        pin.drive_high()
        pin.drive_high()
        assert events == ["pressed", "released"] * 4
    finally:
        button.close()


def test_bounce_within_window_notifies_press_once(
    mock_pin_factory: MockFactory,
    simulated_clock: SimulatedClock,
) -> None:
    """Chatter inside the bounce window does not emit extra callbacks."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    try:
        pin = _configured_pin(mock_pin_factory)
        pin.drive_low()
        simulated_clock.advance(BOUNCE_TIME / 5)
        pin.drive_high()
        simulated_clock.advance(BOUNCE_TIME / 5)
        pin.drive_low()
        simulated_clock.advance(BOUNCE_TIME / 5)
        pin.drive_high()
        pin.drive_low()
        assert events == ["pressed"]
    finally:
        button.close()


def test_transition_after_bounce_window_is_detected(
    mock_pin_factory: MockFactory,
    simulated_clock: SimulatedClock,
) -> None:
    """A later edge is reported once the bounce interval has elapsed."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    try:
        pin = _configured_pin(mock_pin_factory)
        pin.drive_low()
        simulated_clock.advance(BOUNCE_TIME / 5)
        pin.drive_high()
        pin.drive_low()
        assert events == ["pressed"]

        simulated_clock.advance(_PAST_BOUNCE)
        pin.drive_high()
        assert events == ["pressed", "released"]
    finally:
        button.close()


def test_close_releases_the_underlying_pin(mock_pin_factory: MockFactory) -> None:
    """close() drops callbacks and frees the pin for another device."""
    events, on_pressed, on_released = _callbacks()
    button = _open_button(on_pressed, on_released)
    pin = _configured_pin(mock_pin_factory)
    button.close()

    pin.drive_low()
    assert events == []

    replacement = Button(PIN, pull_up=True, bounce_time=BOUNCE_TIME)
    replacement.close()
