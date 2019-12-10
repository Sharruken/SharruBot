#!/usr/bin/env python3
import string
import socket
import sys
import time
import os
import subprocess
import logging
import threading
import re
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
CHANNEL = input("Please input the channel you would like me to connect to or blank to connect to your default(" + CONFIG[0] + "):\r\n")
if (CHANNEL == ""):
        CHANNEL = CONFIG[0]
PERMISSIONS_FILE = open("PERMISSIONS.txt")
PERMISSIONS = list(line.rstrip('\n') for line in PERMISSIONS_FILE.readlines())
PERMISSIONS_FILE.close()
connectedChats = [CHANNEL]
Active = "True"
chat = ""
excludedCommands = ['!bye', '!connect', '!part', '!shoutout', '!toggle', 'toggletimer', '!addcom']

def openSocket():
        try:
                s = socket.socket()
                s.connect((HOST, PORT))
                s.send(bytes("PASS " + PASS + "\r\n", "utf-8"))
                s.send(bytes("NICK " + IDENT + "\r\n", "utf-8"))
                s.send(bytes("JOIN " + "#" +  CHANNEL + "\r\n", "utf-8"))
                s.send(bytes("PRIVMSG " + "#" + CHANNEL + " :" + "/me is now live in this chat!\r\n", "utf-8"))
                return s
        except IndexError:
                pass
        
def sendMessage(s, message):
        messageTemp = "PRIVMSG " + chat + " :" + message
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
        while Active == "True":
                s.send(bytes("PING :tmi.twitch.tv\r\n", "utf-8"))
                time.sleep(240)
                
def timerMessage():
        while ActiveTimer == "True":
                sendMessage(s, "Join me on my discord where you'll be able to see when I go live, have some input on what I'm going to be playing on stream and maybe there will be some 'stream after  the stream' type stuff going on there! https://discord.gg/6nbMJM5")
                time.sleep(1800)

s = openSocket()
joinRoom(s)
print(colorama.ansi.clear_screen())
readbuffer = ""
TOGGLE = "OFF"
ActiveTimer = "OFF"
PingThread = threading.Thread(target=twitchPing)
TimerThread = threading.Thread(target=timerMessage)
PingThread.daemon = True
TimerThread.daemon = True
PingThread.start()
TimerThread.start()

while Active == "True":
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
                        Active = "False"
                if str(message).startswith('!') and "!part" in str(message) and str(user) in PERMISSIONS:
                        try:
                                PART = str(message).split()
                                s.send(bytes("PRIVMSG " + "#" + PART[1].lower() + " :" + user + " has unlinked your chat from theirs! \r\n", "utf-8" ))
                                time.sleep(0.5)
                                connectedChats.remove(PART[1].lower())
                                sendMessage(s, "Leaving " + PART[1].lower() + "'s chat!")
                                s.send(bytes("PART " + "#" + PART[1].lower() + "\r\n", "utf-8"))
                        except:
                                pass
                if str(message).startswith('!') and "!connect" in str(message) and str(user) in PERMISSIONS:
                        try:
                                CONNECT = str(message).split()
                                if CONNECT[1].lower() not in connectedChats:
                                        s.send(bytes("JOIN " + "#" +  CONNECT[1].lower() + "\r\n", "utf-8"))
                                        sendMessage(s, "Joining " +CONNECT[1].lower() + "'s chat!")
                                        connectedChats.append(CONNECT[1].lower())
                                        time.sleep(0.5)
                                        s.send(bytes("PRIVMSG " + "#" + CONNECT[1].lower() + " :" + user + " has just connected "+ chat + "'s chat to yours!" + "\r\n", "utf-8"))
                                elif CONNECT[1].lower() in connectedChats:
                                        sendMessage(s, "Already connected to that chat!")
                        except:
                                pass
                if str(message).startswith('!') and "!toggle" in str(message) and (TOGGLE == "OFF") and str(user) in PERMISSIONS:
                        TOGGLE = "ON"
                        sendMessage(s, "Connected chat feature is now: " + TOGGLE)
                elif str(message).startswith('!') and "!toggle" in str(message) and (TOGGLE == "ON") and str(user) in PERMISSIONS:
                        TOGGLE = "OFF"
                        sendMessage(s, "Connected chat feature is now: " + TOGGLE)
                if str(message).startswith('!') and "!toggletimer" in str(message) and (ActiveTimer == "OFF") and str(user) in PERMISSIONS:
                        ActiveTimer = "ON"
                        sendMessage(s, "Timers are now: " + ActiveTimer)
                if str(message).startswith('!') and "!toggletimer" in str(message) and (ActiveTimer == "OFF") and str(user) in PERMISSIONS:
                        ActiveTimer = "OFF"
                        sendMessage(s, "Timers are now: " + ActiveTimer)
                if str(message).startswith('!') and "!shoutout" in str(message) and str(user) in PERMISSIONS:
                        try:
                                SHOUT = str(message).split()
                                sendMessage(s, "Go watch " + SHOUT[1] + " over at https://www.twitch.tv/" + SHOUT[1])
                        except:
                                pass
                if str(message).startswith('!') and "!chats" in str(message) and str(user) in PERMISSIONS:
                        sendMessage(s, str(connectedChats))
                if str(message).startswith('!') and message[0] not in excludedCommands:
                        try:
                                COMMANDS_FILE = open("COMMANDS.txt")
                                COMMANDS = list(line.rstrip('\n') for line in COMMANDS_FILE.readlines())
                                commandSTR = str(message).split()
                                chatCommand = COMMANDS.index(commandSTR[0])
                                sendMessage(s, COMMANDS[chatCommand+1])
                                COMMANDS_FILE.close()
                        except:
                                pass
                if str(message).startswith('!') and "!addcom" in str(message) and str(user) in PERMISSIONS:
                        try:
                                COMMANDTOADD = str(message).split("'")
                                COMMAND1 = COMMANDTOADD[0].split()
                                COMMANDS_FILE = open("COMMANDS.txt", "a+")
                                COMMANDS_FILE.write(COMMAND1[1]+"\n")
                                COMMANDS_FILE.write(''.join(map(str, COMMANDTOADD[1:])))
                                COMMANDS_FILE.close()
                                sendMessage(s, COMMAND1[1]+" command added!")
                        except:
                                sendMessage(s, "Unable to add this command, please ensure it's in the format of !addcom !command 'message to display' including the quotation marks")
                break



