#!/usr/bin/env bash

echo 'removing executable files..'
rm /usr/bin/musnify-mpd

echo 'removing config files'
rm /etc/musnify-mpd.config
rm -r /usr/share/doc/musnify-mpd

echo 'done.'
