#!/usr/bin/env python3
"""Define an object to handle the set of five buttons in the front."""

import sys
import time
from collections.abc import Sequence

import RPi.GPIO as GPIO
from switch import Switch


class TeleButtons:
    """Implement five buttons.

    They are mutually exclusive: pressing one disables the previously activated
    one. Two buttons have a specific behavior:
        - The first does not stay in the down position. Used to shutdown the
        system.
        - The last does not disable the other button. Used to activate a 220V
        disco light thanks to a relay.

    """

    def __init__(self, switches: Sequence[Switch]) -> None:
        """Create object from several switches."""
        self.switches = switches

    @property
    def off(self) -> Switch:
        """Give the leftmost button."""
        return self.switches[0]

    @property
    def fip(self) -> Switch:
        """Give the 2nd button, starting from left."""
        return self.switches[1]

    @property
    def spotify(self) -> Switch:
        """Give the 3rd button, starting from left."""
        return self.switches[2]

    @property
    def unused(self) -> Switch:
        """Give the 4th button, starting from left."""
        return self.switches[3]

    @property
    def disco(self) -> Switch:
        """Give the last button."""
        return self.switches[4]


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

    kwargs = {
        "log": log,
        "pull_up_down": config.pull_up_down,
        "bouncetime": 1000,
        "callback": None,
    }
    for gpio, name in zip(
        (off_gpio, fip_gpio, spotify_gpio, unused_gpio, disco_gpio),
        ("OFF", "FIP", "SPOTIFY", "UNUSED", "DISCO"),
        strict=True,
    ):
        _ = Switch(button=gpio, name=name, **kwargs)

    try:
        while True:
            time.sleep(1.0)

    except KeyboardInterrupt:
        print(" Stopped")
        GPIO.cleanup()
        sys.exit(0)
