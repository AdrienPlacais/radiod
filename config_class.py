#!/usr/bin/env python3
# Raspberry Pi Internet Radio Configuration Class
# $Id: config_class.py,v 1.101 2024/06/21 06:27:42 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class reads the /etc/radiod.conf file for configuration parameters
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import configparser
import os
import pdb
import sys
from typing import Literal

import RPi.GPIO as GPIO
from constants import *
from log_class import Log

# System files
ConfigFile = "/etc/radiod.conf"
Airplay = "/usr/local/bin/shairport-sync"

log = Log()
config = configparser.ConfigParser(interpolation=None)


class Configuration:
    # Input source
    RADIO = 0
    PLAYER = 1
    AIRPLAY = 2

    """
    Station name source. LIST= from stationlist file 
    or STREAM from radio stream
    """
    LIST = 0
    STREAM = 1

    _stationNamesSource = ["list", "stream"]

    # Display types
    NO_DISPLAY = 0  # No screen attached
    LCD = 1  # Directly connected LCD
    LCD_I2C_PCF8574 = 2  # LCD PCF8574 I2C backpack
    LCD_I2C_ADAFRUIT = 3  # Adafruit I2C LCD backpack
    LCD_ADAFRUIT_RGB = 4  # Adafruit RGB plate
    GRAPHICAL_DISPLAY = 5  # Graphical or touchscreen  display
    OLED_128x64 = 6  # OLED 128 by 64 pixels
    PIFACE_CAD = 7  # Piface CAD
    ST7789TFT = 8  # Pirate audio TFT with ST7789 controller
    SSD1306 = 9  # Sitronix SSD1306 controller for the 128x64 tft
    SH1106_SPI = 10  # SH1106_SPI controller for Waveshare 1.3" 128x64 tft
    LUMA = 11  # Luma driver for  most OLEDs
    LCD_I2C_JHD1313 = 12  # Grove 2x16 I2C LCD RGB

    display_type = LCD
    DisplayTypes = [
        "NO_DISPLAY",
        "LCD",
        "LCD_I2C_PCF8574",
        "LCD_I2C_ADAFRUIT",
        "LCD_ADAFRUIT_RGB",
        "GRAPHICAL_DISPLAY",
        "OLED_128x64",
        "PIFACE_CAD",
        "ST7789TFT",
        "SSD1306",
        "SH1106_SPI",
        "LUMA",
        "LCD_I2C_JHD1313",
    ]

    # User interface ROTARY or BUTTONS
    ROTARY_ENCODER = 0
    BUTTONS = 1
    GRAPHICAL = 2
    COSMIC_CONTROLLER = 3  # IQAudio cosmic controller
    PIFACE_BUTTONS = 4  # PiFace CAD buttons
    ADAFRUIT_RGB = 5  # Adafruit RGB I2C 5 button interface
    TELEFUNKEN = 5  # my config
    _user_interface = TELEFUNKEN

    UserInterfaces = [
        "ROTARY_ENCODER",
        "BUTTONS",
        "GRAPHICAL",
        "COSMIC_CONTROLLER",
        "PIFACE_BUTTONS",
        "ADAFRUIT_RGB",
        "TELEFUNKEN",
    ]

    # Rotary class selection
    STANDARD = 0  # Select rotary_class.py
    ALTERNATIVE = 1  # Select rotary_class_alternate.py
    RGB_ROTARY = 2  # Select rotary_class_rgb.py
    RGB_I2C_ROTARY = 3  # Select rotary_class_rgb_i2c.py

    # Configuration parameters accesible through @property and @<parameter>.setter
    _mpdport = 6600  # MPD port number
    _client_timeout = 10  # MPD client timeout in secons 3 to 15 seconds
    _dateformat = "%H:%M %d/%m/%Y"  # Date format
    _volume_range = 100  # Volume range 10 to 100
    _volume_increment = 1  # Volume increment 1 to 10
    _display_playlist_number = False  # Two line displays only, display station(n)
    _source = RADIO  # Source RADIO or MEDIA Player
    _rotary_class = STANDARD  # Rotary class STANDARD,RGB_ROTARY or ALTERNATIVE
    _rotary_step_size = (
        False  # Rotary full step (False) or half step (True) configuration
    )
    _rotary_gpio_pullup = GPIO.PUD_UP  # KY-040 encoders have own 10K pull-up resistors.
    # Set internal pullups to off with rotary_gpio_pullup = GPIO.PUD_OFF
    _volume_rgb_i2c = 0x0F  # Volume RGB I2C Rotary encoder hex address
    _channel_rgb_i2c = 0x1F  # Channel RGB I2C Rotary encoder hex address
    _display_width = 0  # Line width of display width 0 = use program default
    _display_lines = 2  # Number of display lines
    _scroll_speed = float(0.3)  # Display scroll speed (0.01 to 0.3)
    _airplay = False  # Use airplay
    _mixer_preset = 0  # Mixer preset volume (0 disable setting as MPD controls it)
    _audio_out = ""  # Audio device string such as headphones, HDMI or DAC
    _audio_config_locked = True  # Don't allow dynamic updating of audio configuration
    _display_blocks = False  # Display volume in blocks
    _startup_playlist = ""  # Startup playlist RADIO,MEDIA,LAST or specific playlist
    _load_last = False  # Load the last playlist played. Set by startup_playlist=LAST
    _screen_saver = 0  # Screen saver time n minutes, 0 = No screen save
    _flip_display_vertically = False  # Flip OLED display vertically
    _station_names = LIST  # Station names from playlist names or STREAM
    _update_playlists = False  # Allow update of playlists by external clients
    _mute_action = 0  # MPD action on mute, 1=pause, 2=stop, 0=volume off only
    MuteActions = ["Pause", "Stop"]  # Text for above _mute_action

    # Remote control parameters
    _remote_led = 0  # Remote Control activity LED 0 = No LED
    _remote_control_host = "localhost"  # Remote control to radio communication host
    _remote_control_port = 5100  # Remote control to radio communication port
    _remote_listen_host = (
        "localhost"  # Address (locahost) or IP adress of remote UDP server
    )
    _keytable = "myremote.toml"  # IR event daemon keytable name

    _i2c_address = 0x00  # Use defaults or use setting in radiod.conf
    _i2c_bus = 1  # The I2C bus is normally 1
    _speech = False  # Speech on for visually impaired or blind persons
    _speak_info = False  # If speach enable also speak info (IP address and hostname)
    _speech_volume = 80  # Percentage speech volume
    _verbose = False  # Extra speech verbosity
    _logfile_truncate = False  # Truncate logfile otherwise tail the file
    _shutdown = True  # Shutdown when exiting radio
    _execute = ""  # Execute this parameter when exiting radio
    _comitup_ip = "10.41.0.1"  # Comitup initial IP address.
    _pivumeter = False  # Pimoroni Pivumeter

    # Shoutcast ID
    _shoutcast_key = "anCLSEDQODrElkxl"

    # Internet check URL and port number
    _internet_check_url = "google.com"
    _internet_check_port = 80
    _internet_timeout = 10
    _bluetooth_device = "00:00:00:00:00:00"  # Bluetooth device ID

    # Cyrillic Romanization
    _romanize = True  # Romanize language(convert to Latin). e.g. Russian
    _codepage = 0  # LCD font page 0,1,2 depending upon make of LCD
    _language = "English"  # Translation table in /usr/share/radio/fonts eg Russian
    _controller = (
        "HD44780U"  # LCD/OLED controller type (LCD can have multiple code pages)
    )
    _translate_lcd = True  # Translate characters for LCD display
    # True for latin character LCDs.
    # False for Russian/Cyrillic character LCDs

    # Graphics screen default parameters [SCREEN] section
    _fullscreen = True  # Graphics screen fullscreen yes no
    _window_title = "Bob Rathbone Internet Radio %V - %H"  # Window title
    _window_color = "blue"  # Graphics screen background colour
    _labels_color = "white"  # Graphics screen labels colour
    _display_window_color = "navy"  # Display window background colour
    _display_window_labels_color = "white"  # Display window labels colour
    _display_mouse = False  # Hide mouse
    _switch_programs = False  # Allow switch between gradio and vgradio
    _slider_color = "red"  # Search window slider default colour
    _banner_color = "white"  # Time banner text colour
    _wallpaper = ""  # Background wallpaper
    _graphic_dateformat = "%H:%M:%S %A %e %B %Y"  # Format for graphic screen
    _display_shutdown_button = True  # Shutdown button
    _shutdown_command = "sudo shutdown -h now"  # Shutdown command
    _display_icecast_button = False  # Display Icecast button

    # Parameters specific to the vintage graphic radio
    _scale_labels_color = "white"  # Vintage screen labels colour
    _stations_per_page = 50  # maximum stations per page
    _display_date = True  # Display time and date
    _display_title = True  # Display title play (at bottom of screen)
    _splash_screen = "bitmaps/raspberry-pi-logo.bmp"  # Splash screen (OLED)
    _screen_size = (800, 480)  # Screen size 800x480 (7 inch) or 720x480 (3.5 inch)
    # Colours for Adafruit LCD
    color = {
        "OFF": 0x0,
        "RED": 0x1,
        "GREEN": 0x2,
        "YELLOW": 0x3,
        "BLUE": 0x4,
        "VIOLET": 0x5,
        "TEAL": 0x6,
        "WHITE": 0x7,
    }

    # These are for the Adafruit RGB plate and for not any graphics screen
    colorName = {
        0: "Off",
        1: "Red",
        2: "Green",
        3: "Yellow",
        4: "Blue",
        5: "Violet",
        6: "Teal",
        7: "White",
    }

    # These are for the Adafruit RGB plate and not for any graphics screen
    # Adfafruit uses color codes 0 to 7 and not RGB
    colors = {
        "bg_color": 0x0,
        "mute_color": 0x0,
        "shutdown_color": 0x0,
        "error_color": 0x0,
        "search_color": 0x0,
        "source_color": 0x0,
        "info_color": 0x0,
        "menu_color": 0x0,
        "sleep_color": 0x0,
    }

    # These for LCDs such as the Grove LCD which uses RGB colors
    rgbcolors = {
        "bg_color": "WHITE",
        "mute_color": "VIOLET",
        "shutdown_color": "TEAL",
        "error_color": "RED",
        "search_color": "GREEN",
        "source_color": "TEAL",
        "info_color": "BLUE",
        "menu_color": "YELLOW",
        "sleep_color": "BLACK",
    }

    # List of loaded options for display
    configOptions = {}

    #  GPIOs for switches and rotary encoder configuration (40 pin wiring)
    _switch_gpio = 0  # Switch GPIO
    switches = {
        "menu_switch": 17,
        "mute_switch": 22,
        "left_switch": 14,
        "right_switch": 15,
        "up_switch": 24,
        "down_switch": 23,
        "aux_switch1": 0,
        "aux_switch2": 0,
        "aux_switch3": 0,
        "off_switch": 0,
        "fip_switch": 0,
        "spotify_switch": 0,
        "unused_switch": 0,
        "disco_switch": 0,
    }
    _disco_light = 0

    # Pull up/down resistors (For button class only)
    _pull_up_down = DOWN  # Default

    # Values for the rotary switch on vintage radio (Not rotary encoders)
    # Zero values disable usage
    menu_switches = {
        "menu_switch_value_1": 0,  # Normally 24
        "menu_switch_value_2": 0,  # Normally 8
        "menu_switch_value_4": 0,  # Normally 7
    }

    # RGB LED definitions for vintage radio
    # Zero values disable usage
    rgb_leds = {
        "rgb_green": 0,  # Normally 27
        "rgb_blue": 0,  # Normally 22
        "rgb_red": 0,  # Normally 23
    }

    #  GPIOs for LCD connections
    lcdconnects = {
        "lcd_enable": 0,
        "lcd_select": 0,
        "lcd_data4": 0,
        "lcd_data5": 0,
        "lcd_data6": 0,
        "lcd_data7": 0,
    }

    # Initialisation routine
    def __init__(self):
        log.init("radio")
        if not os.path.isfile(ConfigFile) or os.path.getsize(ConfigFile) == 0:
            log.message("Missing configuration file " + ConfigFile, log.ERROR)
        else:
            self.getConfig()

        return

    # Get configuration options from /etc/radiod.conf
    def getConfig(self):
        section = "RADIOD"

        # Get options from /etc/radiod.conf
        # Parameter for each option is passed to the @property setter for that option
        config.read(ConfigFile)
        try:
            options = config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section, option)

                self.configOptions[option] = parameter

                if option == "loglevel":
                    next

                elif option == "codecs":
                    next

                elif option == "volume_range":
                    range = 100
                    try:
                        range = int(parameter)
                        if range < 10:
                            range = 10
                        if range > 100:
                            range = 100
                        self.volume_range = range
                        self.volume_increment = int(100 / range)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "user_interface":
                    self.user_interface = parameter

                elif option == "remote_led":
                    try:
                        self.remote_led = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "remote_control_host":
                    self.remote_control_host = parameter

                elif option == "remote_control_port":
                    try:
                        self.remote_control_port = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "remote_listen_host":
                    self.remote_listen_host = parameter

                elif option == "keytable":
                    self.keytable = parameter

                elif option == "mpdport":
                    try:
                        self.mpdport = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "client_timeout":
                    try:
                        self.client_timeout = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "dateformat":
                    self.dateformat = parameter

                elif option == "keytable":
                    self.keytable = parameter

                elif option == "display_playlist_number":
                    self.display_playlist_number = self.convertYesNo(parameter)

                elif option == "station_names":
                    self.station_names = parameter

                elif option == "flip_display_vertically":
                    self.flip_display_vertically = parameter

                elif option == "splash":
                    self.splash_screen = parameter

                elif option == "startup":
                    self.startup_playlist = parameter

                elif option == "i2c_address":
                    try:
                        self.i2c_address = int(parameter, 16)
                    except Exception as e:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "i2c_bus":
                    try:
                        value = int(parameter)
                        if value > 0 or parameter <= 1:
                            self.i2c_bus = value
                        else:
                            self.invalidParameter(ConfigFile, option, parameter)

                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif "_color" in option:
                    self.rgbcolors[option] = parameter
                    try:
                        self.colors[option] = self.color[parameter]
                    except:
                        pass

                elif option == "speech":
                    self.speech = parameter

                elif option == "verbose":
                    self.verbose = parameter

                elif option == "speak_info":
                    self.speak_info = parameter

                elif option == "volume_display":
                    self.display_blocks = parameter

                elif option == "speech_volume":
                    try:
                        self.speech_volume = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "pull_up_down":
                    if parameter == "up":
                        self.pull_up_down = UP
                    else:
                        self.pull_up_down = DOWN

                elif "_switch" in option and not "menu_switch_value" in option:
                    try:
                        self.switches[option] = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif "display_width" in option:
                    try:
                        self.display_width = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif "display_lines" in option:
                    try:
                        self.display_lines = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif "scroll_speed" in option:
                    try:
                        self.scroll_speed = float(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif "codepage" in option:
                    try:
                        self.codepage = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif "lcd_" in option:
                    try:
                        lcdconnect = int(parameter)
                        self.lcdconnects[option] = lcdconnect
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif (
                    option == "rgb_red" or option == "rgb_green" or option == "rgb_blue"
                ):
                    try:
                        led = int(parameter)
                        self.rgb_leds[option] = led
                    except:
                        msg = "Invalid RGB LED connect parameter " + option
                        log.message(msg, log.ERROR)

                elif "menu_switch_value_" in option:
                    try:
                        menuswitch = int(parameter)
                        self.menu_switches[option] = menuswitch
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif "display_type" in option:
                    self.display_type = self.LCD  # Default

                    if parameter == "LCD":
                        self.display_type = self.LCD

                    elif parameter == "LCD_I2C_PCF8574":
                        self.display_type = self.LCD_I2C_PCF8574

                    elif parameter == "LCD_I2C_ADAFRUIT":
                        self.display_type = self.LCD_I2C_ADAFRUIT

                    elif parameter == "LCD_ADAFRUIT_RGB":
                        self.display_type = self.LCD_ADAFRUIT_RGB

                    elif parameter == "NO_DISPLAY":
                        self.display_type = self.NO_DISPLAY

                    elif parameter == "GRAPHICAL":
                        self.display_type = self.GRAPHICAL_DISPLAY

                    elif parameter == "OLED_128x64":
                        self.display_type = self.OLED_128x64

                    elif parameter == "PIFACE_CAD":
                        self.display_type = self.PIFACE_CAD

                    elif parameter == "ST7789TFT":
                        self.display_type = self.ST7789TFT

                    elif parameter == "SSD1306":
                        self.display_type = self.SSD1306

                    elif parameter == "SH1106_SPI":
                        self.display_type = self.SH1106_SPI

                    elif parameter == "LCD_I2C_JHD1313":
                        self.display_type = self.LCD_I2C_JHD1313

                    elif "LUMA" in parameter:
                        param = parameter.upper()
                        self.display_type = self.LUMA
                        self.luma_device = "SH1106"  # Default
                        luma_devices = param.split(".")
                        if len(luma_devices) > 0:
                            self.luma_device = luma_devices[1]

                    else:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "rotary_class":
                    if parameter == "alternative":
                        self.rotary_class = self.ALTERNATIVE
                    elif parameter == "rgb_rotary":
                        self.rotary_class = self.RGB_ROTARY
                    elif parameter == "rgb_i2c_rotary":
                        self.rotary_class = self.RGB_I2C_ROTARY
                    else:
                        self.rotary_class = self.STANDARD

                elif option == "rotary_gpio_pullup":
                    if parameter == "none":
                        self.rotary_gpio_pullup = GPIO.PUD_OFF
                    else:
                        self.rotary_gpio_pullup = GPIO.PUD_UP

                elif option == "rotary_step_size":
                    self.rotary_step_size = parameter

                elif option == "exit_action":
                    self.shutdown = parameter

                elif option == "log_creation_mode":
                    self.log_creation_mode = parameter

                elif option == "shoutcast_key":
                    self.shoutcast_key = parameter

                elif option == "internet_check_url":
                    self.internet_check_url = parameter

                elif option == "internet_check_port":
                    try:
                        self.internet_check_port = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "internet_timeout":
                    try:
                        self.internet_timeout = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "bluetooth_device":
                    self.bluetooth_device = parameter

                elif option == "mute_action":
                    self.mute_action = parameter

                elif option == "update_playlists":
                    self.update_playlists = parameter

                elif option == "translate_lcd":
                    self.translate_lcd = parameter

                elif option == "language":
                    self.language = parameter

                elif option == "controller":
                    self.controller = parameter

                elif option == "romanize":
                    self.romanize = parameter

                elif option == "audio_out":
                    self.audio_out = parameter

                elif option == "audio_config_locked":
                    self.audio_config_locked = parameter

                elif option == "comitup_ip":
                    self.comitup_ip = parameter

                elif option == "volume_rgb_i2c":
                    self.volume_rgb_i2c = parameter

                elif option == "channel_rgb_i2c":
                    self.channel_rgb_i2c = parameter

                elif option == "shutdown_command":
                    self.shutdown_command = parameter

                elif option == "pivumeter":
                    self.pivumeter = parameter

                elif option == "disco_light":
                    try:
                        self.disco_light = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                else:
                    msg = f"Invalid {option = } in {section = } in {ConfigFile})"
                    log.message(msg, log.ERROR)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section), "in", ConfigFile
            log.message(msg, log.ERROR)

        # Read Airplay parameters
        section = "AIRPLAY"

        # Get options
        config.read(ConfigFile)
        try:
            options = config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section, option)

                self.configOptions[option] = parameter

                if option == "airplay":
                    self.airplay = parameter

                # Name has been changed from mixer_volume to mixer_preset in v6.7
                elif option == "mixer_volume" or option == "mixer_preset":
                    try:
                        volume = int(parameter)
                        self.mixer_preset = volume
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "mixer_volume_id":
                    next  # No longer used

                else:
                    msg = (
                        "Invalid option "
                        + option
                        + " in section "
                        + section
                        + " in "
                        + ConfigFile
                    )
                    log.message(msg, log.ERROR)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section), "in", ConfigFile
            log.message(msg, log.WARNING)

        section = "SCREEN"
        # Get options
        config.read(ConfigFile)
        try:
            options = config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section, option)

                self.configOptions[option] = parameter

                if option == "screen_size":
                    self.screen_size = parameter

                elif option == "fullscreen":
                    self.fullscreen = parameter

                elif option == "window_color":
                    self.window_color = parameter

                elif option == "window_title":
                    self.window_title = parameter

                elif option == "banner_color":
                    self.banner_color = parameter

                elif option == "labels_color":
                    self.labels_color = parameter

                elif option == "scale_labels_color":
                    self.scale_labels_color = parameter

                elif option == "display_window_color":
                    self.display_window_color = parameter

                elif option == "display_window_labels_color":
                    self.display_window_labels_color = parameter

                elif option == "slider_color":
                    self.slider_color = parameter

                elif option == "stations_per_page":
                    try:
                        self.stations_per_page = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile, option, parameter)

                elif option == "screen_saver":
                    self.screen_saver = int(parameter)

                elif option == "wallpaper":
                    self.wallpaper = parameter

                elif option == "dateformat" or option == "graphic_dateformat":
                    self.graphic_dateformat = parameter

                elif option == "display_mouse":
                    self.display_mouse = parameter

                elif option == "switch_programs":
                    self.switch_programs = parameter

                elif option == "display_date":
                    self.display_date = parameter

                elif option == "display_title":
                    self.display_title = parameter

                elif option == "display_shutdown_button":
                    self.display_shutdown_button = parameter

                elif option == "display_shutdown_button":
                    self.display_shutdown_button = parameter

                elif option == "display_icecast_button":
                    self.display_icecast_button = parameter

                else:
                    msg = (
                        "Invalid option "
                        + option
                        + " in section "
                        + section
                        + " in "
                        + ConfigFile
                    )
                    log.message(msg, log.ERROR)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section), "in", ConfigFile
            log.message(msg, log.WARNING)
        return

    # Convert yes/no to True/False
    def convertYesNo(self, parameter: Literal["yes", "no"]) -> bool:
        if parameter == "yes":
            return True
        return False

    # Convert On/Off to True/False
    def convertOnOff(self, parameter):
        true_false = False
        if parameter == "on":
            true_false = True
        return true_false

    def invalidParameter(self, ConfigFile: str, option: str, parameter: str) -> None:
        """Log an invalid parameter message."""
        log.message(f"Invalid {parameter = } in {option = } in {ConfigFile}", log.ERROR)

    # Get I2C backpack address
    @property
    def i2c_address(self):
        return self._i2c_address

    @i2c_address.setter
    def i2c_address(self, value):
        if value > 0x0:
            self._i2c_address = value

    # Get I2C bus number
    @property
    def i2c_bus(self):
        return self._i2c_bus

    @i2c_bus.setter
    def i2c_bus(self, value):
        if value > 0x0:
            self._i2c_bus = value

    # Get the volume range
    @property
    def volume_range(self):
        return self._volume_range

    @volume_range.setter
    def volume_range(self, value):
        self._volume_range = value

    # Get the volume increment
    @property
    def volume_increment(self):
        return self._volume_increment

    @volume_increment.setter
    def volume_increment(self, value):
        self._volume_increment = value

    # Display volume as text or blocks
    @property
    def display_blocks(self):
        return self._display_blocks

    @display_blocks.setter
    def display_blocks(self, parameter):
        if parameter == "blocks":
            self._display_blocks = True
        else:
            self._display_blocks = False

    # Get the remote control activity LED number
    @property
    def remote_led(self):
        return self._remote_led

    @remote_led.setter
    def remote_led(self, value):
        self._remote_led = value

    # Get the remote Host, default localhost
    @property
    def remote_control_host(self):
        return self._remote_control_host

    @remote_control_host.setter
    def remote_control_host(self, value):
        self._remote_control_host = value

    # Get the UDP server listener IP Host default localhost
    # or 0.0.0.0 for all interfaces
    @property
    def remote_listen_host(self):
        return self._remote_listen_host

    @remote_listen_host.setter
    def remote_listen_host(self, host):
        self._remote_listen_host = host

    # Get the remote Port  default 5100
    @property
    def remote_control_port(self):
        return self._remote_control_port

    @remote_control_port.setter
    def remote_control_port(self, port):
        self._remote_control_port = port

    # Get the mpdport
    @property
    def mpdport(self):
        return self._mpdport

    @mpdport.setter
    def mpdport(self, value):
        self._mpdport = value

    # Get the date format for graphic screen
    @property
    def graphic_dateformat(self):
        return self._graphic_dateformat

    @graphic_dateformat.setter
    def graphic_dateformat(self, parameter):
        self._graphic_dateformat = parameter

    # Get display playlist number (Two line displays only)
    @property
    def display_playlist_number(self):
        return self._display_playlist_number

    @display_playlist_number.setter
    def display_playlist_number(self, value):
        self._display_playlist_number = value

    # Get the startup source 0=RADIO or 1=MEDIA
    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, parameter):
        self._source = parameter

    # Get load last playlist option
    @property
    def load_last(self):
        return self._load_last

    @load_last.setter
    def load_last(self, parameter):
        self._load_last = self.convertYesNo(parameter)

    # Get the remote UDP communication port default 5100
    def remote_control_port(self):
        return self._remote_control_port

    @remote_control_host.setter
    def remote_control_host(self, host):
        self._remote_control_port = host

    # Get MPD Client Timeout 2 to 15 seconds (default 5)
    @property
    def client_timeout(self):
        return self._client_timeout

    @client_timeout.setter
    def client_timeout(self, value):
        # Value 2 to 15
        if value < 2:
            value = 2
        elif value > 15:
            value = 15
        self._client_timeout = value

    # IR event daemon keytable name
    @property
    def keytable(self):
        return self._keytable

    @keytable.setter
    def keytable(self, keytable):
        self._keytable = keytable

    # Get the date format
    @property
    def dateformat(self):
        return self._dateformat

    @dateformat.setter
    def dateformat(self, value):
        self._dateformat = value

    # Get the startup source name RADIO or MEDIA
    @property
    def source_name(self):
        source_name = "MEDIA"
        if self.source < 1:
            source_name = "RADIO"
        return source_name

    @source_name.setter
    def source_name(self, parameter):
        self._source_name = parameter

    # Get the background color (Integer)
    def getBackColor(self, sColor):
        color = 0x0
        try:
            color = self.colors[sColor]
        except:
            log.message("Invalid option " + sColor, log.ERROR)
        return color

    # Get the background color (color format (r,g,b))
    # Used by Grove LCD RGB
    def getRgbColor(self, sColor):
        rgbcolor = self.rgbcolors[sColor]
        return rgbcolor

    # Get the background colour string name
    def getBackColorName(self, iColor):
        sColor = "None"
        try:
            sColor = self.colorName[iColor]
        except:
            log.message("Invalid option " + int(iColor), log.ERROR)
        return sColor

    # Get speech
    @property
    def speech(self):
        return self._speech

    @speech.setter
    def speech(self, parameter):
        self._speech = self.convertYesNo(parameter)

    # speech verbose - Speak hostname and IP address
    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, parameter):
        self._verbose = self.convertYesNo(parameter)

    # Get verbose

    # Get verbose
    @property
    def speak_info(self):
        return self._speak_info

    @speak_info.setter
    def speak_info(self, parameter):
        self._speak_info = self.convertYesNo(parameter)

    # Get speech volume % of normal volume level
    @property
    def speech_volume(self):
        return self._speech_volume

    @speech_volume.setter
    def speech_volume(self, value):
        self._speech_volume = value

    # Display parameters
    def display(self):
        for option in sorted(self.configOptions):
            param = self.configOptions[option]
            if option != "None":
                log.message(option + " = " + param, log.DEBUG)
        return

    # Return the ID of the rotary class to be used STANDARD or ALTERNATIVE
    @property
    def rotary_class(self):
        return self._rotary_class

    @rotary_class.setter
    def rotary_class(self, value):
        self._rotary_class = value

    # Set rotary class step size to half (True) or full (False)
    @property
    def rotary_step_size(self):
        return self._rotary_step_size

    @rotary_step_size.setter
    def rotary_step_size(self, value):
        if value == "half":
            self._rotary_step_size = True
        else:
            self._rotary_step_size = False

    # Get rotary encoder pull-up resistor configuration
    @property
    def rotary_gpio_pullup(self):
        return self._rotary_gpio_pullup

    @rotary_gpio_pullup.setter
    def rotary_gpio_pullup(self, value):
        self._rotary_gpio_pullup = value

    # Returns the switch GPIO configuration by label
    @property
    def switch_gpio(self):
        return self._switch_gpio

    @switch_gpio.setter
    def switch_gpio(self, label):
        switch = -1
        try:
            self._switch_gpio = self.switches[label]
        except:
            msg = "Invalid switch label " + label
            log.message(msg, log.ERROR)

    def getSwitchGpio(self, switch_label) -> int:
        self.switch_gpio = switch_label
        return self.switch_gpio

    # Returns the LCD GPIO configuration by label
    def getLcdGpio(self, label):
        lcdconnect = -1
        try:
            lcdconnect = self.lcdconnects[label]
        except:
            msg = "Invalid LCD connection label " + label
            log.message(msg, log.ERROR)
        return lcdconnect

    # Get the RGB Led configuration by label (Retro radio only)
    def getRgbLed(self, label):
        led = -1
        try:
            led = self.rgb_leds[label]
        except:
            msg = "Invalid RGB configuration label " + label
            log.message(msg, log.ERROR)
        return led

    # Get the RGB Led configuration by label (Retro radio only)
    def getMenuSwitch(self, label):
        menuswitch = -1
        try:
            menuswitch = self.menu_switches[label]
        except:
            msg = "Invalid menu switch configuration label " + label
            log.message(msg, log.ERROR)
        return menuswitch

    # Get update playlists switch
    @property
    def update_playlists(self):
        return self._update_playlists

    @update_playlists.setter
    def update_playlists(self, parameter):
        self._update_playlists = self.convertYesNo(parameter)

    # User interface (Buttons or Rotary encoders or uther)
    @property
    def user_interface(self) -> int:
        return self._user_interface

    @user_interface.setter
    def user_interface(self, parameter: str):
        if parameter == "rotary_encoder":
            self._user_interface = self.ROTARY_ENCODER
        elif parameter == "graphical":
            self._user_interface = self.GRAPHICAL
        elif parameter == "cosmic_controller":
            self._user_interface = self.COSMIC_CONTROLLER
        elif parameter == "phatbeat":
            self._user_interface = self.BUTTONS
        elif parameter == "pifacecad":
            self._user_interface = self.PIFACE_BUTTONS
        elif parameter == "telefunken":
            self._user_interface = self.TELEFUNKEN
        else:
            self._user_interface = self.BUTTONS

    # Get Display type
    def getDisplayType(self):
        return self.display_type

    # User interface (Buttons or Rotary encoders)
    def getUserInterfaceName(self):
        return self.UserInterfaces[self.user_interface]

    # Get Display name
    def getDisplayName(self):
        name = self.DisplayTypes[self.display_type]
        if name == "LUMA":
            name = name + "." + self.luma_device
        return name

    # Get LUMA device name eg SH1106 SSD1306
    @property
    def luma_device(self):
        return self._luma_device

    @luma_device.setter
    def luma_device(self, value):
        self._luma_device = value

    # Get LCD width
    @property
    def display_width(self):
        return self._display_width

    @display_width.setter
    def display_width(self, value):
        self._display_width = value

    # Get Display lines
    @property
    def display_lines(self):
        return self._display_lines

    @display_lines.setter
    def display_lines(self, value):
        self._display_lines = value

    # Get scroll speed
    @property
    def scroll_speed(self):
        return self._scroll_speed

    @scroll_speed.setter
    def scroll_speed(self, value):
        if value < 0.001:
            value = 0.001
        if value > 0.5:
            value = 0.5
        self._scroll_speed = value

    # Get airplay option (True or false)
    @property
    def airplay(self):
        return self._airplay

    @airplay.setter
    def airplay(self, parameter):
        self._airplay = False
        if parameter == "yes" and os.path.isfile(Airplay):
            self._airplay = True

    # Get mixer volume preset
    @property
    def mixer_preset(self):
        return self._mixer_preset

    @mixer_preset.setter
    def mixer_preset(self, volume):
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100
        self._mixer_preset = volume

    # Get startup playlist
    @property
    def startup_playlist(self):
        return self._startup_playlist

    @startup_playlist.setter
    def startup_playlist(self, parameter):
        if parameter == "RADIO":
            self._source = self.RADIO
        elif parameter == "MEDIA":
            self._source = self.PLAYER
        elif parameter == "AIRPLAY":
            self._source = self.AIRPLAY
        elif parameter == "SPOTIFY":
            self._source = self.SPOTIFY
        elif parameter == "LAST":
            self._load_last = True
        self._startup_playlist = parameter

    # Shutdown option
    @property
    def shutdown(self):
        return self._shutdown

    @shutdown.setter
    def shutdown(self, parameter):
        if parameter == "stop_radio":
            self._shutdown = False
        elif parameter == "shutdown":
            self._shutdown = True
        else:
            self._execute = parameter
            self._shutdown = False

    # Execute action (Calls another program)
    @property
    def execute(self):
        return self._execute

    """
    @shutdown.setter
    def execute(self, parameter):
        self._execute = parameter
    """

    # Pull Up/Down resistors (Button interface only)
    @property
    def pull_up_down(self):
        return self._pull_up_down

    @pull_up_down.setter
    def pull_up_down(self, value):
        self._pull_up_down = value

    # Truncate logfile
    @property
    def log_creation_mode(self):
        return self._logfile_truncate

    @log_creation_mode.setter
    def log_creation_mode(self, parameter):
        if parameter == "truncate":
            self._logfile_truncate = True
        else:
            self._logfile_truncate = False

    # ===== SCREEN section =====
    @property
    def screen_size(self):
        return self._screen_size

    @screen_size.setter
    def screen_size(self, parameter):
        sW, sH = parameter.split("x")
        w = int(sW)
        h = int(sH)
        self._screen_size = (w, h)

    # Fullscreen option for graphical screen
    @property
    def fullscreen(self):
        return self._fullscreen

    @fullscreen.setter
    def fullscreen(self, parameter):
        self._fullscreen = self.convertYesNo(parameter)

    # Get graphics window title
    @property
    def window_title(self):
        return self._window_title

    @window_title.setter
    def window_title(self, title):
        self._window_title = title

    # Get graphics window colour
    @property
    def window_color(self):
        return self._window_color

    @window_color.setter
    def window_color(self, color):
        self._window_color = color

    # Get time banner text colour
    @property
    def banner_color(self):
        return self._banner_color

    @banner_color.setter
    def banner_color(self, color):
        self._banner_color = color

    # Get graphics labels colour
    @property
    def labels_color(self):
        return self._labels_color

    @labels_color.setter
    def labels_color(self, color):
        self._labels_color = color

    # Get graphics sdcale labels color
    @property
    def scale_labels_color(self):
        return self._scale_labels_color

    @scale_labels_color.setter
    def scale_labels_color(self, color):
        self._scale_labels_color = color

    # Get display window color
    @property
    def display_window_color(self):
        return self._display_window_color

    @display_window_color.setter
    def display_window_color(self, color):
        self._display_window_color = color

    # Get display window labels color
    @property
    def display_window_labels_color(self):
        return self._display_window_labels_color

    @display_window_labels_color.setter
    def display_window_labels_color(self, color):
        self._display_window_labels_color = color

    # Get slider colour
    @property
    def slider_color(self):
        return self._slider_color

    @slider_color.setter
    def slider_color(self, color):
        self._slider_color = color

    # Get maximum stations displayed per page (vintage graphic radio)
    @property
    def stations_per_page(self):
        return self._stations_per_page

    @stations_per_page.setter
    def stations_per_page(self, value):
        if value > 50:
            value = 50
        self._stations_per_page = value

    # Get window wallpaper
    @property
    def wallpaper(self):
        return self._wallpaper

    @wallpaper.setter
    def wallpaper(self, parameter):
        if os.path.exists(parameter):
            self._wallpaper = parameter

    # Hide mouse True/False
    @property
    def display_mouse(self):
        return self._display_mouse

    @display_mouse.setter
    def display_mouse(self, parameter):
        self._display_mouse = self.convertYesNo(parameter)

    # Allow program switch
    @property
    def switch_programs(self):
        return self._switch_programs

    @switch_programs.setter
    def switch_programs(self, parameter):
        self._switch_programs = self.convertYesNo(parameter)

    # Display date and time yes/no
    @property
    def display_date(self):
        return self._display_date

    @display_date.setter
    def display_date(self, parameter):
        self._display_date = self.convertYesNo(parameter)

    # Display date and time yes/no
    @property
    def display_title(self):
        return self._display_title

    @display_title.setter
    def display_title(self, parameter):
        self._display_title = self.convertYesNo(parameter)

    # Screensaver time
    @property
    def screen_saver(self):
        return self._screen_saver

    @screen_saver.setter
    def screen_saver(self, value):
        self._screen_saver = value

    # Shoutcast key
    @property
    def shoutcast_key(self):
        return self._shoutcast_key

    @shoutcast_key.setter
    def shoutcast_key(self, parameter):
        self._shoutcast_key = parameter

    # Bluetooth device
    @property
    def bluetooth_device(self):
        return self._bluetooth_device

    @bluetooth_device.setter
    def bluetooth_device(self, parameter):
        self._bluetooth_device = parameter

    # Mute action is either mpc pause or stop
    @property
    def mute_action(self):
        return self._mute_action

    @mute_action.setter
    def mute_action(self, parameter):
        if parameter == "pause":
            self._mute_action = PAUSE
        elif parameter == "stop":
            self._mute_action = STOP

    # Oled flip display setting
    @property
    def flip_display_vertically(self):
        return self._flip_display_vertically

    @flip_display_vertically.setter
    def flip_display_vertically(self, parameter):
        self._flip_display_vertically = self.convertYesNo(parameter)

    @property
    def pivumeter(self):
        return self._pivumeter

    @pivumeter.setter
    def pivumeter(self, parameter):
        self._pivumeter = self.convertYesNo(parameter)

    @property
    def disco_light(self) -> int:
        """Give GPIO associated with disco light."""
        return self._disco_light

    @disco_light.setter
    def disco_light(self, parameter: int) -> None:
        """Set the GPIO associated with disco light."""
        self._disco_light = parameter

    @property
    def splash_screen(self):
        return self._splash_screen

    @splash_screen.setter
    def splash_screen(self, parameter):
        self._splash_screen = parameter

    # Station names from playlist names or from the stream
    @property
    def station_names(self):
        return self._station_names

    @station_names.setter
    def station_names(self, parameter):
        if parameter == "stream":
            self._station_names = self.STREAM
        else:
            self._station_names = self.LIST

    # Get translate LCD characters True/False
    @property
    def translate_lcd(self):
        return self._translate_lcd

    @translate_lcd.setter
    def translate_lcd(self, parameter):
        self._translate_lcd = self.convertOnOff(parameter)

    # Get LCD translation codepage
    @property
    def codepage(self):
        return self._codepage

    @codepage.setter
    def codepage(self, codepage):
        if codepage >= 0 and codepage <= 4:
            self._codepage = codepage

    # Get Romanize language e.g. Russian/Cyrillic characters
    @property
    def romanize(self):
        return self._romanize

    @romanize.setter
    def romanize(self, parameter):
        self._romanize = self.convertOnOff(parameter)

    # Get audio_outetting HDMI, headphones DAC tec.
    @property
    def audio_out(self):
        return self._audio_out

    @audio_out.setter
    def audio_out(self, parameter):
        audio_out = parameter.lstrip('"')
        audio_out = audio_out.rstrip('"')
        self._audio_out = audio_out

    # Get language e.g. Russian, European or English etc
    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        self._language = language

    # Get controller type HD44780U or HD44780
    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, parameter):
        self._controller = parameter

    # Get the comitup IP address
    @property
    def comitup_ip(self):
        return self._comitup_ip

    @comitup_ip.setter
    def comitup_ip(self, parameter):
        self._comitup_ip = parameter

    # Internet check URL (Usually goolge.com)
    @property
    def internet_check_url(self):
        return self._internet_check_url

    @internet_check_url.setter
    def internet_check_url(self, url):
        self._internet_check_url = url

    # Internet check port (Usually port 80)
    @property
    def internet_check_port(self):
        return self._internet_check_port

    @internet_check_port.setter
    def internet_check_port(self, port):
        self._internet_check_port = port

    # Get Internet check timeout
    @property
    def internet_timeout(self):
        return self._internet_timeout

    @internet_timeout.setter
    def internet_timeout(self, port):
        self._internet_timeout = port

    # Audio configuration locked - disable dynamic HDMI/headphone
    @property
    def audio_config_locked(self):
        return self._audio_config_locked

    @audio_config_locked.setter
    def audio_config_locked(self, parameter):
        self._audio_config_locked = self.convertYesNo(parameter)

    # Display the shutown button
    @property
    def display_shutdown_button(self):
        return self._display_shutdown_button

    @display_shutdown_button.setter
    def display_shutdown_button(self, parameter):
        self._display_shutdown_button = self.convertYesNo(parameter)

    # Display the Icecast button
    @property
    def display_icecast_button(self):
        return self._display_icecast_button

    @display_icecast_button.setter
    def display_icecast_button(self, parameter):
        self._display_icecast_button = self.convertYesNo(parameter)

    # RGB I2C Rotary Encoder Hex addresses
    @property
    def volume_rgb_i2c(self):
        return self._volume_rgb_i2c

    @volume_rgb_i2c.setter
    def volume_rgb_i2c(self, parameter):
        if self.hexValue(parameter):
            self._volume_rgb_i2c = int(parameter, 16)

    @property
    def channel_rgb_i2c(self):
        return self._channel_rgb_i2c

    @channel_rgb_i2c.setter
    def channel_rgb_i2c(self, parameter):
        if self.hexValue(parameter):
            self._channel_rgb_i2c = int(parameter, 16)

    # Shutdown command
    @property
    def shutdown_command(self):
        shutdown_command = self._shutdown_command.lstrip('"')
        shutdown_command = shutdown_command.rstrip('"')
        return shutdown_command

    @shutdown_command.setter
    def shutdown_command(self, parameter):
        self._shutdown_command = parameter

    # Check for valid hex value
    def hexValue(self, x):
        try:
            int(x, 16)
            isHex = True
        except:
            isHex = False
        return isHex


# End Configuration of class

# Test Configuration class and diagnostics
if __name__ == "__main__":

    config = Configuration()

    # Convert True/False to Yes/No
    def TrueFalse2yn(param):
        yn = "No"
        if param:
            yn = "Yes"
        return yn

    print("Configuration file:", ConfigFile)
    print("Labels in brackets (...) are the parameters found in", ConfigFile)
    print("\n[RADIO] section")
    print("---------------")

    print(
        "Truncate log file (log_creation_mode):", TrueFalse2yn(config.log_creation_mode)
    )
    print(
        "User interface (user_interface):",
        config.user_interface,
        config.getUserInterfaceName(),
    )
    print("Mpd port (mpdport):", config.mpdport)
    print("Mpd client timeout (client_timeout):", config.client_timeout)
    print("Date format (dateformat):", config.dateformat)
    print(
        "Display playlist number(playlist_number):",
        TrueFalse2yn(config.display_playlist_number),
    )
    print("Source (source):", config.source, config.source_name)
    print("Startup playlist(startup_playlist):", config.startup_playlist)
    print("Background colour number ('bg_color'):", config.getBackColor("bg_color"))
    print(
        "Background colour:", config.getBackColorName(config.getBackColor("bg_color"))
    )
    print(
        "Station names source(station_names):",
        config._stationNamesSource[config.station_names],
    )
    print("Do shutdown on exit (shutdown):", TrueFalse2yn(config.shutdown))
    print("Comitup IP (comitup_ip):", config.comitup_ip)
    print("Shoutcast key (shoutcast_key):", config.shoutcast_key)

    print("")
    print("Volume range (volume_range):", config.volume_range)
    print("Volume increment (volume_increment):", config.volume_increment)
    print("Mute action (mute_action):", config.MuteActions[config.mute_action])
    print("Audio out(audio_out):", config.audio_out)
    print(
        "Audio Configuration locked(audio_config_locked):",
        TrueFalse2yn(config.audio_config_locked),
    )
    print("Bluetooth device (bluetooth_device):", config.bluetooth_device)

    print("")
    print("Remote control host (remote_control_host):", config.remote_control_host)
    print("Remote control port (remote_control_port):", config.remote_control_port)
    print("UDP server listen host (remote_listen_host):", config.remote_listen_host)
    print("Remote LED (remote_led):", config.remote_led)
    print("IR remote event daemon (keytable):", config.keytable)

    print("")
    print("Speech (speech):", TrueFalse2yn(config.speech))
    print("Verbose speech(verbose):", TrueFalse2yn(config.verbose))
    print("Speech volume adjustment (speech_volume):", str(config.speech_volume) + "%")
    print("Speak info (speak_info):", TrueFalse2yn(config.speak_info))
    print(
        "Allow playlists playlists (update_playlists):",
        TrueFalse2yn(config.update_playlists),
    )

    print("")
    for switch_label in config.switches:
        switch_gpio = config.getSwitchGpio(switch_label)
        print("%s: %s" % (switch_label, switch_gpio))

    print("")
    for lcdconnect in sorted(config.lcdconnects):
        print(lcdconnect, config.getLcdGpio(lcdconnect))

    print("")
    for led in config.rgb_leds:
        print(led, config.getRgbLed(led))
    print(f"Disco light GPIO: {config.disco_light}")

    print("")
    for menuswitch in config.menu_switches:
        print(menuswitch, config.getMenuSwitch(menuswitch))

    print("")
    rclass = ["Standard", "Alternative", "rgb_rotary", "rgb_i2c_rotary"]
    print("Rotary class:", config.rotary_class, rclass[config._rotary_class])
    rotary_pullup = "PUD_UP"
    if config.rotary_gpio_pullup == GPIO.PUD_OFF:
        rotary_pullup = "PUD_OFF"
    print("Rotary resistor pullup (rotary_pullup):", rotary_pullup)
    if config.rotary_step_size:
        step_size = "half"
    else:
        step_size = "full"
    print("Rotary step size (rotary_step_size):", step_size)
    print("Volume RGB I2C hex address (volume_rgb_i2c):", hex(config.volume_rgb_i2c))
    print("Channel RGB I2C hex address (channel_rgb_i2c):", hex(config.channel_rgb_i2c))

    print("")
    print(
        "Display type (display_type):", config.getDisplayType(), config.getDisplayName()
    )
    print("Display lines (display_lines):", config.display_lines)
    print("Display width display_width):", config.display_width)
    print("Scroll speed (scroll_speed):", config.scroll_speed)
    print("Mixer Volume Preset (config.mixer_preset):", config.mixer_preset)
    print("")
    print(
        "Translate LCD characters (translate_lcd):", TrueFalse2yn(config.translate_lcd)
    )
    print("LCD translation code page (codepage):", config.codepage)
    print("LCD Controller (controller):", config.controller)
    print("Language (language):", config.language)
    print("Romanize Cyrillic (romanize):", TrueFalse2yn(config.romanize))
    print("Pimoroni phatbeat (pivumeter):", TrueFalse2yn(config.pivumeter))

    # I2C parameters
    print("")
    print("I2C bus: (config.i2c_bus)", config.i2c_bus)
    print("I2C address (i2c_address):", hex(config.i2c_address))

    # IR remote control parametere
    print("")
    print("IR key table (keytable):", config.keytable)

    # Internet check
    print("")
    print("Internet check URL (internet_check_url): ", config.internet_check_url)
    print("Internet check port (internet_check_port):", config.internet_check_port)
    print("Internet timeout (internet_timeout): ", config.internet_timeout)

    # OLED
    print(
        "OLED flip screen vertical (flip_display_vertically):",
        TrueFalse2yn(config.flip_display_vertically),
    )
    print("OLED splash screen (splash_screen):", config.splash_screen)

    # Shutdown command
    print("Shutdown command (shutdown_command):", config.shutdown_command)

    # Execute command
    print("Execute on exit command (execute):", config.execute)

    print("\n[SCREEN] section")
    print("----------------")
    print("Graphic screen size (screen_size):", config.screen_size)
    print("Full screen (fullscreen):", TrueFalse2yn(config.fullscreen))
    print("Window title (window_title):", config.window_title)
    print("Window color (window_color):", config.window_color)
    print("Display window color (display_window_color):", config.display_window_color)
    print("Graphic date format (graphic_dateformat):", config.graphic_dateformat)
    print("Window wallpaper (wallpaper):", config.wallpaper)
    print("Labels color (labels_color):", config.labels_color)
    print("Slider color (slider_color):", config.slider_color)
    print("Banner color (banner_color):", config.banner_color)
    print(
        "Display window labels color (display_window_labels_color):",
        config.display_window_labels_color,
    )
    print("Scale labels color (scale_labels_color):", config.scale_labels_color)
    print("Stations per page (stations_per_page):", config.stations_per_page)
    print("Display mouse (display_mouse):", TrueFalse2yn(config.display_mouse))
    print("Display title (display_title):", TrueFalse2yn(config.display_title))
    print("Display date (display_date):", TrueFalse2yn(config.display_date))
    print(
        "Allow programs switch (switch_programs):", TrueFalse2yn(config.switch_programs)
    )
    print(
        "Display shutdown button (display_shutdown_button):",
        TrueFalse2yn(config.display_shutdown_button),
    )
    print(
        "Display Icecast button (display_icecast_button):",
        TrueFalse2yn(config.display_icecast_button),
    )

    print("Screen saver time:", config.screen_saver)
    print("\n[AIRPLAY] section")
    print("----------------")
    print("Airplay (airplay):", TrueFalse2yn(config.airplay))
# End of __main__

# set tabstop=4 shiftwidth=4 expandtab
# retab
