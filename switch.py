#!/usr/bin/env python3
"""Define a Switch.

The difference with Button is that Switch keeps it's current state.

"""

import sys
import time
from collections.abc import Callable
from typing import Literal

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
        gpio: int,
        log: Log,
        pull_up_down: Literal[0, 1] = 0,
        callback: Callable | None = None,
        stable_time: float = 0.05,
        name: str = "",
        invert_logic: bool = True,
    ) -> None:
        """Initialize the Switch object.

        Parameters
        ----------
        gpio : int
            The GPIO pin number associated with the switch.
        log : Log
            The logging object used to record events.
        pull_up_down : int, optional
            Specifies whether to use a pull-up or pull-down resistor. The
            default is 0.
        callback : Callable | None, optional
            A function to call when the switch is pressed. The function will
            receive two arguments: the GPIO pin number and the new state (bool).
            If None, we set a default function that simply prints some info.
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
        super().__init__(
            button=gpio, callback=callback, log=log, pull_up_down=pull_up_down
        )

        raw_state: bool = GPIO.input(gpio)
        self.state: bool = not raw_state if invert_logic else raw_state
        self.stable_time: float = stable_time
        self.last_state_time: float = time.time()
        self.invert_logic: bool = invert_logic

        state_str = "ON" if self.state else "OFF"
        self.log.message(
            f"Switch initialized on GPIO {gpio} with initial state {state_str} "
            f"(inverted: {self.invert_logic}). {name = }",
            self.log.DEBUG,
        )

    def button_event(self, button: int) -> None:
        """Handle the switch press event.

        Confirm state changes only if the new state is stable for the specified
        duration.

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


if __name__ == "__main__":
    from config_class import Configuration
    from log_class import Log

    config = Configuration()
    log = Log()
    if len(log.getName()) < 1:
        log.init("radio")

    print("Test Switch class")

    # Get switch configuration
    off_gpio = config.getSwitchGpio("off_switch")
    fip_gpio = config.getSwitchGpio("fip_switch")
    spotify_gpio = config.getSwitchGpio("spotify_switch")
    unused_gpio = config.getSwitchGpio("unused_switch")
    disco_gpio = config.getSwitchGpio("disco_switch")

    print(f"off_switch GPIO: {off_gpio}")
    print(f"fip_switch GPIO: {fip_gpio}")
    print(f"spotify_switch GPIO: {spotify_gpio}")
    print(f"unused_switch GPIO: {unused_gpio}")
    print(f"disco_switch GPIO: {disco_gpio}")

    pull_up_down_strings = ["DOWN", "UP"]
    pull_up_down = config.pull_up_down
    assert pull_up_down in (0, 1)
    print(f"Pull Up/Down resistors: {pull_up_down_strings[pull_up_down]}")

    for gpio, name in zip(
        (off_gpio, fip_gpio, spotify_gpio, unused_gpio, disco_gpio),
        ("OFF", "FIP", "SPOTIFY", "UNUSED", "DISCO"),
        strict=True,
    ):
        _ = Switch(
            gpio=gpio, log=log, callback=None, pull_up_down=pull_up_down, name=name
        )

    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print(" Stopped")
        GPIO.cleanup()
        sys.exit(0)
