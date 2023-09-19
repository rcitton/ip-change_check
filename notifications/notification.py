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
# ------------------------------------------------------------------------------

import json
import os
from pathlib import Path
import socket

import keyring

from notifications import pushbullet_notification as pushbullet
from notifications import ifttt_notification as ifttt
from notifications import sendmail as mail


def sent_notification(old_ip, new_ip):

    # Getting configuration
    config_path = os.path.join(os.path.expanduser("~"), ".config/ip-changed")
    with open(os.path.join(config_path, "config.json")) as json_file:
      notification_json = json.load(json_file)
      notification_type = notification_json["notification_type"]

    if notification_type == "pushbullet":
        pushbullet_notification = True
        ifttt_notification = False
    elif notification_type == "ifttt":
        pushbullet_notification = False
        ifttt_notification = True
    else:
        pushbullet_notification = False
        ifttt_notification = False


    # Collect Mail data
    address = ""
    try:
        with open(os.path.join(config_path, "config.json")) as json_file:
            mail_json = json.load(json_file)
            sender = mail_json["sender"]
            receivers = mail_json["receivers"]
            smtp_server = mail_json["smtp_server"]
            password = keyring.get_password("Mail-OutageDetector", sender)
            if password is None:
                print("Mail password not found, try running initial configuration again!")
                exit(1)
            address = mail_json["house_address"]
    except FileNotFoundError:
        print("Mail will not be sent, there is no config file in the folder.")
    except KeyError:
        print("Config.json file doesn't have all fields (sender, receivers, smtp_server, house address")


    # Collect additional notification info
    if pushbullet_notification:
        push_key = keyring.get_password("PushBullet-OutageDetector", "pushbullet")
        try:
            with open(os.path.join(config_path, "config.json")) as json_file:
                notification_json = json.load(json_file)
                address = notification_json["house_address"]
        except FileNotFoundError:
            print("Configuration file does not exist, try running the initial configuration again!")
        except KeyError:
            print("Config.json file doesn't have all fields, try running the initial configuration again!")
    elif ifttt_notification:
        try:
            with open(os.path.join(config_path, "config.json")) as json_file:
                notification_json = json.load(json_file)
                ifttt_name = notification_json["ifttt_event"]
                address = notification_json["house_address"]
        except FileNotFoundError:
            print("Configuration file does not exist, try running the initial configuration again!")
        except KeyError:
            print("Config.json file doesn't have all fields, try running the initial configuration again!")
        api_key = keyring.get_password("IFTTT-OutageDetector", ifttt_name)


    #Send Mail
    print("- Sending mail...")
    subject = "IP changed at {}!".format(address)
    message_body = "IP has changed from {} to {}".format(old_ip, new_ip)
    mail.send_mail(sender, receivers, subject, message_body, smtp_server, password)

    if pushbullet_notification:
        # Send pushbullet
        print("- Sending pushbullet notification...")
        pushbullet.push_to_bullet(old_ip, new_ip, address, push_key)
    elif ifttt_notification:
        # Send ifttt
        print("- Sending ifttt notification...")
        message_body = message_body+" at "+address
        ifttt.push_to_ifttt(ifttt_name, api_key, message_body)

if __name__ == '__main__':
    sent_notification("", "")


# --------------
# EndOfFile
# --------------

