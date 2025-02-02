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
        pull_up_down: Literal["UP", "DOWN"] = "UP",
        callback: Callable | None = None,
        name: str = "",
        invert_logic: bool = True,
        press_duration: float = 0.1,
        disco_light: DiscoLight | None = None,
        disco_activator: bool = False,
    ) -> None:
        """
        Initialize the Switch object.

        Parameters
        ----------
        gpio : int
            GPIO pin number for the switch.
        log : Log
            Logging object for messages.
        pull_up_down : str, optional
            Pull resistor configuration: "UP" or "DOWN".
        callback : Callable, optional
            Function to call when the button action is triggered.
        stable_time : float, optional
            Time in seconds for the state to stabilize. Default is 0.05.
        name : str, optional
            Name of the switch for logging purposes.
        invert_logic : bool, optional
            If True, inverts the ON/OFF logic. Default is True.
        press_duration : float, optional
            Minimum time the button must be pressed to trigger the action in
            seconds.
        disco_light : DiscoLight | None, optional
            The disco light, that is turned OFF when another button is pressed.
        disco_activator : bool, optional
            If current object triggers the disco light.

        """
        if callback is None:
            callback = self._debug_callback

        self.gpio: int

        t = threading.Thread(target=self._run, args=(gpio, callback, log, pull_up_down))
        t.daemon = True
        t.start()

        self._name = name
        self.state = False if name != "OFF" else True
        self.press_duration = press_duration
        self.last_press_time = None
        self.action_triggered = False
        self.invert_logic = invert_logic
        self._disco_light = disco_light
        self._is_disco_activator = disco_activator

        self._polling_thread = threading.Thread(
            target=self._poll_press_duration, daemon=True
        )
        self._polling_thread.start()

    def _run(
        self,
        gpio: int,
        callback: Callable,
        log: Log,
        pull_up_down: str | int,
    ) -> None:
        """Define the run method."""
        self.gpio = gpio
        self.callback = callback
        self.pull_up_down = pull_up_down
        self.log = log

        if self.gpio <= 0:
            return
        GPIO.setwarnings(False)

        if pull_up_down in ("DOWN", "down", 0):
            resistor = GPIO.PUD_DOWN
            edge = GPIO.RISING
            sEdge = "Rising"
        elif pull_up_down in ("UP", "up", 1):
            resistor = GPIO.PUD_UP
            edge = GPIO.FALLING
            sEdge = "Falling"
        else:
            log.message(f"{pull_up_down = } is invalid.", log.ERROR)

        try:
            msg = f"Creating button object for GPIO {self.gpio} {sEdge = }"
            log.message(msg, log.DEBUG)
            GPIO.setup(self.gpio, GPIO.IN, pull_up_down=resistor)
            GPIO.add_event_detect(self.gpio, edge, callback=self.event, bouncetime=200)
        except Exception as e:
            log.message(f"Button GPIO {self.gpio} initialise error: {e}", log.ERROR)
            sys.exit(1)

    @property
    def button(self) -> int:
        """Alias for GPIO."""
        return self.gpio

    def event(self, gpio: int) -> None:
        """Handle GPIO events for button presses and releases.

        Parameters
        ----------
        gpio : int
            GPIO pin number where the event occurred.

        """
        print(f"Switch event at {gpio = }")
        state = GPIO.input(gpio)
        is_pressed = not state if self.invert_logic else state

        if is_pressed:
            self.log.message(
                f"Switch {self._name} pressed on GPIO {gpio}", self.log.DEBUG
            )
            self.last_press_time = time.time()
            self.action_triggered = False  # Reset the action flag
            return

        self.log.message(f"Button {self._name} released on GPIO {gpio}", self.log.DEBUG)
        self.last_press_time = None

    def _switch_disco_light(self) -> None:
        """Turn ON/OFF the disco light if necessary."""
        if self._disco_light is None:
            return
        if self._is_disco_activator:
            self.log.message(f"Disco light is turned on.", self.log.DEBUG)
            print(f"Disco light is turned on.")
            self._disco_light.set(self._disco_light.ON)
            return
        self.log.message(f"Disco light is turned off.", self.log.DEBUG)
        print(f"Disco light is turned off.")
        self._disco_light.set(self._disco_light.OFF)

    def _poll_press_duration(self) -> None:
        """
        Poll the press duration and trigger the action if the button is held
        for the required time.
        """
        while True:
            if self.last_press_time and not self.action_triggered:
                elapsed_time = time.time() - self.last_press_time
                if elapsed_time >= self.press_duration:
                    self.action_triggered = (
                        True  # Ensure the action is triggered only once
                    )
                    self.log.message(
                        f"Button {self._name} held for {elapsed_time:.2f} seconds, triggering action.",
                        self.log.INFO,
                    )
                    self.callback(self.gpio, True)  # Call the callback
            time.sleep(0.05)  # Polling interval

    def pressed(self) -> bool:
        """Check if the button is currently pressed.

        Returns
        -------
        bool
            True if the button is pressed, False otherwise.

        """
        state = GPIO.input(self.gpio)
        return not state if self.invert_logic else state

    def _debug_callback(self, gpio: int, state: bool) -> None:
        """Print a message when the button is pressed."""
        print(f"[DEBUG] Switch {self._name} on GPIO {gpio} changed state to {state}")


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

    for gpio, name in zip(
        (off_gpio, fip_gpio, spotify_gpio, unused_gpio, disco_gpio),
        ("OFF", "FIP", "SPOTIFY", "UNUSED", "DISCO"),
        strict=True,
    ):
        _ = Switch(
            gpio=gpio,
            log=log,
            callback=None,
            pull_up_down=config.pull_up_down,
            name=name,
            disco_light=disco_light,
            disco_activator=True if name == "DISCO" else False,
        )

    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print(" Stopped")
        GPIO.cleanup()
        sys.exit(0)
