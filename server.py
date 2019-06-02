import os
import threading
import config
import sys
import queue
from _thread import *
import socket
import json
import time
from queue import PriorityQueue
from collections import OrderedDict

host = "127.0.0.1"



#config
server_id = sys.argv[1]


serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = config.config[server_id]["server_port"]
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((host, port))
serversocket.listen(5)

sockets = dict()

def connections():
    while True:
        clientsocket, addr = serversocket.accept()
        print("CLIENT CONNECTED")

        msg = clientsocket.recv(1024)
        socket_name = msg.decode('ascii')
        sockets[socket_name] = clientsocket

start_new_thread(connections, () )

while True:
    msg = clientsocket.recv(1024)
    print(msg.decode('ascii'))
