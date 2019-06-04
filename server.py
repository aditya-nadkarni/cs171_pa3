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
server_id_name = sys.argv[1]
server_id_int = int(server_id_name)
other_server_ids = set(["1", "2", "3", "4", "5"]) - set([server_id_name])

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#serversocket.settimeout(20)
port = 8000 + server_id_int #Use config later
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((host, port))
serversocket.listen(5)


sockets = dict() #Make global


TRANS = [] #Make global
BLOCKCHAIN = [] #Make global

SEQUENCE_NUMBER = 0 #Make global
DEPTH = 0 #Make global

#Job of acceptor in paxos
def listen_to_server(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    while True:
        print("listen_to_server: ", socketName)
        try:
            msg = conn_socket.recv(1024)
            print("Message: ", msg)
            if (not msg):
                print ("Disconnected")
                break
            print(socketName, "received the message: ", msg.decode('ascii'))
        except socket.error:
            print ("Disconnected")
            break
        #msg = conn_socket.recv(1024)
        #print(socketName, "received the message: ", msg.decode('ascii'))
        msg_decoded = msg.decode('ascii')
        msg_dict = json.loads(msg_decoded)

        msg_type = msg_dict['msg']

        if (msg_type == "prepare"):
            pass
        elif (msg_type == "ack"):
            pass
        elif (msg_type == "accept_request"):
            pass
        elif (msg_type == "accept"):
            pass
        elif (msg_type == "decision"):
            pass




# Message Structure:

def toPaxosDict(message_type, seq_num, proc_id, depth, value = None, acceptNum = None, acceptVal = None):
    return {'msg': message_type, 'bal': (seq_num, proc_id, depth), 'val': value, 'aNum': acceptNum, 'aVal': acceptVal}

#ballot = {"seq_num":, "proc_id":, "depth":}

#prepare = {"prepare", ballot}

#ack = {"ack", ...}

def paxosProposal(value):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    proposal = toPaxosProposal("prepare", SEQUENCE_NUMBER, server_id_int, DEPTH)
    proposal_string = json.dumps(proposal) #MAYBE ADD SEPERATING CHARACTERS
    for s_id in other_server_ids: #To do: add partition functionality, make other_server_ids a parameter
        sockets[s_id].send(proposal_string.encode('ascii'))



def moneyTransfer(socketName, conn_socket, amount, client1, client2):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    print("Sending Transaction to server: ", socketName)

    #Mine Nonce Here!!!!

    conn_socket.send("Added Transaction To TRANS: ".encode('ascii'))
    #Initiate Paxos
    value = 1
    paxosProposal(value)




def printBlockchain(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    print("Printing Blockchain: ")
    conn_socket.send("Printing Blockchain: ".encode('ascii'))

def printBalance(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    print("Printing Balance: ")
    conn_socket.send("Printing Balance: ".encode('ascii'))

def printSet(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    print("Printing Set: ")
    conn_socket.send("Printing Set: ".encode('ascii'))


def listen_to_client(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    while True:
        print("listen_to_client")
        try:
            msg = conn_socket.recv(1024)
            print("Message: ", msg)
            if (not msg):
                print ("Disconnected")
                break
            print(socketName, "received the message: ", msg.decode('ascii'))
        except socket.error:
            print ("Disconnected")
            break
        #msg = conn_socket.recv(1024)
        #print(socketName, "received the message: ", msg.decode('ascii'))
        msg_decoded = msg.decode('ascii')
        if (msg_decoded == "printBlockchain"):
            printBlockchain(socketName, conn_socket)
        elif (msg_decoded == "printBalance"):
            printBalance(socketName, conn_socket)
        elif (msg_decoded == "printSet"):
            printSet(socketName, conn_socket)
        elif (msg_decoded.find("moneyTransfer") != -1):
            stripped_msg = msg_decoded.replace(" ", "")
            open_paren = stripped_msg.find("(")
            comma1 = stripped_msg.find(",", open_paren + 2)
            comma2 = stripped_msg.find(",", comma1 + 2)
            close_paren  = stripped_msg.find(")", comma2 + 2)
            if (open_paren != -1 and comma1 != -1 and comma2 != -1 and close_paren != -1):
                amount = int(stripped_msg[open_paren + 1: comma1])
                print("Amount: ", amount)
                client1 = stripped_msg[comma1 + 1: comma2]
                print("Client 1: ", client1)
                client2 = stripped_msg[comma2 + 1: close_paren]
                print("Client 2: ", client2)
                moneyTransfer(socketName, conn_socket, amount, client1, client2)
            else:
                print("Invalid parameters")
                conn_socket.send("Invalid parameters".encode('ascii'))
        else:
            print("Invalid command")
            conn_socket.send("Invalid Command".encode('ascii'))



def handle_connection(socketName, clientSocket):
    print("handle_connection with ", socketName)
    if (socketName == "client"):
        start_new_thread(listen_to_client, (socketName, clientSocket) )
    else:
        start_new_thread(listen_to_server, (socketName, clientSocket) )


#BOOT UP PROTOCOL



def ConnectWithServers():
    print("Connect With Servers")
    #Connect with every other server
    for s_id in other_server_ids:
        print ("Considering a connection with:", s_id)
        if s_id not in sockets:
            print ("Trying to connect with:", s_id)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s_port = 8000 + int(s_id)
                s.connect((host, s_port))
                print("Connected with", s_id)
                s.send(server_id_name.encode('ascii'))
                start_new_thread(listen_to_server, (s_id, s) )
            except:
                print("Failed to connect with", s_id)
                pass
        else:
            print("Already connected with ", s_id, ". Is this even possible?")



##################################################################################
ConnectWithServers()

while True:
    print("Main Loop")
    clientsocket, addr = serversocket.accept()
    print("NEW CONNECTION ACCEPTED")

    msg = clientsocket.recv(1024)
    socket_name = msg.decode('ascii')
    sockets[socket_name] = clientsocket
    print("NEW CONNECTION CONNECTED", socket_name)
    #start_new_thread(handle_connection, (socket_name, clientsocket) ) #Temporary, later switch to 5 distinct threads that are limited.
    handle_connection(socket_name, clientsocket)
