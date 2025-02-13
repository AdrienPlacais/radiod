#!/bin/bash
# set -x
# Raspberry Pi Internet Radio Audio configuration script 
# $Id: configure_audio.sh,v 1.5 2024/12/23 12:51:41 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used to select the sound card to be used.
# It configures /etc/mpd.conf
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

# Set -s flag to skip package addition or removal (dpkg error otherwise)
# Also prevent running dtoverlay command (Causes hangups on stretch)

# This script requires an English locale(C)
export LC_ALL=C

SKIP_PKG_CHANGE=$1
SCRIPT=$0

# Version 7.5 onwards allows any user with sudo permissions to install the software
USR=$(logname)
GRP=$(id -g -n ${USR})

BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
MPDCONFIG=/etc/mpd.conf
ASOUNDCONF=/etc/asound.conf
MODPROBE=/etc/modprobe.d/alsa-base.conf
MODULES=/proc/asound/modules
DIR=/usr/share/radio
CONFIG=/etc/radiod.conf
ASOUND_DIR=${DIR}/asound
ASOUND_CONF=/etc/asound.conf
AUDIO_INTERFACE="alsa"
LIBDIR=/var/lib/radiod
PIDFILE=/var/run/radiod.pid
I2SOVERLAY="dtoverlay=i2s-mmap"
PULSEAUDIO=/usr/bin/pulseaudio
SPOTIFY_CONFIG=/etc/default/raspotify
MIXER_ID_FILE=${LIBDIR}/mixer_volume_id
PULSE_PA=/etc/pulse/default.pa
OS_RELEASE=/etc/os-release
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/audio.log

BLUETOOTH_SERVICE=/lib/systemd/system/bluetooth.service

# Audio types
JACK=1  # Audio Jack or Sound Cards
HDMI=2  # HDMI
DAC=3   # DAC card
BLUETOOTH=4 # Bluetooth speakers
USB=5   # USB PnP DAC
TLVDAC=6 # tlvaudioCODEC
WM8960=7 # Waveshare WM8960 DAC
RPI=8    # RPi Sound Cards
BIT=$(getconf LONG_BIT)     # 32 or 64-bit archtecture

TYPE=${JACK}

SCARD="headphones"  # aplay -l string. Set to headphones, HDMI, DAC ,bluetooth or other 
            # description to configure the audio_out parameter in the configuration file
PIVUMETER=0 # PVumeter using alsa

# dtoverlay parameter in /etc/config.txt
DTOVERLAY=""

# Device and Name
DEVICE="hw:0,0"
CARD=0
NAME="Onboard jack"
MIXER="software"
COMMAND=""
# Format is Frequency 44100 Hz: 16 bits: 2 channels
FORMAT="44100:16:2"
NUMID=1
# Lock /etc/radio.conf from being updated 
# (HDMI plug in/out changes audio card order) 0=no 1=yes
LOCK_CONFIG=0   

# Pulse audio asound.conf
USE_PULSE=0
ASOUND_CONF_DIST=asound.conf.dist
ASOUND_CONF_DEFAULT=asound.conf.dist

# Create log directory
sudo mkdir -p ${LOGDIR}
sudo chown ${USR}:${GRP} ${LOGDIR}

sudo rm -f ${LOG}
echo "$0 configuration log, $(date) " | tee ${LOG}

# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}

# Get OS release name
function codename
{
    VERSION_CODENAME=$(grep VERSION_CODENAME $OS_RELEASE)
    arr=(${VERSION_CODENAME//=/ })
    CODENAME=$(echo "${arr[1]}" | tr -d '"')
    echo ${CODENAME}
}

# Identify card ID from "aplay -l" command
function card_id
{
    name=$1
    # Match first line only
    CARD_ID=$(aplay -l | grep -m1 ${name} | awk '{print $2}')
    CARD_ID=$(echo "${CARD_ID}" | tr -d ':')
    if [[ ${#CARD_ID} < 1 ]]; then
        CARD_ID=0
    fi
    CARD_ID=$(expr ${CARD_ID} + 0)
    echo ${CARD_ID}
}

# Releases before Bullseye not supported
if [[ $(release_id) -lt 11 ]]; then
    echo "This program is only supported on Raspbian Bullseye/Bookworm or later!" | tee -a ${LOG}
    echo "This system is running $(codename) OS"
    echo "Exiting program." | tee -a ${LOG}
    exit 1
fi


# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
fi

echo "Boot configuration in ${BOOTCONFIG}" | tee -a ${LOG}

# Location of raspotify configuration file has changed in Bullseye
if [[ $(release_id) -ge 11 ]]; then
    SPOTIFY_CONFIG=/etc/raspotify/conf
else
    SPOTIFY_CONFIG=/etc/default/raspotify
fi

# Add the user to the audio group 
sudo usermod -G audio -a $USER

# Stop the radio and MPD
CMD="sudo systemctl stop radiod.service"
echo ${CMD};${CMD} | tee -a ${LOG}
CMD="sudo systemctl stop mpd.service"
echo ${CMD};${CMD} | tee -a ${LOG}
CMD="sudo systemctl stop mpd.socket"
echo ${CMD};${CMD} | tee -a ${LOG}

sleep 2 # Allow time for service to stop

# If the above fails check pid
if [[ -f  ${PIDFILE} ]];then
    rpid=$(cat ${PIDFILE})
    if [[ $? == 0 ]]; then  # Don't seperate from above
        sudo kill -TERM ${rpid}  >/dev/null 2>&1
    fi
fi

sudo service mpd stop

selection=1 
while [ $selection != 0 ]
do
    ASOUND_CONF_DIST=${ASOUND_CONF_DEFAULT}

    ans=$(whiptail --title "Select audio output" --menu "Choose your option" 18 75 12 \
    "1" "On-board audio output jack" \
    "2" "HDMI output" \
    "3" "USB DAC" \
    "4" "Pimoroni Pirate/pHat with PiVumeter" \
    "5" "HiFiBerry DAC/Mini-amp/PCM5102A/PCM5100A" \
    "6" "HiFiBerry DAC plus/Amp2" \
    "7" "HiFiBerry DAC Digi" \
    "8" "HiFiBerry Amp" \
    "9" "IQaudIO DAC/Zero DAC" \
    "10" "IQaudIO DAC plus and Digi/AMP " \
    "11" "JustBoom DAC/Zero/Amp" \
    "12" "JustBoom Digi HAT" \
    "13" "Bluetooth device" \
    "14" "Adafruit speaker bonnet" \
    "15" "Pimoroni Pirate Audio" \
    "16" "HiFiBerry DAC 400" \
    "17" "Waveshare WM8960 DAC" \
    "18" "RPi (Raspberry Pi) Audio Cards" \
    "19" "Manually configure" 3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DESC="On-board audio output Jack"

    elif [[ ${ans} == '2' ]]; then
        DESC="HDMI output"
        NAME="HDMI audio"
        TYPE=${HDMI}
        NUMID=3

    elif [[ ${ans} == '3' ]]; then
        DESC="USB PnP DAC"
        NAME="USB PnP"
        DEVICE="plughw:1,0"
        CARD=1
        MIXER="software"
        TYPE=${USB}
        NUMID=6

    elif [[ ${ans} == '4' ]]; then
        DESC="Pimoroni pHat with PiVumeter"
        NAME=${DESC}
        DTOVERLAY="hifiberry-dac"
        MIXER="hardware"
        ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.pivumeter
        TYPE=${DAC}
        PIVUMETER=1  # PVumeter using pulse
        LOCK_CONFIG=1   


    elif [[ ${ans} == '5' ]]; then
        DESC="HiFiBerry DAC/Mini-amp"
        NAME=${DESC}
        DTOVERLAY="hifiberry-dac"
        ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.softvol
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '6' ]]; then
        DESC="HiFiBerry DAC Plus/Amp2"
        NAME=${DESC}
        DTOVERLAY="hifiberry-dacplus"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '7' ]]; then
        DESC="HiFiBerry Digi"
        NAME=${DESC}
        DTOVERLAY="hifiberry-digi"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '8' ]]; then
        DESC="HiFiBerry Amp"
        NAME=${DESC}
        DTOVERLAY="hifiberry-amp"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '9' ]]; then
        DESC="IQaudIO DAC/Zero DAC"
        NAME=${DESC}
        DTOVERLAY="iqaudio-dac"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '10' ]]; then
        DESC="IQaudIO DAC plus or DigiAMP"
        NAME="IQaudIO DAC+"
        TYPE=${DAC}
        DTOVERLAY="iqaudio-dacplus"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '11' ]]; then
        DESC="JustBoom DAC/Amp"
        NAME="JustBoom DAC"
        DTOVERLAY="justboom-dac"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '12' ]]; then
        DESC="JustBoom Digi HAT"
        NAME="JustBoom Digi HAT"
        DTOVERLAY="justboom-digi"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '13' ]]; then
        DESC="Bluetooth device"
        # NAME is set up later
        MIXER="software"
        USE_PULSE=1
        AUDIO_INTERFACE="pulse"
        TYPE=${BLUETOOTH}
        ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.bluealsa
        LOCK_CONFIG=1   
        CARD=-1     # No cards displayed (aplay -l) 

    elif [[ ${ans} == '14' ]]; then
        DESC="Adafruit speaker bonnet"
        NAME=${DESC}
        DTOVERLAY="hifiberry-dac"
        MIXER="software"
        ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.bonnet
        TYPE=${DAC}
        DEVICE="plug:softvol"
        USE_PULSE=0

    elif [[ ${ans} == '15' ]]; then
        DESC="Pimoroni Pirate Audio"
        NAME=${DESC}
        DTOVERLAY="hifiberry-dac"
        MIXER="software"
        TYPE=${DAC}

    elif [[ ${ans} == '16' ]]; then
        DESC="HiFiBerry DAC 400" 
        NAME=${DESC}
        DTOVERLAY="dacberry400"
        SCARD="tlvaudioCODEC"
        MIXER="software"
        TYPE=${TVDAC}

    elif [[ ${ans} == '17' ]]; then
        DESC="Waveshare WM8960 DAC" 
        NAME=${DESC}
        DTOVERLAY="wm8960-soundcard"
        MIXER="software"
        TYPE=${WM8960}
        LOCK_CONFIG=1   
        ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.wm8960

    elif [[ ${ans} == '18' ]]; then
        DESC="RPi (Raspberry Pi) Audio Cards" 
        NAME=${DESC}
        TYPE=${RPI}

    elif [[ ${ans} == '19' ]]; then
        DESC="Manual configuration"
    fi

    whiptail --title "$DESC selected" --yesno "Is this correct?" 10 60
    selection=$?
done 

# Handle RPi Display cards
if [[ ${TYPE} == ${RPI} ]]; then
    SCARD="Unknown"
    selection=1 
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Select audio output" --menu "Choose your option" 18 75 12 \
        "1" "RPi DAC Pro" \
        "2" "RPi DigiAmp Plus" \
        "3" "RPi DAC Plus" \
        "4" "RPi Codec Zero" 3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="RPi DAC Pro"
            NAME=${DESC}
            DTOVERLAY="rpi-dacpro"
            MIXER="software"
            SCARD="DAC"

        elif [[ ${ans} == '2' ]]; then
            DESC="RPi DigiAmp Plus"
            NAME=${DESC}
            DTOVERLAY="rpi-digiampplus"
            MIXER="software"
            SCARD="DigiAmp+"

        elif [[ ${ans} == '3' ]]; then
            DESC="RPi DAC Plus"
            NAME=${DESC}
            DTOVERLAY="rpi-dacplus"
            MIXER="software"
            SCARD="DAC+"

        elif [[ ${ans} == '4' ]]; then
            DESC="RPi Codec Zero"
            NAME=${DESC}
            DTOVERLAY="rpi-codeczero"
            MIXER="software"
            SCARD="Codec Zero"
        fi

        whiptail --title "$DESC selected" --yesno "Is this correct?" 10 60
        selection=$?
    done
fi

# Summarise selection
echo "${DESC} selected" | tee -a ${LOG}
echo "Card ${CARD}, Device ${DEVICE}, Mixer ${MIXER}" | tee -a ${LOG}

# Install alsa-utils if not already installed
PKG="alsa-utils"
if [[ ! -f /usr/bin/amixer && ${SKIP_PKG_CHANGE} != "-s" ]]; then
    echo "Installing ${PKG} package" | tee -a ${LOG}
    sudo apt-get --yes install ${PKG}
fi

# Check if required pulse audio installed
if [[ ${USE_PULSE} == 1 ]]; then
    if [[ ! -f ${PULSEAUDIO} ]]; then
        if [[ ${SKIP_PKG_CHANGE} == "-s" ]]; then
            echo "${DESC} requires pulseaudio to run correctly" | tee -a ${LOG}
            echo "Run: sudo apt-get install pulseaudio" | tee -a ${LOG}
            echo "and re-run ${SCRIPT}" | tee -a ${LOG}
            exit 1
        else
            PKG="pulseaudio"
            echo "Installing ${PKG} package" | tee -a ${LOG}
            sudo apt-get --yes install ${PKG}

            # Set up /etc/pulse/default.pa
            if [[ ! -f ${PULSE_PA}.orig ]]; then
                cmd="sudo cp ${PULSE_PA} ${PULSE_PA}.orig"
                echo $cmd | tee -a ${LOG}
                $cmd | tee -a ${LOG}
            fi
            
        fi
    fi
    grep "^load-module module-native-protocol-tcp" ${PULSE_PA}
    if [[ $? != 0 ]]; then  # Do not separate from above
        cmd="sudo cp ${PULSE_PA}.orig ${PULSE_PA}"
        echo $cmd | tee -a ${LOG}
        $cmd | tee -a ${LOG}
        sudo sed -i -e "0,/^load-module module-native-protocol-unix/{s/load-module module-native-protocol-unix/load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1/}" ${PULSE_PA}
    fi
else
    if [[ -f ${PULSEAUDIO} ]]; then
        if [[ ${SKIP_PKG_CHANGE} == '-s' ]]; then
            echo "${DESC} requires pulseaudio to be removed" | tee -a ${LOG}
            echo "Run: sudo apt-get remove pulseaudio" | tee -a ${LOG}
            echo "and re-run ${SCRIPT}" | tee -a ${LOG}
            echo "" | tee -a ${LOG}
        else
            echo "Un-installng pulseaudio" | tee -a ${LOG}
            sudo apt --yes remove pulseaudio | tee -a ${LOG}
        fi
    fi

fi

# Lock audio configuration if required (radiod won't dynamically configure Card number)
# See audio_config_lock parameter in /etc/radiod.conf
if [[ ${LOCK_CONFIG} == 1 ]]; then
    # Lock configuration in /etc/radiod.conf
    sudo sed -i -e "0,/^audio_config_locked=/{s/audio_config_locked=.*/audio_config_locked=yes/}" ${CONFIG}
else
    sudo sed -i -e "0,/^audio_config_locked=/{s/audio_config_locked=.*/audio_config_locked=no/}" ${CONFIG}
fi

# Check if audio_out parameter in configuration file
# Configure pulseaudio package
PKG="pulseaudio"
if [[ -x /usr/bin/${PKG} && ${USE_PULSE} == 1 ]]; then
    AUDIO_INTERFACE="pulse"
    echo "Package ${PKG} found" | tee -a ${LOG}
    echo "Configuring ${MPDCONFIG} for ${PKG} support" | tee -a ${LOG}
else
    echo "Configuring ${MPDCONFIG} for ${AUDIO_INTERFACE} support" | tee -a ${LOG}
fi

# Select HDMI name ether "HDMI" (Buster/Bullseye) or "vc4hdmi" (Bullseye)
# Also setup audio_out parameter in the config file
echo "Configuring ${NAME} as output" | tee -a ${LOG}

if [[ ${TYPE} == ${HDMI} ]]; then
    echo "Configuring HDMI as output" | tee -a ${LOG}
    sudo touch ${LIBDIR}/hdmi

    aplay -l | grep vc4hdmi
    if [[ $? == 0 ]]; then
        SCARD=vc4hdmi
        DEVICE="sysdefault:vc4hdmi0"
        ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.vc4hdmi
    else
        SCARD=HDMI
        DEVICE="0:0"
    fi
    echo "Card ${SCARD} Device ${DEVICE}"

    # Force HDMI hotplug in /boot/config.txt
    sudo sed -i 's/^#hdmi_force_hotplug=.*$/hdmi_force_hotplug=1/g' ${BOOTCONFIG}

elif [[ ${TYPE} == ${JACK} ]]; then
    echo "Configuring on-board jack as output" | tee -a ${LOG}
    sudo amixer cset numid=3 1
    sudo alsactl store
    SCARD="headphones"

elif [[ ${TYPE} == ${DAC} ]]; then
    echo "Configuring DAC as output" | tee -a ${LOG}
    SCARD="DAC"

elif [[ ${TYPE} == ${USB} ]]; then
    echo "Configuring USB PnP as output" | tee -a ${LOG}
    SCARD="USB"

elif [[ ${TYPE} == ${TLVDAC} ]]; then
    echo "Configuring tlvaudioCODEC as output" | tee -a ${LOG}
    SCARD="tlvaudioCODEC"

elif [[ ${TYPE} == ${WM8960} ]]; then
    echo "Configuring Waveshare WM8960 as output" | tee -a ${LOG}
    SCARD="wm8960soundcard"


# Configure bluetooth device
elif [[ ${TYPE} == ${BLUETOOTH} ]]; then
 
    # Install Bluetooth packages 
    if [[ ${SKIP_PKG_CHANGE} != "-s" ]]; then
        echo "Installing Bluetooth packages" | tee -a ${LOG}
        sudo apt --yes install pulseaudio-module-bluetooth 
    fi

    echo "Configuring Blutooth device as output" | tee -a ${LOG}

    # Configure bluealsa
    echo |  tee -a ${LOG}
    echo "Bluetooth device configuration"  |  tee -a ${LOG}
    echo "------------------------------"  |  tee -a ${LOG}
    if [[ $(release_id) -lt 12 ]]; then
        PAIRED=$(bluetoothctl paired-devices)
    else
        PAIRED=$(bluetoothctl devices)
    fi
    echo ${PAIRED} |  tee -a ${LOG}
    BT_NAME=$(echo ${PAIRED} | awk '{print $3}')
    BT_DEVICE=$( echo ${PAIRED} | awk '{print $2}')

    # Disable Sap initialisation in bluetooth.service   
    grep "noplugin=sap" ${BLUETOOTH_SERVICE}
    if [[ $? != 0 ]]; then  # Do not seperate from above
        echo "Disabling Sap driver in  ${BLUETOOTH_SERVICE}" | tee -a ${LOG}
        sudo sed -i -e 's/^ExecStart.*/& --plugin=a2dp --noplugin=sap/' ${BLUETOOTH_SERVICE} | tee -a ${LOG}
    fi

    # Connect the Bluetooth device
    if [[  ${BT_DEVICE} != '' ]];then
        echo "Bluetooth device ${BT_NAME} ${BT_DEVICE} found"  |  tee -a ${LOG}
        NAME=${BT_NAME}
        DEVICE="bluetooth"
        cmd="bluetoothctl trust ${BT_DEVICE}" 
        echo $cmd | tee -a ${LOG}
        $cmd | tee -a ${LOG}
        cmd="bluetoothctl connect ${BT_DEVICE}" 
        echo $cmd | tee -a ${LOG}
        $cmd | tee -a ${LOG}
        cmd="bluetoothctl discoverable on" 
        echo $cmd | tee -a ${LOG}
        $cmd | tee -a ${LOG}
        cmd="bluetoothctl info ${BT_DEVICE}" 
        echo $cmd | tee -a ${LOG}
        $cmd | tee -a ${LOG}

        # Configure bluetooth device in /etc/radiod.conf 
        sudo sed -i -e "0,/^bluetooth_device/{s/bluetooth_device.*/bluetooth_device=${BT_DEVICE}/}" ${CONFIG}
    else
        echo "Error: No paired bluetooth devices found" | tee -a ${LOG}
        echo "Use bluetoothctl to pair Bluetooth device" | tee -a ${LOG}
        echo "and re-run this program with the following commands" | tee -a ${LOG}
        echo "  cd ${DIR} " | tee -a ${LOG}
        echo "  sudo ./configure_audio.sh  " | tee -a ${LOG}
        echo -n "Press enter to continue: "
        read ans
        exit 1
    fi
    SCARD="bluetooth"
fi

# Configure the audio_out parameter in /etc/radiod.conf
echo |  tee -a ${LOG}
echo "Configuring audio_out parameter in ${CONFIG} with ${SCARD} " | tee -a ${LOG}
sudo sed -i -e "0,/audio_out=/{s/^#aud/aud/}" ${CONFIG}
sudo sed -i -e "0,/audio_out=/{s/^audio_out=.*/audio_out=\"${SCARD}\"/}" ${CONFIG}
grep -i "audio_out="  ${CONFIG} | tee -a ${LOG}

# Configure Card device using the audio_out parameter configured above in /etc/radiod.conf 
if [[ ${TYPE} != ${BLUETOOTH} ]]; then
    CARD_ID=$(card_id ${SCARD})
    echo "Card ${SCARD} ID ${CARD_ID}"
    DEVICE=$(echo ${DEVICE} | sed -e 's/:0/:'"${CARD_ID}"'/')
fi

# Set up asound configuration for espeak and aplay
echo |  tee -a ${LOG}
if [[ ${CARD} -ge 0 ]]; then
    echo "Configuring ${ASOUNDCONF} with card ${CARD} " | tee -a ${LOG}
fi

if [[ ! -f ${ASOUNDCONF}.org && -f ${ASOUNDCONF} ]]; then
    echo "Saving ${ASOUNDCONF} to ${ASOUNDCONF}.org" | tee -a ${LOG}
    sudo cp -f ${ASOUNDCONF} ${ASOUNDCONF}.org
fi

# Set up /etc/asound.conf except if using pulseaudio and bluetooth
echo "Copying ${ASOUND_CONF_DIST} to ${ASOUNDCONF}" | tee -a ${LOG}
sudo cp -f ${ASOUND_DIR}/${ASOUND_CONF_DIST} ${ASOUNDCONF}

if [[ ${CARD} == 0 ]]; then
        sudo sed -i -e "0,/card/s/1/0/" ${ASOUNDCONF}
        sudo sed -i -e "0,/plughw/s/1,0/0,0/" ${ASOUNDCONF}
else
        sudo sed -i -e "0,/card/s/0/1/" ${ASOUNDCONF}
        sudo sed -i -e "0,/plughw/s/0,0/1,0/" ${ASOUNDCONF}
fi

# Save original configuration 
if [[ ! -f ${MPDCONFIG}.orig ]]; then
    grep ^audio_output ${MPDCONFIG}
    if [[ $? != 0 ]]; then
        echo "Correcting corrupt ${MPDCONFIG} (Missing audio_out definition)" 
        sudo cp -f -p ${DIR}/mpd.conf ${MPDCONFIG}
        sudo cp -f -p ${DIR}/mpd.conf ${MPDCONFIG}.orig
    fi
    sudo cp -f -p ${MPDCONFIG} ${MPDCONFIG}.orig
fi

# Configure name device and mixer type in mpd.conf
sudo cp -f -p ${MPDCONFIG}.orig ${MPDCONFIG}
echo ${NAME}
echo "Device ${DEVICE}"
NAME=$(echo ${NAME} | sed 's/\//\\\//')
DEVICE=$(echo ${DEVICE} | sed 's/\//\\\//')

if [[ ${TYPE} == ${BLUETOOTH} ]]; then
    sudo cp ${DIR}/mpd.conf ${MPDCONFIG}
    # The mpd configuration is different for 32-bit and 64-bit archictectures
    echo "Configuring ${MPDCONFIG} for ${BIT}-bit system"

    sudo sed -i -e "0,/^\sname/{s/\sname.*/\tname\t\t\"${NAME}\"/}" ${MPDCONFIG}
    if [[ ${BIT} == "64" ]]; then
        sudo sed -i -e "0,/^\stype/{s/\stype.*/\ttype\t\t\"alsa\"/}" ${MPDCONFIG}
        sudo sed -i -e "0,/^#\s*device\s/{s/^#\s*device/\tdevice/}" ${MPDCONFIG}
        sudo sed -i -e "0,/^\sdevice\s/{s/^\sdevice.*/\tdevice\t\t\"bluealsa\"/}" ${MPDCONFIG}
    else
        sudo sed -i -e "0,/^\stype/{s/\stype.*/\ttype\t\t\"pipe\"/}" ${MPDCONFIG}
        sudo sed -i -e "0,/^#\sdevice\s/{s/^#\sdevice/\tdevice/}" ${MPDCONFIG}
        sudo sed -i -e "0,/^\sdevice\s/{s/^\sdevice.*/\tcommand\t\t\"aplay -D bluealsa -f cd\"/}" ${MPDCONFIG}
        sudo sed -i -e "0,/^#\s*mixer_device\s/{s/^#\s*mixer_device.*/\tformat\t\t\"44100:16:2\"/}" ${MPDCONFIG}
    fi

    # Configure /etc/asound.conf
    sudo sed -i -e "0,/defaults.bluealsa.device\s\"<btdevice>\"/{s/device\s\"<btdevice>\"/device \"${BT_DEVICE}\"/g}" ${ASOUND_CONF}
    sudo sed -i -e "0,/device\s\"<btdevice>\"/{s/device\s\"<btdevice>\"/device \"${BT_DEVICE}\"/g}" ${ASOUND_CONF}

    # /etc/radiod.conf
    echo "Configuring audio_out parameter in ${CONFIG}" | tee -a ${LOG}
    sudo sed -i -e "0,/^audio_out=/{s/^audio_out=.*/audio_out=\"bluetooth\"/}" ${CONFIG}
    grep -i "audio_out="  ${CONFIG} | tee -a ${LOG}

else
    sudo sed -i -e "0,/^\stype/{s/\stype.*/\ttype\t\t\"${AUDIO_INTERFACE}\"/}" ${MPDCONFIG}
    sudo sed -i -e "0,/^\sname/{s/\sname.*/\tname\t\t\"${NAME}\"/}" ${MPDCONFIG}
    sudo sed -i -e "0,/mixer_type/{s/.*mixer_type.*/\tmixer_type\t\"${MIXER}\"/}" ${MPDCONFIG}
    sudo sed -i -e "/^#/ ! {s/\stype.*/\ttype\t\t\"${AUDIO_INTERFACE}\"/}" ${MPDCONFIG}
    if [[ ${PIVUMETER} == 1 ]]; then
        sudo sed -i -e "0,/device/{s/.*device.*/\#\tdevice\t\t\"${DEVICE}\"/}" ${MPDCONFIG}
    else
        sudo sed -i -e "0,/device/{s/.*device.*/\tdevice\t\t\"${DEVICE}\"/}" ${MPDCONFIG}
    fi
fi
if [[ ${TYPE} == ${WM8960} ]]; then
    # Set up aplay pipe
    #sudo sed -i -e "0,/device/{s/.*device.*/\tcommand\t\t\"${COMMAND}\"/}" ${MPDCONFIG}
    sudo sed -i -e "0,/device/{s/.*device.*/\#\tdevice\t\t\"${DEVICE}\"/}" ${MPDCONFIG}
fi

# Set up mpd.conf for Pirate radio with pHat Beat (pivumeter)
if [[ ${PIVUMETER} == 1 ]]; then
    sudo sed -i -e "0,/pivumeter=/{s/^pivumeter=.*/pivumeter=yes/}" ${CONFIG}
else
    sudo sed -i -e "0,/pivumeter=/{s/^pivumeter=.*/pivumeter=no/}" ${CONFIG}
fi

# Set the mixer control to "DAC"
if [[ ${DEVICE} =~ "softvol" ]]; then
    sudo sed -i -e '0,/^#\smixer_control.*/{s/^#\smixer_control.*/\tmixer_control   \"DAC\"/}' ${MPDCONFIG}
fi

# Save all new alsa settings
sudo alsactl store
if [[ $? != 0 ]]; then  # Don't seperate from above
    echo "Failed to alsa settings"
fi

# Bind address to localhost (Prevent binding to IPV6 ::1)
sudo sed -i -e "0,/bind_to_address/{s/.*bind_to_address.*/bind_to_address\t\t\"127.0.0.1\"/}" ${MPDCONFIG}

# Save original boot config
if [[ ! -f ${BOOTCONFIG}.orig ]]; then
    sudo cp ${BOOTCONFIG} ${BOOTCONFIG}.orig
fi

# Delete existing dtoverlays
echo "Delete old audio overlays" | tee -a ${LOG}
sudo sed -i '/dtoverlay=iqaudio/d' ${BOOTCONFIG}
sudo sed -i '/dtoverlay=hifiberry/d' ${BOOTCONFIG}
sudo sed -i '/dtoverlay=justboom/d' ${BOOTCONFIG}
sudo sed -i '/dtoverlay=wm8960-soundcard/d' ${BOOTCONFIG}

# Add dtoverlay for sound cards and disable on-board sound
if [[ ${DTOVERLAY} != "" || ${TYPE} == ${HDMI} ]]; then
    grep "^dtoverlay=${DTOVERLAY}" ${BOOTCONFIG} >/dev/null 2>&1
    if [[ $? != 0 ]]; then
        echo "dtoverlay=${DTOVERLAY} added"
        #sudo sed -i "/\[all\]/a dtoverlay=${DTOVERLAY}" ${BOOTCONFIG}
        sudo  bash -c "echo dtoverlay=${DTOVERLAY} >> ${BOOTCONFIG}"
    fi

    echo "Disable on-board audio" | tee -a ${LOG}
    sudo sed -i 's/^dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}
    sudo sed -i 's/^#dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}

    # Load the overlay
    cmd="sudo dtoverlay ${DTOVERLAY}"
    echo ${cmd}; ${cmd}
    if [[ $?  == 0 ]]; then
        OVERLAY_LOADED=1
    else
        OVERLAY_LOADED=0
    fi
else
    if [[ ${TYPE} == ${BLUETOOTH} || ${TYPE} == ${USB} || ${TYPE} == ${WM8960} ]]; then
        # Switch off onboard devices (headphones and HDMI) if bluetooth or USB
        sudo sed -i 's/^dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}
        sudo sed -i 's/^#dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}
    else
        sudo sed -i 's/^dtparam=audio=.*$/dtparam=audio=on/g'  ${BOOTCONFIG}
        sudo sed -i 's/^#dtparam=audio=.*$/dtparam=audio=on/g'  ${BOOTCONFIG}
    fi
fi

# Switch on I2S audio for PCM5102A devices
sudo sed -i 's/^#dtparam=i2s=.*$/dtparam=i2s=on/g'  ${BOOTCONFIG}

# Configure I2S overlay
grep "^#${I2SOVERLAY}" ${BOOTCONFIG} >/dev/null 2>&1
if [[ $?  == 0 ]]; then
        sudo sed -i 's/^#dtoverlay=i2s-mmap/dtoverlay=i2s-mmap/g'  ${BOOTCONFIG}
else
    grep "^${I2SOVERLAY}" ${BOOTCONFIG} >/dev/null 2>&1
    if [[ $?  != 0 ]]; then
        sudo  bash -c "echo ${I2SOVERLAY} >> ${BOOTCONFIG}"
    fi
fi

# Load the audio card overlay
if [[ ${DTOVERLAY} != "" ]]; then
    cmd="sudo dtoverlay ${DTOVERLAY}"
    echo ${cmd} | tee -a ${LOG}
    ${cmd}
fi

# Set mixer ID to 0 to force set_mixer_id to run  
# first time the radio runs
echo "Reset ${MIXER_ID_FILE} file to zero" |  tee -a ${LOG}
sudo echo 0 > ${MIXER_ID_FILE}

echo; echo ${BOOTCONFIG} | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
grep ^dtparam=audio ${BOOTCONFIG} | tee -a ${LOG}
grep ^dtoverlay ${BOOTCONFIG} | tee -a ${LOG}

echo | tee -a ${LOG}
DESC=$(echo ${DESC} | sed 's/\\\//\//g')
echo "${DESC} configured" | tee -a ${LOG}

grep ^audio_out= ${CONFIG}
if [[ $? != 0 ]]; then  # Don't seperate from above
        echo "ERROR: audio_out parameter missing from ${CONFIG}" | tee -a ${LOG}
        echo "At the end of this program run \"amixer controls | grep card\" " | tee -a ${LOG}
        echo "to display available audio output devices" | tee -a ${LOG}
        echo '' | tee -a ${LOG}
        echo "Add the audio_out parameter to ${CONFIG} as shown below" | tee -a ${LOG}
        echo "     audio_out=\"<unique string>\"" | tee -a ${LOG}
        echo "     Where: <unique string> is a unique string from the amixer command output" | tee -a ${LOG}
        echo "Enter to continue: "
        read ans
fi

cmd="sudo echo 0 > ${MIXER_ID_FILE}"
echo ${cmd} | tee -a ${LOG}
${cmd}

# Configure Spotify if installed  
if [[ -f ${SPOTIFY_CONFIG} ]]; then
    # Save original configuration
    if [[ ! -f ${SPOTIFY_CONFIG}.orig ]]; then
        sudo cp ${SPOTIFY_CONFIG} ${SPOTIFY_CONFIG}.orig
    fi
    echo '' | tee -a ${LOG}
    echo "Configuring Spotify (raspotify)" | tee -a ${LOG}
    echo "-------------------------------" | tee -a ${LOG}
    spotify_device=${DEVICE} 
    if [[ ${DEVICE} =~ bluetooth ]]; then
        spotify_device="btdevice"
    fi
    OPTIONS="OPTIONS=\"--device ${spotify_device}\" "
    echo ${OPTIONS} | tee -a ${LOG}

    # Check if configured
    grep "^OPTIONS=" ${SPOTIFY_CONFIG}
    if [[ $? != 0 ]]; then
        echo "OPTIONS not found"
        sudo sed -i -e '/^#OPTIONS=/a OPTIONS=' ${SPOTIFY_CONFIG}
    fi
    sudo sed -i -e "0,/^OPTIONS.*$/{s/OPTIONS.*/${OPTIONS}/}" ${SPOTIFY_CONFIG}
fi 

echo '' | tee -a ${LOG}
if [[ ${OVERLAY_LOADED}} != 1 && ${DTOVERLAY} != "" ]]; then
    echo "WARNING:" | tee -a ${LOG}
    echo "OVERLAY ${DTOVERLAY} could not be loaded, so configuration is not complete!" | tee -a ${LOG}
    echo "It is necessary to reboot the Raspberry Pi and after reboot " | tee -a ${LOG}
    echo "to re-boot again to complete the configuration" | tee -a ${LOG}
    echo -n "Press enter to continue: "
    read ans
fi

# Reboot dialogue
echo '' | tee -a ${LOG}
if [[ ${SKIP_PKG_CHANGE} != "-s" ]]; then
    if (whiptail --title "Audio selection" --yesno "Reboot Raspberry Pi (Recommended)" 10 60) then
        echo "Rebooting Raspberry Pi" | tee -a ${LOG}
        sudo reboot 
    else
        echo | tee -a ${LOG}
        echo "You chose not to reboot!" | tee -a ${LOG}
        echo "Changes made will not become active until the next reboot" | tee -a ${LOG}
    fi
fi

# Integrity check of /boot/config.txt
declare -i lines=$(wc -l ${BOOTCONFIG} | awk '{print $1}')
if [[ ${lines} -lt 10 ]]; then
    echo "ERROR: ${BOOTCONFIG} failed integrity check"
    echo "Restoring ${BOOTCONFIG} from ${BOOTCONFIG}.orig"
    sudo cp ${BOOTCONFIG}.orig ${BOOTCONFIG}
    echo "Re-run sudo ${0} "
    exit 1
else
    echo
    echo "${BOOTCONFIG} has ${lines} lines"
    echo
fi

# Sync changes to disk
sync;sync

echo "A log of these changes has been written to ${LOG}"
exit 0
# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
