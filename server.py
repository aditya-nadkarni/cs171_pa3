import os
import threading
import config
import sys
import queue
import random
from _thread import *
import socket
import json
import time
from queue import PriorityQueue
from collections import OrderedDict

host = "127.0.0.1"

#TO DO:
#LOCKS
#Globsl acknowledge counter, accept counter, last accepted Val, last accepted Num,


#config
server_id_name = sys.argv[1]
server_id_int = int(server_id_name)
other_server_ids = set(["1", "2", "3", "4", "5"]) - set([server_id_name])
num_servers = 5
majority = int(num_servers/2 + 1)

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

ACK_COUNTER = 0 # Number of acknowledgements received by proposer in phase 1
ACC_COUNTER = 0 # Number of accepts received by proposer in phase 2
ACC_NUM = (0, 0, 0) # Last accepted ballot number in phase 2
ACC_VAL = None # last accepted value in phase 2
BALLOT_NUM = (0, 0, 0) # Highest received ballot number by acceptor
PROP_BAL_NUM = (0, 0, 0) # Highest received ballot number by Proposer from an ack in phase 1
PROP_BAL_VAL = None # Highest received ballot number's value by Proposer from an ack in phase 1
MY_VAL = 0

def send_msg(socketName, msg):
    #rand int between 1 and 5
    delay = random.randint(1,5)
    sleep(delay)
    sockName.send(msg)

def check_ack_num():
    sleep(25)
    if (ACK_COUNTER < majority):
        ACK_COUNTER = 0
        print("Send new proposal w/ new ballot num")
        #send new proposal

#Job of acceptor in paxos
def listen_to_server(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    global ACK_COUNTER  # Number of acknowledgements received by proposer in phase 1
    global ACC_COUNTER # Number of accepts received by proposer in phase 2
    global ACC_NUM # Last accepted ballot number in phase 2
    global ACC_VAL # last accepted value in phase 2
    global BALLOT_NUM # Highest received ballot number by acceptor
    global PROP_BAL_NUM # Highest received ballot number by Proposer from an ack in phase 1
    global PROP_BAL_VAL # Highest received ballot number's value by Proposer from an ack in phase 1
    while True:
        print("listen_to_server: ", socketName)
        try:
            msg = conn_socket.recv(1024)
            print("Message: ", msg)
            if (not msg):
                print ("Disconnected from:", socketName)
                del sockets[socketName]
                break
            print(socketName, "received the message: ", msg.decode('ascii'))
        except socket.error:
            print ("Disconnected")
            del sockets[socketName]
            break
        except KeyError:
            print("We fucked up")
        #msg = conn_socket.recv(1024)
        #print(socketName, "received the message: ", msg.decode('ascii'))
        msg_decoded = msg.decode('ascii')
        msg_dict = json.loads(msg_decoded)

        msg_type = msg_dict['msg']

        if (msg_type == "prepare"):
            bal = tuple(msg_dict['bal'])
            if (bal >= BALLOT_NUM):
                    #USE LOCK
                    BALLOT_NUM = bal
                    #LOCK

                    # SEND "ACK" to bal[1] (proc_id)
                    ack_msg = toPaxosDict("ack", bal[0], bal[1], bal[2], None, ACC_NUM, ACC_VAL)
                    ack_string = json.dumps(ack_msg)

                    start_new_thread(send_msg, (sockets[bal[1]], ack_string.encode('ascii')))
            elif(bal[2] < DEPTH):
                #Update the sucker with blockchain
                print("Need to send updated block chain to:", bal[1])
                pass
        elif (msg_type == "ack"):
            bal = tuple(msg_dict['bal'])
            if bal == (SEQUENCE_NUMBER, server_id_int, DEPTH):
                ACK_COUNTER += 1

                if(bal >= PROP_BAL_NUM):
                        PROP_BAL_NUM = bal
                        PROP_BAL_VAL = msg_dict['aVal']
                        MY_VAL = PROP_BAL_VAL

                if(ACK_COUNTER >= majority):
                    #send accept-request to everyone
                    acc_req_msg = toPaxosDict("accept-request", bal[0], bal[1], bal[2], MY_VAL)
                    acc_req_string = json.dumps(acc-req_msg)

                    for s_id in other_server_ids: #To do: add partition functionality, make other_server_ids a parameter
                        if s_id in sockets:
                            start_new_thread(send_msg, (sockets[s_id], acc_req_string.encode('ascii')))

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

def paxosProposal():
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    SEQUENCE_NUMBER += 1
    proposal = toPaxosDict("prepare", SEQUENCE_NUMBER, server_id_int, DEPTH)
    proposal_string = json.dumps(proposal) #MAYBE ADD SEPERATING CHARACTERS
    for s_id in other_server_ids: #To do: add partition functionality, make other_server_ids a parameter
        if s_id in sockets:
            start_new_thread(send_msg, (sockets[s_id], proposal_string.encode('ascii')))
            #sockets[s_id].send(proposal_string.encode('ascii'))
    start_new_thread(check_ack_num, ())
    # NOW gotta wait for acks from everyone, then listener thread will start Proposal Phase 2 thread. HOWEVER need timeout in case no acks come in



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
    MY_VAL = 7777
    start_new_thread(paxosProposal, ()) #Thread and add delay




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
