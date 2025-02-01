#!/usr/bin/env python3
"""Define a ON/OFF light."""

import sys
import time
from typing import Literal

import RPi.GPIO as GPIO


class DiscoLight:
    OFF = 0
    ON = 1

    status: Literal[0, 1] = 0

    def __init__(self, gpio: int = 26) -> None:
        """Instantiate object and associate GPIO pin."""
        self.gpio = gpio

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        if self.gpio > 0:
            GPIO.setup(self.gpio, GPIO.OUT)
            self.set(self.OFF)

    def __str__(self) -> str:
        """Return info on object."""
        return f"DiscoLight({self.gpio = }), currently {self.status}"

    def set(self, status: Literal[0, 1]) -> Literal[0, 1]:
        """Change state of light."""
        if status is self.status:
            return status

        if self.gpio < 0:
            return status

        if status not in (self.OFF, self.ON):
            print(f"{status = } is invalid.")
            return status

        if status is self.ON:
            GPIO.output(self.gpio, True)
        elif status is self.OFF:
            GPIO.output(self.gpio, False)
        self.status = status
        return status

    def get(self) -> Literal[0, 1]:
        """Get current status of light."""
        return self.status


if __name__ == "__main__":
    disco_light = DiscoLight(gpio=26)
    print("Test disco light, press Ctrl-C to stop")
    print(str(disco_light))
    print("")
    try:
        while True:
            print("ON")
            disco_light.set(disco_light.ON)
            time.sleep(2)
            print("OFF")
            disco_light.set(disco_light.OFF)
            time.sleep(2)
    except KeyboardInterrupt:
        disco_light.set(disco_light.OFF)
        print("\nExit")
        sys.exit(0)
