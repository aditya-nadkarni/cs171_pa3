import os
import threading
import config
import sys
import queue
import time
from _thread import *
import socket

host = "127.0.0.1"

client_id_name = sys.argv[1]
client_id_int = int(client_id_name)

port = 8000 + client_id_int

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((host, port))

s.send("client".encode('ascii'))

#def listen():
#    while True:
#        msg = s.recv(1024)
#        print(msg.decode('ascii'))

#start_new_thread(listen, () )

while True:
    msg = input("Enter a command: ")
    s.send(msg.encode('ascii'))
    # try:
    #     msg = s.recv(1024)
    #     print(msg.decode('ascii'))
    # except:
    #     print("Disconnected from Server")
    #     break
    msg = s.recv(1024)
    if (not msg):
        print("Server is not available")
    print(msg.decode('ascii'))
s.close()
