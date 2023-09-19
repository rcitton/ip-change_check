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

import json
import os
import requests
import socket
import sys

import getpass
import keyring

from notifications import cron_scheduling
from notifications import pushbullet_notification as pushbullet
from notifications import ifttt_notification as ifttt
from notifications import sendmail as mail

# ----------------------------------------------------------------------
# Notification Type
notification_type   = os.environ.get('NOTIFICATION_TYPE', None)

# Mail Notification
sender_mail_address     = os.environ.get('SENDER_MAIL_ADDRESS', None)
receiver_mail_addresses = os.environ.get('RECEIVER_MAIL_ADDRESSES', None)
smtp_server             = os.environ.get('SMTP_SERVER', None)
port_number             = os.environ.get('SMTP_SERVER_PORT', None)
mail_password           = os.environ.get('MAIL_PASSWORD', None)

# IFTT
ifttt_name = os.environ.get('IFTTT_NAME', None)

# Generic Notification Password/Token
notification_password = os.environ.get('NOTIFICATION_PASSWORD', None)

# Generic Data
ipchange_check = os.environ.get('IPCHANGE_CHECK', "60")
house_address  = os.environ.get('HOUSE_ADDRESS', None)
crontab        = os.environ.get('CRONTAB', False)
# ----------------------------------------------------------------------

def banner():
    print ("")
    print ("██╗██████╗░  ░█████╗░██╗░░██╗░█████╗░███╗░░██╗░██████╗░███████╗  ░█████╗░██╗░░██╗███████╗░█████╗░██╗░░██╗")
    print ("██║██╔══██╗  ██╔══██╗██║░░██║██╔══██╗████╗░██║██╔════╝░██╔════╝  ██╔══██╗██║░░██║██╔════╝██╔══██╗██║░██╔╝")
    print ("██║██████╔╝  ██║░░╚═╝███████║███████║██╔██╗██║██║░░██╗░█████╗░░  ██║░░╚═╝███████║█████╗░░██║░░╚═╝█████═╝░")
    print ("██║██╔═══╝░  ██║░░██╗██╔══██║██╔══██║██║╚████║██║░░╚██╗██╔══╝░░  ██║░░██╗██╔══██║██╔══╝░░██║░░██╗██╔═██╗░")
    print ("██║██║░░░░░  ╚█████╔╝██║░░██║██║░░██║██║░╚███║╚██████╔╝███████╗  ╚█████╔╝██║░░██║███████╗╚█████╔╝██║░╚██╗")
    print ("╚═╝╚═╝░░░░░  ░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝░╚═════╝░╚══════╝  ░╚════╝░╚═╝░░╚═╝╚══════╝░╚════╝░╚═╝░░╚═╝")
    print ("")



def get_integer_input():
    while True:
        minute_interval = input("- Provide the minute interval: ")
        if minute_interval.isnumeric():  # Check if input is a number
            minute_interval = int(minute_interval)  # Convert it to number
            return minute_interval
        else:  # if it is not a number
            print("The input is not a number.")

def curate_input(shown_message, expected_values):
    result = input(shown_message)
    if result in expected_values:
        return result.lower()
    else:
        return curate_input("You need to input one of the following: {}. Try again! ".format(expected_values),
                            expected_values)

def initialize():
    global notification_type
    global sender_mail_address
    global receiver_mail_addresses
    global smtp_server
    global port_number
    global mail_password
    global ifttt_name
    global notification_password
    global house_address
    global ipchange_check
    global crontab
    global container
    config_path = os.path.join(os.path.expanduser("~"), ".config/ip-changed")
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    if os.path.exists(os.path.join(config_path, "config.json")):
        result = curate_input("Configuration file already exists. Would you like to reconfigure the script? (y/n) ",
                              ("y", "n"))
        if result != "y":
            print("Alright, script should be ready to run. If you run into issues, run the initialization process "
                  "again")
            exit(1)

    json_data = {}
    print("We are going to walk you through setting up this script!")
    if notification_type is None:
        notification_type = curate_input("- Would you like to be alerted of an ip change through mail and by a notification"
                                         " on your pushbullet or through ifttt? ('', 'pushbullet', 'ifttt'): ",
                                         ("", "pushbullet", "ifttt"))
    json_data["notification_type"] = notification_type

    # Mail setup
    mail_working = False
    failed_attempts = 0
    while not mail_working:
        if sender_mail_address is None:
            sender_mail_address = None
            while sender_mail_address is None:
                sender_mail_address = mail.check_mails(input("- Please input the mail address you want to send the "
                                                            "notification mail from: "))
        json_data["sender"] = sender_mail_address

        if mail_password is None:
            keyring.set_password("Mail-OutageDetector", json_data["sender"],
                                getpass.getpass("- Type in your password: "))
        else:
            keyring.set_password("Mail-OutageDetector", json_data["sender"], mail_password)
        
        if receiver_mail_addresses is None:
            receiver_mail_addresses = None
            while receiver_mail_addresses is None:
                receiver_mail_addresses = mail.check_mails(input("- Please input the mail addresses "
                                                                "(separated by a comma) to which you want to send "
                                                                "the notification: "))
        json_data["receivers"] = receiver_mail_addresses

        if "gmail" in json_data["sender"]:
            json_data["smtp_server"] = "smtp.gmail.com"
            json_data["port"] = 465
        elif "yahoo" in json_data["sender"]:
            json_data["smtp_server"] = "smtp.mail.yahoo.com"
            json_data["port"] = 465
        else:
            if smtp_server is None:
                json_data["smtp_server"] = input("- Please enter the SMTP server of your mail provider "
                                                "(you can look it up online): ")
            if port_number is None:
                port_number = ""
                while not port_number.isdigit():
                    port_number = input("- Type in the port number of the SMTP server: ")
                json_data["port"] = port_number

        if mail_password is None:
            password = keyring.get_password("Mail-OutageDetector", json_data["sender"])
        else:
            password = mail_password
            break

        try:
            mail.send_mail(json_data["sender"], json_data["receivers"], "IP Change Detector - Testing mail notification",
                           "Mail sent successfully!", json_data["smtp_server"], password, json_data["port"])
            mail_working = True
            print("Mail has been successfully sent, check your mailbox!")
        except mail.SMTPAuthenticationError as e:
            failed_attempts += 1
            if failed_attempts >= 3:
                print("Too many failed attempts, exiting script, try again later!")
                exit(1)
            if "BadCredentials" in str(e):
                print(e)
                print("Wrong user/password or less secure apps are turned off")
            elif "InvalidSecondFactor" in str(e):
                print(e)
                print("Two factor authentification is not supported! Turn it off and try again!")
        except socket.gaierror:
            print("No internet connection, try again later!")
            exit(1)


    if notification_type == "pushbullet":
        if notification_password is None:
            pushbullet_working = False
            failed_attempts = 0
            while not pushbullet_working:
                try:
                    keyring.set_password("PushBullet-OutageDetector", "pushbullet",
                                        getpass.getpass("- Input your PushBullet API key: "))
    
                    pushbullet_key = keyring.get_password("PushBullet-OutageDetector", "pushbullet")

                    print("Trying to send a notification through PushBullet!")
                    pushbullet.push_to_bullet("Testing PushBullet Key", "Test is successful!", "", pushbullet_key)
                    pushbullet_working = True
                    print("Notification has been successfully sent, check your phone!")
                except pushbullet.errors.InvalidKeyError:
                    failed_attempts += 1
                    if failed_attempts >= 3:
                        print("Too many failed attempts, exiting script, try again later!")
                        exit(1)
                    print("Key is not valid, try again!")
    
                except requests.exceptions.ConnectionError:
                    print("No internet, try reconnecting and running the script again!")
                    exit(1)
        else:
            keyring.set_password("PushBullet-OutageDetector", "pushbullet", notification_password)

    elif notification_type == "ifttt":
        if ifttt_name is None:
            ifttt_working = False
            failed_attempts = 0
            while not ifttt_working:
                try:
                    ifttt_name = input("- Input your IFTTT event name: ")
                    keyring.set_password("IFTTT-OutageDetector", ifttt_name, getpass.getpass("- Input your IFTTT API key: "))
                    api_key = keyring.get_password("IFTTT-OutageDetector", ifttt_name)
                    print("Trying to send a notification through IFTTT!")
                    iftt.push_to_ifttt(ifttt_name, api_key, "Testing IFTTT")
                    ifttt_work = curate_input("Did you get the notification? (y/n) ", ("y", "n"))
                    if ifttt_work == "y":
                        ifttt_working = True
                    else:
                        failed_attempts += 1
                        if failed_attempts >= 3:
                            print("Too many failed attempts, exiting script, try again later!")
                            exit(1)
                        print("Check to make sure you followed the steps correctly and try again.")
    
                except requests.exceptions.ConnectionError:
                    print("No internet, try reconnecting and running the script again!")
                    exit(1)
        else:
            keyring.set_password("IFTTT-OutageDetector", ifttt_name, notification_password)
        json_data["ifttt_event"] = ifttt_name

    else:
        notification_type == "none"


    if house_address is None:
        json_data["house_address"] = input("- Enter a description of the run location (used to tell you in the "
                                        "{} where the ip cahnge happened): ".format(notification_type))
    else:
        json_data["house_address"] = house_address.format(notification_type)

    with open(os.path.join(config_path, 'config.json'), 'w+') as json_file:
        json.dump(json_data, json_file)

    if crontab is False:
        crontab_edit = curate_input("- Would you like to setup the script to run automatically "
                                    "(it will run at boot time and at given minute intervals)? (y/n) ", ("y", "n"))
    else:
        crontab_edit = 'y'

    if crontab_edit == "y":
        ipchange_check = get_integer_input()
        exec_path = os.path.join(os.getcwd(), "IP-check.py")
        cron_scheduling.schedule_job(exec_path, config_path, int(ipchange_check))


if __name__ == '__main__':
    banner()
    initialize()

# --------------
# EndOfFile
# --------------
