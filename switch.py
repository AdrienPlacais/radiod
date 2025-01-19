"""Define a Switch.

The difference with Button is that Switch keeps it's current state.

"""

import time
from collections.abc import Callable

import RPi.GPIO as GPIO
from button_class import Button
from log_class import Log


class Switch(Button):
    """
    A class representing a switch that inherits from the Button class.

    The Switch class maintains a persistent state (ON/OFF) and toggles this
    state each time it is pressed.

    """

    def __init__(
        self,
        button: int,
        log: Log,
        callback: Callable | None = None,
        pull_up_down: int = GPIO.PUD_DOWN,
        bouncetime: int = 200,
        stable_time: float = 0.05,
        name: str = "",
        invert_logic: bool = True,
    ):
        """Initialize the Switch object.

        Parameters
        ----------
        gpio : int
            The GPIO pin number associated with the switch.
        callback : Callable
            A function to call when the switch is pressed. The function will
            receive two arguments: the GPIO pin number and the new state (bool).
        log : Log
            The logging object used to record events.
        pull_up_down : int, optional
            Specifies whether to use a pull-up or pull-down resistor. Default
            is `GPIO.PUD_DOWN`.
        bouncetime : int, optional
            Debounce time for button presses in milliseconds. Default is 200.
        stable_time : float, optional
            Minimum time (in seconds) the state must remain stable before
            confirming the change. Default is 0.05 seconds (50 ms).
        name : str, optional
            Name of the switch.
        invert_logic : bool, optional
            If ON and OFF should be inverted.

        """
        self._name = name
        if callback is None:
            callback = self._debug_callback
        super().__init__(button, callback, log, pull_up_down, bouncetime)

        raw_state = GPIO.input(button)
        self.state: bool = not raw_state if invert_logic else raw_state
        self.stable_time: float = stable_time
        self.last_state_time: float = time.time()
        self.invert_logic: bool = invert_logic

        state_str = "ON" if self.state else "OFF"
        self.log.message(
            f"Switch initialized on GPIO {button} with initial state {state_str} "
            f"(inverted: {self.invert_logic})",
            self.log.DEBUG,
        )

    def button_event(self, button: int) -> None:
        """
        Handle the switch press event, confirming state changes only if the new state
        is stable for the specified duration.

        Parameters
        ----------
        button : int
            The GPIO pin number where the event occurred.

        """
        raw_state = GPIO.input(button)
        current_state = not raw_state if self.invert_logic else raw_state
        current_time = time.time()

        # Check if the state has been stable for the required time
        if (
            current_state != self.state
            and (current_time - self.last_state_time) >= self.stable_time
        ):
            # Update the switch state
            self.state = current_state
            self.last_state_time = current_time

            # Log the state change
            state_str = "ON" if self.state else "OFF"
            self.log.message(
                f"Switch event on GPIO {button}: State changed to {state_str}",
                self.log.DEBUG,
            )

            # Invoke the callback with the GPIO pin and the new state
            self.callback(button, self.state)

    def get_state(self) -> bool:
        """Get the current state of the switch.

        Returns
        -------
        bool
            True if the switch is ON, False if it is OFF.

        """
        return self.state

    def _debug_callback(self, *args, **kwargs) -> None:
        """Print a message when the button is pressed."""
        state_str = "ON" if self.state else "OFF"
        print(
            f"[DEBUG] Switch {self._name} on GPIO {self.button} changed state to {state_str}"
        )
