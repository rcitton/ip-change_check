#!/usr/bin/python3

# -------------------------------------------------------------------------------
# Author: Ruggero Citton
# Date: September 18 , 2023
# Purpose: Send a notification in case of public IP change
# Tested on: Ubuntu 23.04 - Raspberry PI 4
#
#
# Licensed under The MIT License (MIT).
# See included LICENSE file or the notice below.
#
# Copyright (c) 2023 Ruggero Cittons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -------------------------------------------------------------------------------

import requests
import time
import sys 
import os.path
from datetime import datetime

from notifications import notification

#Global variables
ipFile = os.path.join(os.path.expanduser("~"), ".config/ip-changed/ip.log")
timeout = 10

class Service:
  url=""
  def request(self): return requests.get(self.url, timeout = timeout)

class Icanhazip(Service):
  name="icanhazip"
  url="http://ipv4.icanhazip.com/"
  def ip(self): return self.request().text.strip()

class Ipinfo(Service):
  name="ipinfo"
  url="http://ipinfo.io/json"
  def ip(self): return self.request().json()["ip"]

class IpApi(Service):
  name="ip-api"
  url="http://ip-api.com/json"
  def ip(self): return self.request().json()["query"]

def request_ip():
  #List of services
  services = [Icanhazip(), Ipinfo(), IpApi() ]
  for i in range(len(services)):
    
    service = services[i]
    try:
      start = time.time()
      print ("- Requesting current ip with '{}'".format(service.name))
      ip = service.ip()
      print ("- Request took {} seconds ".format(int(time.time() - start)))
      return ip
    except Exception as error:
      print ("- Exception when requesting ip using '{}': {} ".format(service.name, error ))
      
  error = "Non available services, add more services or increase the timeout (services = {}, timeout = {}) ".format(len(services), timeout)
  raise RuntimeError(error)

def current_ip():
  ip = open(ipFile,"r").readlines()[0]
  return ip.replace('\n', '')

def save_ip(ip):
  f = open(ipFile,'w')
  f.write(str(ip)) 

#Main
timestamp_format   = "%d-%m-%Y %H:%M:%S"
hour_minute_format = "%H:%M"
current_timestamp  = datetime.now()
current_timestring = datetime.strftime(current_timestamp, timestamp_format)

if os.path.isfile(ipFile) : #File exists
  print("*** Check at "+current_timestring+" ***")
  new_ip = request_ip()  
  old_ip = current_ip()

  if new_ip != old_ip:
    save_ip(new_ip)
    print ("- IP has changed from "+old_ip+" to "+new_ip)
    notification.sent_notification(old_ip, new_ip)
  else :
    print ("- IP is still the same: {}".format(old_ip))

else: 
  new_ip = request_ip()
  save_ip(new_ip)
  print ("- This is the first time to run the ip_change script, I will create a file in {} to store your current address: {} ".format(ipFile, new_ip))

# --------------
# EndOfFile
# --------------
