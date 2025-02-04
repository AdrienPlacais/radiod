# Raspberry Pi Internet Radio

Author : Bob Rathbone
Site   : http://www.bobrathbone.com
Email  : bob@bobrathbone.com

This program uses  Music Player Daemon 'mpd', its client 'mpc' and the python3-mpd library
See http://www.musicpd.org/
Use "sudo apt-get install mpd mpc python3-mpd" to install the Music Player Daemon (MPD)
This software uses the python3-mpd library. See https://packages.debian.org/sid/python3-mpd

## Resume

The software is an adaptation of Bob Rathbone's work for a Telefunken vintage radio.
Radio can be controlled thanks to the buttons:
- First: OFF
- 2nd: FIP webradios
- 3rd: Spotify
- 4th: unused
- Last: backlight

Volume is controlled thanks to left rotary encore (push to mute).
Navigation between FIP webradios/within Spotify playlists is performed thanks to right rotary encoder.
![picture_radio](images/pic_radio.jpg) 


## To-do
- [ ] Software vol matching radio's
- [x] Spotify
- [x] No sound at start up
- [x] Set-up backlight

## Optional
- [ ] During navigation between FIP webradios, voice to announce which webradio is selected (use [fip-radiod](https://github.com/AdrienPlacais/fip_radiod)).
- [ ] Hold mute to tell the name of current song (needs `espeak`)
- [ ] Radios on the front plate match FIP webradios
