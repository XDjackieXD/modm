#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright (c) 2013, Roboterclub Aachen e.V.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of the Roboterclub Aachen e.V. nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY ROBOTERCLUB AACHEN E.V. ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL ROBOTERCLUB AACHEN E.V. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------
#

import re, sys, os

# add python module logger to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'logger'))
from logger import Logger

class DeviceIdentifier:
	""" DeviceIdentifier
	A class to parse a device string, e.g. "stm32f407vg".
	TODO: Add parsing capabilities for atmel (i.e. avr, xmega, avr32) as
	well as lpc controllers
	"""

	def __init__(self, string=None, logger=None):
		# quick'n'dirty copy constructor
		if isinstance(string, DeviceIdentifier):
			self.log      = string.log
			self.platform = string.platform
			self.family   = string.family
			self.name	  = string.name
			self.type	  = string.type
			self.pin_id   = string.pin_id
			self.size_id  = string.size_id
			self.valid    = string.valid
			return
		
		if logger == None:
			self.log = Logger()
		else:
			self.log = logger

		self._string = string
		# default for properties is None
		self.platform = None # e.g. stm32, avr
		self.family   = None # e.g.	f4, atmega
		self.name	 = None # e.g.   405, 16
		self.type	 = None # e.g. -----, m1
		self.pin_id   = None # e.g.	 r, -----
		self.size_id  = None # e.g.	 g, 16
		self.valid = False
		
		if string == None:
			return
		
		# try to determine platform and to parse string accordingly
		if string.startswith('stm32f'):
			self.platform = "stm32"
			self.family = string[5:7]
			self.name = string[6:9]
			if len(string) >= 10:
				self.pin_id = string[9]
			if len(string) >= 11:
				self.size_id = string[10]
			if len(string) >= 9:
				self.valid = True

		# AVR platform with AT90, ATtiny, ATmega and ATxmega family
		elif string.startswith('at'):
			self.platform = "avr"
			matchString = "(?P<family>attiny|atmega|atxmega)(?P<name>\d+)"
			if string.startswith('at90'):
				matchString = "(?P<family>at90)(?P<type>CAN|can|PWM|pwm|USB|usb)(?P<name>\d+)[Bb]?"
			match = re.search(matchString, string)
			if match:
				self.family = match.group('family').lower()
				self.name = match.group('name').lower()

				if self.family == 'at90':
					self.type = match.group('type').lower()
					match = re.search("(?P<size>128|64|32|16|8|4|3|2|1)\d*", self.name)
					if match:
						self.size_id = match.group('size')
				elif self.family in ['attiny', 'atmega']:
					match = re.search(self.family + self.name + "(?P<type>\w*)-?(?P<package>\w*)", string)
					if match:
						if match.group('type') != '':
							self.type = match.group('type').lower()
						if match.group('package') != '':
							self.pin_id = match.group('package').lower()
					match = re.search("(?P<size>256|128|64|32|16|8|4|2)\d*", self.name)
					if match:
						self.size_id = match.group('size')

				elif self.family == "atxmega":
					match = re.search(self.family + self.name + "(?P<type>[A-Ea-e]?[1-5]?)(?P<package>[Bb]?[Uu]?)", string)
					if match:
						if match.group('type') != '':
							self.type = match.group('type').lower()
						if match.group('package') != '':
							self.pin_id = match.group('package')
					self.size_id = self.name
					# The ATxmega is the 'extreme ATmega' and actually quite different from the ATmega.
					# We call this the xmega, without the 'at' prefix, to remind you of the differences.
					self.family = 'xmega'
				
				self.valid = True
		# LPC Platform
		elif string.startswith('lpc'):
			self.platform = "lpc"
			self.family = string[3:5]
			self.name = string[5:string.find('_')]
			self.log.debug("TODO: Handle ending: %s" % string[string.find('_'):])
			if len(string) >= 7:
				self.valid = True
		else:
			raise ParserException("Parse Error: unknown platform. Device string: %" % (string))

	@property
	def string(self):
		string = ""
		if self.platform != None and '|' not in self.platform and self.platform != "avr":
			string += self.platform
		if self.family != None and '|' not in self.family:
			if self.platform != "stm32":
				string += self.family
			else:
				string += 'f'
		if self.family == 'at90':
			if self.type and '|' not in self.type:
				string += self.type
			if self.name and '|' not in self.name:
				string += self.name
		else:
			if self.name and '|' not in self.name:
				string += self.name
			if self.type and '|' not in self.type and self.platform != "stm32":
				string += self.type
		if self.pin_id and '|' not in self.pin_id and self.family not in ['atmega', 'attiny']:
			string += self.pin_id
		if self.size_id and '|' not in self.size_id and self.platform != "avr":
			string += self.size_id
		return string

	@property
	def properties(self):
		dict = {}
		dict['platform'] = self.platform
		dict['family'] = self.family
		dict['name'] = self.name
		dict['type'] = self.type
		dict['pin_id'] = self.pin_id
		dict['size_id'] = self.size_id
		return dict
	
	def getTargetDict(self):
		return {'target': self.properties}
	
	def isEmpty(self):
		target = self.properties
		for key in target:
			if target[key] != None:
				return False
		return True
	
	def intersectionWithDeviceIdentifier(self, other):
		dev = DeviceIdentifier(self)
		for attr in dev.properties:
			if dev.properties[attr] != other.properties[attr]:
					setattr(dev, attr, None)
		return dev
	
	def unionWithDeviceIdentifier(self, other):
		dev = DeviceIdentifier(self)
		for attr in dev.properties:
			props = [None]
			if (dev.properties[attr] != None):
				props = dev.properties[attr].split("|")
			if (other.properties[attr] != None):
				props.extend(other.properties[attr].split("|"))
			props = list(set(props))
			props = [p for p in props if p != None]
			props.sort()
			setattr(dev, attr, "|".join(props) if len(props) else None)
		return dev

	def __hash__(self):
		return hash(str(self))

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		target = self.properties
		#target = {o:target[o] for o in target if target[o] != None}
		t = {}
		for o in target:
			if target[o] != None:
				t[o] = target[o]
		target = t
		return "DeviceIdentifier(" + str(target) + ")"
