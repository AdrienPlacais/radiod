#!/usr/bin/env python3
"""Define a Switch.

The difference with Button is that Switch keeps it's current state.

"""
import sys
import threading
import time
from collections.abc import Callable
from typing import Literal

import RPi.GPIO as GPIO
from disco_light import DiscoLight
from log_class import Log

GPIO.setmode(GPIO.BCM)


class Switch:
    """A class representing a switch.

    The Switch class triggers an action immediately after the button is pressed
    for a specified duration (`MIN_PRESS_DURATION`).
    """

    def __init__(
        self,
        gpio: int,
        log: Log,
        detect: Literal["rising", "falling", "both"],
        callback: Callable | None = None,
        name: str = "",
    ) -> None:
        """
        Initialize the Switch object.

        Parameters
        ----------
        gpio : int
            GPIO pin number for the switch.
        log : Log
            Logging object for messages.
        callback : Callable, optional
            Function to call when the button action is triggered.
        name : str, optional
            Name of the switch for logging purposes.

        """
        if callback is None:
            callback = self._debug_callback

        self.gpio: int
        self.callback: Callable
        self.log: Log
        thread = threading.Thread(target=self._run, args=(gpio, callback, log, detect))
        thread.daemon = True
        thread.start()

        self._name = name

    def _run(
        self,
        gpio: int,
        callback: Callable,
        log: Log,
        detect: Literal["rising", "falling", "both"],
        bouncetime: int = 5000,
    ) -> None:
        """Define the run method, invoked by ``Thread.run``."""
        self.gpio = gpio
        self.callback = callback
        self.log = log

        if self.gpio <= 0:
            return
        GPIO.setwarnings(False)

        pull_up_down, edge = pud_settings(detect)

        try:
            msg = f"Creating Switch object for GPIO {self.gpio} {detect = }"
            log.message(msg, log.DEBUG)
            GPIO.setup(self.gpio, GPIO.IN, pull_up_down=pull_up_down)
            GPIO.add_event_detect(
                self.gpio, edge, callback=self.callback_wrapper, bouncetime=bouncetime
            )
        except Exception as e:
            log.message(f"Button GPIO {self.gpio} initialise error: {e}", log.ERROR)
            sys.exit(1)

    @property
    def button(self) -> int:
        """Alias for GPIO."""
        return self.gpio

    def callback_wrapper(self, gpio: int) -> None:
        """Handle GPIO events for button presses and releases.

        Parameters
        ----------
        gpio : int
            GPIO pin number where the event occurred.

        """
        self.log.message(
            f"Event detected {self._name} pressed on GPIO {gpio}", self.log.DEBUG
        )
        # self.action_triggered = False  # Reset the action flag
        # return

        self.log.message(f"Button {self._name} released on GPIO {gpio}", self.log.DEBUG)

    def _debug_callback(self, gpio: int, state: bool) -> None:
        """Print a message when the button is pressed."""
        print(f"[DEBUG] Switch {self._name} on GPIO {gpio} changed state to {state}")


def pud_settings(detect: Literal["rising", "falling", "both"]) -> tuple[int, int]:
    """Set up pull-up resistor.

    Returns
    -------
    resistor : int
        Code for the default pull-up resistor.
    edge : int
        Code for the edge to detect.

    """
    resistor = GPIO.PUD_UP
    if detect == "rising":
        return resistor, GPIO.RISING
    if detect == "falling":
        return resistor, GPIO.FALLING
    if detect == "both":
        return resistor, GPIO.BOTH
    log.message(f"{detect = } not allowed.", level=log.ERROR)
    raise OSError(f"{detect = } not allowed.")


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

    print(f"Pull Up/Down resistors: {config.pull_up_down}")

    disco_light = DiscoLight(config.getSwitchGpio("disco_light"))

    for gpio, name, detect in zip(
        (off_gpio, fip_gpio, spotify_gpio, unused_gpio, disco_gpio),
        ("OFF", "FIP", "SPOTIFY", "UNUSED", "DISCO"),
        ("rising", "rising", "rising", "rising", "both"),
        strict=True,
    ):
        _ = Switch(
            gpio=gpio,
            log=log,
            detect=detect,
            callback=None,
            name=name,
        )

    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print(" Stopped")
        GPIO.cleanup()
        sys.exit(0)
