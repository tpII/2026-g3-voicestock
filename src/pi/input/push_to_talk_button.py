"""GPIO adapter for the push-to-talk button."""

from collections.abc import Callable

from gpiozero import Button


class PushToTalkButton:
    """Forward button press and release to caller-supplied callbacks.

    Wiring is fixed: the button connects the GPIO pin to ground and the
    internal pull-up stays enabled, so released is high and pressed is low.
    ``pin`` and ``bounce_time`` (seconds) are the only settings. ``bounce_time``
    is passed through to GPIO Zero.

    The button is active after construction. ``close`` releases the GPIO pin.
    """

    def __init__(
        self,
        pin: int,
        bounce_time: float,
        on_pressed: Callable[[], None],
        on_released: Callable[[], None],
    ) -> None:
        self._button = Button(
            pin,
            pull_up=True,
            bounce_time=bounce_time,
        )
        self._button.when_pressed = on_pressed
        self._button.when_released = on_released

    def close(self) -> None:
        """Release the underlying GPIO Zero button."""
        self._button.close()
