#!/usr/bin/env python

import urllib 
import serial
import time
import os
import sys
import socket
import random

from datetime import datetime
import RPi.GPIO as GPIO
import serial, io


class WOBBApHATDoor:
	def __init__(self):
		# config
		self.door_repeat_timeout = 7 # sec, must be more than door_open_timeout
		self.door_open_timeout = 5 * 1000 # m sec
		self.rfid_uart_filename = "/dev/serial0"
		self.rfid_uart_timeout = 2 # sec
		self.rfid_en_gpio = 14
		self.door_coil_gpio = 23
		self.door_sense_gpio = 26

		# open rfid uart port
		# Parallax 28140 is uart 2400 8N1
		self.rfid_uart = serial.Serial(self.rfid_uart_filename, 2400, timeout=self.rfid_uart_timeout)
		if(not self.rfid_uart):
			print "Couldn't open rfid UART on {}".format(self.rfid_uart_filename)
			sys.exit()
		self.rfid_uart_io = io.TextIOWrapper(io.BufferedRWPair(self.rfid_uart, self.rfid_uart), newline='\r')

		# setup GPIO
		GPIO.setmode(GPIO.BCM)
		# setup en pin after serial setup so it will override gpio mux
		GPIO.setup(self.rfid_en_gpio, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(self.door_coil_gpio, GPIO.OUT, initial=GPIO.LOW)
		# door sense (green/yellow) is NC when door closed, rising edge on open
		GPIO.setup(self.door_sense_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	def rfid_readline(self):
		# expecting \n X X X X X X X X X X \r from Parallax 28140
		# MUST setup readline to catch \r instead of \n or we will always see old tags
		new_tag = self.rfid_uart_io.readline()
		if(len(new_tag) == 12 and new_tag[0] == '\n' and new_tag[11] == '\r'):
			return "TAG|" + new_tag[1:11] + "\r\n"
		else:
			return "BADREAD\r\n"

	def open_door_for_time(self):
		GPIO.output(self.door_coil_gpio, GPIO.HIGH)
		GPIO.output(self.rfid_en_gpio, GPIO.HIGH)
		# continue either after timeout or when door is closed
		GPIO.wait_for_edge(self.door_sense_gpio, GPIO.RISING, timeout=self.door_open_timeout)
		GPIO.output(self.door_coil_gpio, GPIO.LOW)
		GPIO.output(self.rfid_en_gpio, GPIO.LOW)
		# might want to purge rfid uart input here

	def open_door_force(self):
		GPIO.output(self.door_coil_gpio, GPIO.HIGH)

	def close_door_force(self):
		GPIO.output(self.door_coil_gpio, GPIO.LOW)

	def cleanup():
		GPIO.cleanup()


socket.setdefaulttimeout(10);


def parse_number(num):
	valid_cards = open('rfid.inc','r').read().strip().split('\n')
	return num in valid_cards

lastnum = "q"
lasttime = 0
door = WOBBApHATDoor()

while True:
	print "READY"
	# start by resetting door to closed
	door.close_door_force()
	
	# check for override request
	if os.path.isfile('forceopen.now'):
		print datetime.today().isoformat(' ')
		print "!!FORCING DOOR OPEN REMOTELY!!"
		door.open_door_for_time()
		time.sleep(1);
		os.remove('forceopen.now')
		# try:
		# 	urllib.urlretrieve("https://ssl.acemonstertoys.org/member/logrfid.php?rfid=-1&valid=True")
		# except:
		# 	print "Timed-out or some other error reporting to AMT server"
	time.sleep(0.2)

	# check for rfid request
	line = door.rfid_readline()
	print datetime.today().isoformat(' ')
	line = line.strip()
	print line
	parts = line.split('|')
	cmd = parts[0]
	if cmd == "BADREAD":
		print "invalid rfid read (noise?)"
	elif cmd == "SENSOR":
		pass
		# try:
		# 	urllib.urlretrieve("https://ssl.acemonstertoys.org/member/sensor.php?door="+parts[1])
		# except:
		# 	print "Timed-out or some other error reporting to AMT server"
	elif cmd == "TAG":
		num = parts[1]
		valid = parse_number(num)
		if valid:
			if num == lastnum and (time.time() - lasttime) < door.door_repeat_timeout:
				print "Too many reads in a row"
			else:
				door.open_door_for_time()
				print "ACCESS GRANTED"
		else:
			print "DENIED"

		lastnum = num
		lasttime = time.time()

		# try:
		# 	urllib.urlretrieve("https://ssl.acemonstertoys.org/member/logrfid.php?rfid="+num+"&valid="+str(valid))
		# except:
		# 	print "Timed-out or some other error reporting to AMT server"


# Example output:
#
# READY
# 2018-01-15 07:53:49.356094
# BADREAD
# invalid rfid read (noise?)
# READY
# 2018-01-15 07:53:51.563473
# TAG|XXXXXXXXXX
# ACCESS GRANTED
# READY
# 2018-01-15 07:53:52.614501
# TAG|XXXXXXXXXX
# Too many reads in a row
# READY
# 2018-01-15 07:53:52.822779
# TAG|XXXXXXXXXX
# Too many reads in a row
# READY
# 2018-01-15 07:53:53.030419
# TAG|XXXXXXXXXX
# Too many reads in a row
# READY
# 2018-01-15 07:53:55.239558
# TAG|XXXXXXXXXX
# Too many reads in a row
# READY
# 2018-01-15 07:53:57.450473
# BADREAD
# invalid rfid read (noise?)
# READY
# 2018-01-15 07:53:59.658845
# BADREAD
# invalid rfid read (noise?)
