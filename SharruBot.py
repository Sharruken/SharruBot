#!/usr/bin/env python3
import string
import socket
import sys
import time
import os
import subprocess
import logging
import threading
try:
        import colorama
except ModuleNotFoundError:
        subprocess.run("python -m pip install colorama")
        import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)

CONFIG_FILE = open("CONFIG.txt")
CONFIG = list(line.rstrip('\n') for line in CONFIG_FILE.readlines())
CONFIG_FILE.close()
HOST = "irc.twitch.tv"
PORT = 6667
PASS = CONFIG[1] # your Twitch OAuth token
IDENT = "sharrubot"  # Twitch username your using for your bot
CHANNEL = input("Please input the channel you would like me to connect to or blank to connect to your default(" + CONFIG[0] + ")")
if (CHANNEL == ""):
        CHANNEL = CONFIG[0]
PERMISSIONS_FILE = open("PERMISSIONS.txt")
PERMISSIONS = list(line.rstrip('\n') for line in PERMISSIONS_FILE.readlines())
PERMISSIONS_FILE.close()
connectedChats = [CHANNEL]


def openSocket():
        try:
                s = socket.socket()
                s.connect((HOST, PORT))
                s.send(bytes("PASS " + PASS + "\r\n", "utf-8"))
                s.send(bytes("NICK " + IDENT + "\r\n", "utf-8"))
                s.send(bytes("JOIN " + "#" +  CHANNEL + "\r\n", "utf-8"))
                s.send(bytes("PRIVMSG " + "#" + CHANNEL + " :" + "I HAVE ARRIVED!" + "\r\n", "utf-8"))
                return s
        except IndexError:
                pass
        
def sendMessage(s, message):
        messageTemp = "PRIVMSG " + "#" + CHANNEL + " :" + message
        s.send(bytes(messageTemp + "\r\n", "utf-8"))

def joinRoom(s):
        try:
                readbuffer = ""
                Loading = True
                while Loading:
                        decodedreadbuffer = (s.recv(1024).decode("utf-8"))
                        readbuffer = (readbuffer + decodedreadbuffer)
                        temp = string.split(str(readbuffer), "\n")
                        readbuffer = temp.pop()
                
                        for line in temp:
                                print(line)
                                Loading = loadingComplete(line)
        except AttributeError:
                pass
        
def loadingComplete(line):
        if("End of /NAMES list" in line):
                return False
        else:
                return True

def getChat(line):
        try:
                separate = line.split()
                chat = separate[2]
                return chat
        except IndexError:
                pass
        
def getUser(line):
        try:
                separate = line.split(":", 2)
                user = separate[1].split("!", 1)[0]
                return user
        except IndexError:
                pass
    
def getMessage(line):
        try:
                separate = line.split(":", 2)
                message = separate[2]
                return message
        except IndexError:
                pass

def twitchPing():
                while True:
                        s.send(bytes("PING :tmi.twitch.tv\r\n", "utf-8"))
                        time.sleep(240)


s = openSocket()
joinRoom(s)
print(colorama.ansi.clear_screen())
readbuffer = ""
TOGGLE = "OFF"
PingThread = threading.Thread(target=twitchPing)
PingThread.daemon = True
PingThread.start()

while True:
        readbuffer = ""
        decodedreadbuffer = (s.recv(2048).decode("utf-8"))
        readbuffer = readbuffer + decodedreadbuffer
        temp = readbuffer.split("\n")
        readbuffer = temp.pop()
        chatExclusions = ["tmi.twitch.tv", "", "#"+CHANNEL, "sharrubot"]
        for line in temp:
                user = getUser(line)
                message = getMessage(line)
                chat = getChat(line)
                if (str(chat).startswith("#")):
                        print (Style.BRIGHT + Fore.GREEN + str(chat) + " - " + Fore.RED + str(user) + ": " + Fore.WHITE + str(message) + Style.RESET_ALL)
                if (str(chat) not in (chatExclusions)) and str(message) != ("None") and (TOGGLE == "ON") and not str(message).startswith("!"):
                        s.send(bytes("PRIVMSG " + "#" + CHANNEL + " :" + str(chat) + " - " + str(user) + ": " + str(message) + "\r\n", "utf-8"))
                if str(message).startswith('!') and "!bye" in str(message) and str(user) in PERMISSIONS:
                        sendMessage(s, "Leaving chat!")
                        chatNum = len(connectedChats)
                        for i in range(chatNum):
                                s.send(bytes("PART " + "#" + connectedChats[i] + "\r\n", "utf-8"))
                                print("Leaving " + connectedChats[i] + "'s channel!")
                                time.sleep(0.1)
                        time.sleep(0.1)                        
                        sys.exit()
                if str(message).startswith('!') and "!part" in str(message) and str(user) in PERMISSIONS:
                        PART = str(message).split()
                        s.send(bytes("PRIVMSG " + "#" + PART[1].lower() + " :" + user + " has unlinked your chat from theirs! \r\n", "utf-8" ))
                        time.sleep(0.5)
                        try:
                                connectedChats.remove(PART[1].lower())
                                sendMessage(s, "Leaving " + PART[1].lower() + "'s chat!")
                                s.send(bytes("PART " + "#" + PART[1].lower() + "\r\n", "utf-8"))
                        except ValueError:
                                sendMessage(s, "Error: Not connected to " + PART[1].lower() + "'s chat!")
                if str(message).startswith('!') and "!connect" in str(message) and str(user) in PERMISSIONS:
                        CONNECT = str(message).split()
                        if CONNECT[1].lower() not in connectedChats:
                                s.send(bytes("JOIN " + "#" +  CONNECT[1].lower() + "\r\n", "utf-8"))
                                sendMessage(s, "Joining " +CONNECT[1].lower() + "'s chat!")
                                connectedChats.append(CONNECT[1].lower())
                                time.sleep(0.5)
                                s.send(bytes("PRIVMSG " + "#" + CONNECT[1].lower() + " :" + user + " has just connected their chat to yours!" + "\r\n", "utf-8"))
                        elif CONNECT[1].lower() in connectedChats:
                                sendMessage(s, "Already connected to that chat!")
                if str(message).startswith('!') and "!Toggle" in str(message) and (TOGGLE == "OFF") and str(user) in PERMISSIONS:
                        TOGGLE = "ON"
                        sendMessage(s, "Connected chat feature is now: " + TOGGLE)
                elif str(message).startswith('!') and "!Toggle" in str(message) and (TOGGLE == "ON") and str(user) in PERMISSIONS:
                        TOGGLE = "OFF"
                        sendMessage(s, "Connected chat feature is now: " + TOGGLE)
                if str(message).startswith('!') and "!shoutout" in str(message) and str(user) in PERMISSIONS:
                        SHOUT = str(message).split()
                        sendMessage(s, "Go watch " + SHOUT[1] + " over at https://www.twitch.tv/" + SHOUT[1])
                if str(message).startswith('!') and "!chats" in str(message) and str(user) in PERMISSIONS:
                        sendMessage(s, str(connectedChats))
                break



