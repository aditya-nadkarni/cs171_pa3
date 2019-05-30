import os
import threading
import config
import sys
import queue
import time
from _thread import *
import socket

host = "127.0.0.1"

port = 8001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((host, port))

#def listen():
#    while True:
#        msg = s.recv(1024)
#        print(msg.decode('ascii'))

#start_new_thread(listen, () )

while True:
    msg = input("Enter a transaction: ")
    s.send(msg.encode('ascii'))
    print("Transaction sent to server ", 1)
    msg2 = s.recv(1024)
    print(msg2.decode('ascii'))
s.close()
