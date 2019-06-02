import os
import threading
import config
import sys
import queue
import time
from _thread import *
import socket

host = "127.0.0.1"

client_id = int(sys.argv[1])

port = 8000 + client_id

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((host, port))

s.send(sys.argv[1].encode('ascii'))

#def listen():
#    while True:
#        msg = s.recv(1024)
#        print(msg.decode('ascii'))

#start_new_thread(listen, () )

while True:
    msg = input("Enter a command: ")
    s.send(msg.encode('ascii'))
s.close()
