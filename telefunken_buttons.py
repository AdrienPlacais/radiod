#!/usr/bin/env python3
"""Define an object to handle the set of five buttons in the front."""

import sys
import time
from collections.abc import Sequence

import RPi.GPIO as GPIO
from button_class import Button, interrupt


class TeleButtons:
    """Implement five buttons.

    They are mutually exclusive: pressing one disables the previously activated
    one. Two buttons have a specific behavior:
        - The first does not stay in the down position. Used to shutdown the
        system.
        - The last does not disable the other button. Used to activate a 220V
        disco light thanks to a relay.

    """

    def __init__(self, buttons: Sequence[Button]) -> None:
        """Create object from several buttons."""
        self.buttons = buttons

    @property
    def off(self) -> Button:
        """Give the leftmost button."""
        return self.buttons[0]

    @property
    def fip(self) -> Button:
        """Give the 2nd button, starting from left."""
        return self.buttons[1]

    @property
    def spotify(self) -> Button:
        """Give the 3rd button, starting from left."""
        return self.buttons[2]

    @property
    def unused(self) -> Button:
        """Give the 4th button, starting from left."""
        return self.buttons[3]

    @property
    def disco(self) -> Button:
        """Give the last button."""
        return self.buttons[4]


if __name__ == "__main__":
    from config_class import Configuration
    from log_class import Log

    config = Configuration()
    log = Log()
    if len(log.getName()) < 1:
        log.init("radio")

    pullupdown = ["DOWN", "UP"]

    print("Test TelefunkenButtons class")

    # Get switch configuration
    off_switch = config.getSwitchGpio("off_switch")
    fip_switch = config.getSwitchGpio("fip_switch")
    spotify_switch = config.getSwitchGpio("spotify_switch")
    unused_switch = config.getSwitchGpio("unused_switch")
    disco_switch = config.getSwitchGpio("disco_switch")

    print(f"off_switch GPIO: {off_switch}")
    print(f"fip_switch GPIO: {fip_switch}")
    print(f"spotify_switch GPIO: {spotify_switch}")
    print(f"unused_switch GPIO: {unused_switch}")
    print(f"disco_switch GPIO: {disco_switch}")

    Button(off_switch, interrupt, log, config.pull_up_down)
    Button(fip_switch, interrupt, log, config.pull_up_down)
    Button(spotify_switch, interrupt, log, config.pull_up_down)
    Button(unused_switch, interrupt, log, config.pull_up_down)
    Button(disco_switch, interrupt, log, config.pull_up_down)

    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print(" Stopped")
        GPIO.cleanup()
        sys.exit(0)
