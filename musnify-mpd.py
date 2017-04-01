# coding: utf-8

import requests
import json
import time
import os
import gi
gi.require_version('Notify', '0.7')

from gi.repository import Notify
from mpd import MPDClient

global musicLibrary
musicLibrary = "/home/darklyn/Música/"

class MPDWrapper:
	def __init__(self,host="localhost",port="6600"):
		self.client = MPDClient()
		self.client.timeout = 1
		self.client.idletimeout = None
		self.client.connect(host,port)

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
			song["title"] = song["file"].split("/")[-1]
		
		return song

	def getStatus(self):
		return self.client.status()

class NotificationWrapper:
	def __init__(self):
		Notify.init("musnify-mpd")
		self.notification = Notify.Notification.new("Initializing Musnify..")

	def notify(self,artist,album,title,coverPath):
		self.notification.update(title,"by " + artist + "\n" + album,coverPath)
		self.notification.show()

	def notifyStatus(self,status):
		if status == "pause":
			self.notification.update("MPD Paused")
		elif status == "stop":
			self.notification.update("MPD Stopped")
		self.notification.show()

class CoverArt:
	@staticmethod
	def fetchAlbumCoverURL(artist,album,size=1):
		apiUrl = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo'
		apiKey = "3915759326476a5f23963c3782fa3b98"
		
		apiReqUrl = apiUrl+'&artist=' + artist + '&album=' + album + '&api_key=' + apiKey + '&format=json'
		r = requests.get(apiReqUrl)
		
		dataInfo = json.loads(r.content)
		
		try:
			assert dataInfo["error"] > 0
			return False
		except:
			url = dataInfo["album"]["image"][size]["#text"]
			if url == "":
				return False
			return url

	@staticmethod
	def downloadAlbumCover(url,path):
		response = requests.get(url, stream=True)
		with open(path, "wb") as fileOutput:
			fileOutput.write(response.raw.read())

class Musnify(object):
	def __init__(self):
		self.nw = NotificationWrapper()
		self.lastfmCoverPath = "/tmp/musnifyCurrentCover.png"

	def start(self):
		mpd = MPDWrapper("0.0.0.0","6688")

		status = ""
		song = ""

		while True:
			time.sleep(0.5)
			actualStatus = mpd.getStatus()["state"]
			actualSong = mpd.getCurrentSong()

			if status != actualStatus:
				status = mpd.getStatus()["state"]

				if actualStatus == "play":
					song = mpd.getCurrentSong()
					musnify.handle(song)
				else:
					musnify.nw.notifyStatus(status)
			

			if song != actualSong: 
				song = mpd.getCurrentSong()
				musnify.handle(song)

	def handle(self,song):
		localCoverPath = musicLibrary + self._separa(song["file"]) + "Folder.jpg"

		artist = song["artist"]
		album = song["album"]
		title = song["title"]

		coverUrl = CoverArt.fetchAlbumCoverURL(artist,album)

		if coverUrl != False:
			CoverArt.downloadAlbumCover(coverUrl,self.lastfmCoverPath)
			path = self.lastfmCoverPath
		else:
			path = localCoverPath


		self.nw.notify(artist, album, title, path)
	
	@staticmethod
	def _separa(url):
		url0 = url.split("/")
		url1 = ""
		for i in range(len(url0)-1):
			url1 += url0[i] + "/"
		return url1

	def stop(self):
		Notify.uninit()


musnify = Musnify()

try:
	musnify.start()
finally:
	musnify.stop()
