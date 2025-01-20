#!/usr/bin/env python3
# Raspberry Pi Button Push Button Class
# $Id: button_class.py,v 1.1 2024/12/19 15:29:57 bob Exp $
#
# Author: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#

import sys
import threading
import time
from collections.abc import Callable
from typing import Literal

import RPi.GPIO as GPIO
from constants import *
from log_class import Log

GPIO.setmode(GPIO.BCM)


class Button:

    def __init__(
        self,
        button,
        callback,
        log,
        pull_up_down=GPIO.PUD_DOWN,
    ):
        t = threading.Thread(
            target=self._run,
            args=(
                button,
                callback,
                log,
                pull_up_down,
            ),
        )
        t.daemon = True
        t.start()

    def _run(
        self,
        button: int,
        callback: Callable,
        log: Log,
        pull_up_down: str | int,
    ) -> None:
        self.button = button
        self.callback = callback
        self.pull_up_down = pull_up_down
        self.log = log

        if self.button <= 0:
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
            msg = f"Creating button object for GPIO {self.button} {sEdge = }"
            log.message(msg, log.DEBUG)
            # Enable the internal pull-up resistor
            GPIO.setup(self.button, GPIO.IN, pull_up_down=resistor)

            # Add event detection to the GPIO inputs
            GPIO.add_event_detect(
                self.button, edge, callback=self.button_event, bouncetime=200
            )
        except Exception as e:
            log.message(f"Button GPIO {self.button} initialise error: {e}", log.ERROR)
            sys.exit(1)

    def button_event(self, button: int) -> None:
        """Push button event."""
        self.log.message("Push button event GPIO " + str(button), self.log.DEBUG)
        event_button = self.button
        self.callback(event_button)  # Pass button event to event class
        return

    def pressed(self) -> bool:
        """Tell if a button was pressed.

        From 0 to 1 or from 1 to 0 depending on ``pull_up_down``.

        """
        level = 1
        if self.pull_up_down == UP:
            level = 0
        state = GPIO.input(self.button)
        if state == level:
            return True
        return False


def interrupt(gpio):
    print("Button pressed on GPIO", gpio)
    return


if __name__ == "__main__":

    from config_class import Configuration
    from log_class import Log

    config = Configuration()
    log = Log()
    if len(log.getName()) < 1:
        log.init("radio")

    pullupdown = ["DOWN", "UP"]

    print("Test Button Class")

    # Get switch configuration
    left_switch = config.getSwitchGpio("left_switch")
    right_switch = config.getSwitchGpio("right_switch")
    mute_switch = config.getSwitchGpio("mute_switch")
    down_switch = config.getSwitchGpio("down_switch")
    up_switch = config.getSwitchGpio("up_switch")
    menu_switch = config.getSwitchGpio("menu_switch")
    aux_switch1 = config.getSwitchGpio("aux_switch1")
    aux_switch2 = config.getSwitchGpio("aux_switch2")
    aux_switch3 = config.getSwitchGpio("aux_switch3")

    print("Left switch GPIO", left_switch)
    print("Right switch GPIO", right_switch)
    print("Mute switch GPIO", mute_switch)
    print("Up switch GPIO", up_switch)
    print("Down switch GPIO", down_switch)
    print("Menu switch GPIO", menu_switch)
    print("Aux switch 1 GPIO", aux_switch1)
    print("Aux switch 2 GPIO", aux_switch2)
    print("Aux switch 3 GPIO", aux_switch3)
    print("Pull Up/Down resistors", pullupdown[config.pull_up_down])

    Button(left_switch, interrupt, log, config.pull_up_down)
    Button(right_switch, interrupt, log, config.pull_up_down)
    Button(mute_switch, interrupt, log, config.pull_up_down)
    Button(down_switch, interrupt, log, config.pull_up_down)
    Button(up_switch, interrupt, log, config.pull_up_down)
    Button(menu_switch, interrupt, log, config.pull_up_down)
    Button(aux_switch1, interrupt, log, config.pull_up_down)
    Button(aux_switch2, interrupt, log, config.pull_up_down)
    Button(aux_switch3, interrupt, log, config.pull_up_down)

    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print(" Stopped")
        GPIO.cleanup()
        sys.exit(0)
