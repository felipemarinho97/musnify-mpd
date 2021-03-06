#!/bin/bash

echo 'installing..'
echo '#!/usr/bin/env python2' >> musnify-mpd && cat musnify-mpd.py >> musnify-mpd
mv musnify-mpd /usr/bin/musnify-mpd
chmod 755 /usr/bin/musnify-mpd

echo 'copying config files'
cp musnify-mpd.config /etc/musnify-mpd.config
echo 'config file stored in /etc/musnify-mpd.config'

mkdir /usr/share/doc/musnify-mpd
cp doc/musnify-mpdconfig.example /usr/share/doc/musnify-mpd/musnify-mpdconfig.example
chmod 555 /usr/share/doc/musnify-mpd/musnify-mpdconfig.example
echo 'copy the musnify-mpdconfig.example to ~/.config/musnify-mpd/musnify-mpd.config to set up your custom config'

cp README.md /usr/share/doc/musnify-mpd/README.md

echo 'done.'

