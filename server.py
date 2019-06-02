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
port = 8000 + int(server_id) #Use config later
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((host, port))
serversocket.listen(5)

sockets = dict()

#def connections():


#start_new_thread(connections, () )

def handle_connection(socketName, clientSocket):
    while True:
        msg = clientSocket.recv(1024)
        print(socketName, "received the message: ", msg.decode('ascii'))

while True:
    clientsocket, addr = serversocket.accept()
    print("CLIENT ACCEPTED")

    msg = clientsocket.recv(1024)
    socket_name = msg.decode('ascii')
    sockets[socket_name] = clientsocket
    print("CLIENT CONNECTED", socket_name)
    start_new_thread(handle_connection, (socket_name, clientsocket) ) #Temporary, later switch to 5 distinct threads that are limited.
