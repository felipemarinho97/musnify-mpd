# coding: utf-8
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser
import json
import os
import sys
import time
import re

import gi
import requests

gi.require_version('Notify', '0.7')

from gi.repository import Notify
from gi.repository.Gio import File
from gi.repository.GdkPixbuf import Pixbuf
from mpd import MPDClient

configFile = os.path.expanduser("~/.config/musnify-mpd/musnify-mpd.config")

if not os.path.isfile(configFile):
    print("Loading default config")
    configFile = "/etc/musnify-mpd.config"

config = ConfigParser()
config.read(configFile)

host = config.get("mpd", "host", fallback=os.environ.get("MPD_HOST", "localhost"))
port = config.get("mpd", "port", fallback=os.environ.get("MPD_PORT", 6600))
password = config.get("mpd", "password", fallback=os.environ.get("MPD_PASSWORD", 6600))
if config.has_option("apiKey", "lastfm"):
    apiKey = config.get("apiKey", "lastfm")
musicLibrary = os.path.expanduser(config.get("mpd", "musiclibrary", fallback='~/Music')) + "/"

debug = False

class MPDWrapper:
    def __init__(self, host="localhost", port="6600", password=None):
        self.client = MPDClient()
        self.client.timeout = 1
        self.client.idletimeout = None
        self.client.connect(host, port)
        if password:
            self.client.password(password)

    def getCurrentSong(self):
        song = self.client.currentsong()

        try:
            artist = song["artist"]
        except KeyError:
            song["artist"] = "Unknown Artist"

        try:
            album = song["album"]
        except KeyError:
            song["album"] = "Unknown Album"

        try:
            title = song["title"]
        except KeyError:
            try:
                song["title"] = song["file"].split("/")[-1]
            except KeyError:
                song["title"] = "Unknown Title"

        return song

    def getStatus(self):
        return self.client.status()["state"]
    
    def waitForChange(self):
        return self.client.idle("player")


class NotificationWrapper:
    def __init__(self):
        Notify.init("musnify-mpd")
        self.notification = Notify.Notification.new("Initializing Musnify...")

    def notify(self, artist, album, title, cover):
        self.notification.clear_hints()
        if cover == None:
            self.notification.update(title, ("by " + artist + "\n" + album).replace("&", "&amp;"), "music")
        else:
            self.notification.update(title, ("by " + artist + "\n" + album).replace("&", "&amp;"))
            self.notification.set_image_from_pixbuf(cover)
        self.notification.show()

    def notifyStatus(self, status):
        self.notification.clear_hints()
        if status == "pause":
            self.notification.update("MPD Paused",icon="music")
        elif status == "stop":
            self.notification.update("MPD Stopped",icon="music")
        self.notification.show()


class CoverArt:
    @staticmethod
    def fetchAlbumCoverURL(artist, album, size=1):
        apiUrl = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo'

        if not 'apiKey' in globals():
            return False

        apiReqUrl = apiUrl + '&artist=' + artist + '&album=' + album + '&api_key=' + apiKey + '&format=json'
        r = requests.get(apiReqUrl)

        dataInfo = json.loads(r.content)

        try:
            assert dataInfo["error"] > 0
            if debug:
                print("Nothing found on last fm")
            return False
        except:
            url = dataInfo["album"]["image"][size]["#text"]
            if url == "":
                if debug:
                    print("Nothing found on last fm")
                return False
            return url

    @staticmethod
    def downloadPixbufAlbumCover(url):
        if debug:
            print("downloading album cover from " + url)

        f = File.new_for_uri(url)
        stream = f.read()

        cover = Pixbuf.new_from_stream(stream)
        stream.close()
        return cover

    @staticmethod
    def fetchLocalCover(path):
        regex = re.compile(r'(album|cover|\.?folder|front).*\.(gif|jpeg|jpg|png)$', re.I | re.X)
        try:
            for e in os.listdir(path):
                if regex.match(e) != None:
                    if debug:
                        print("local cover found at " + path + e)
                    return Pixbuf.new_from_file(path + e)
        except:
            pass
        if debug:
            print("Nothing found on local directory")
        return False

class Musnify(object):
    def __init__(self):
        self.nw = NotificationWrapper()
        self.lastfmCoverPath = "/tmp/musnifyCurrentCover.png"

    def start(self):
        mpd = MPDWrapper(host, port, password)

        status = ""
        song = ""

        while True:
            actualStatus = mpd.getStatus()
            actualSong = mpd.getCurrentSong()

            if status != actualStatus:
                status = mpd.getStatus()

                if actualStatus == "play":
                    song = mpd.getCurrentSong()
                    self.handle(song)
                else:
                    self.nw.notifyStatus(status)

            if (song != actualSong) and status != "stop":
                song = mpd.getCurrentSong()
                self.handle(song)
                if debug:
                    print(song)
            
            mpd.waitForChange()

    def handle(self, song):
        localCoverPath = CoverArt.fetchLocalCover(musicLibrary + self._separa(song["file"]))

        artist = song["artist"]
        album = song["album"]
        title = song["title"]

        coverUrl = CoverArt.fetchAlbumCoverURL(artist, album)

        if coverUrl != False:
            path = CoverArt.downloadPixbufAlbumCover(coverUrl)
        elif localCoverPath != False:
            path = localCoverPath
        else:
            path = None
        self.nw.notify(artist, album, title, path)

    @staticmethod
    def _separa(url):
        url0 = url.split("/")
        url1 = ""
        for i in range(len(url0) - 1):
            url1 += url0[i] + "/"
        return url1

    def stop(self):
        Notify.uninit()

def help():
    print("""musnify-mpd\n\nOptions:
  --help\tShow this help and exit
  -h\t\tSpecify your MPD host (default: localhost)
  -p\t\tSpecify your MPD port (default: 6600)
  -x\t\tSpecify your MPD password (empty by default)
  -d\t\tRun with debug mode enabled
         """)

if __name__ == "__main__":
    for i in range(len(sys.argv)):
        if sys.argv[i] == "-h":
            host = sys.argv[i + 1]
        if sys.argv[i] == "-p":
            port = sys.argv[i + 1]
        if sys.argv[i] == "-x":
            password = sys.argv[i + 1]
        if sys.argv[i] == "-d":
            debug = True
        if sys.argv[i] == "--help":
            help()
            exit()
    
    musnify = Musnify()

    try:
        musnify.start()
    except KeyboardInterrupt:
        pass
    finally:
        musnify.stop()
