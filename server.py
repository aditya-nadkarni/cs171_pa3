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

transactionQ = queue.Queue()
lamportQ = PriorityQueue()
release_list = OrderedDict()

#config
server_id = 1
other_server1 = 2
other_server2 = 3
server_name = "A"
client_name = "Alice"
file_name = "ledger1.txt"



resource_delay = 0
if len(sys.argv) == 2:
    resource_delay = int(sys.argv[1])
reply_counter = 0
lamport_time = 0
#network
Money = {"A": 100, "B": 100, "C":100}

portN = 9000 + server_id
sN = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sN.connect((host, portN))
print("NETWORK CONNECTED")

#client
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 8000 + server_id
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind((host, port))
serversocket.listen(5)
clientsocket, addr = serversocket.accept()
print("CLIENT CONNECTED")
f = open(file_name, 'w+')
f.close()

print("Server ", server_id, " started! (Logicial Time ", lamport_time, ")")
# def client():
#     while True:
#         msg = clientsocket.recv(1024)
#         print("From Client: ", msg.decode('ascii'))
#         sN.send(msg)

def eval_transaction(msg):
    global Money
    if msg == "":
        return 0
    values = msg.split(" ")
    if (Money[values[0]] - int(values[2])) < 0:
        return 0
    else:
        Money[values[0]] = Money[values[0]] - int(values[2])
        Money[values[1]] = Money[values[1]] + int(values[2])
        #UPDATE LEDGER
        return 1


def handle_critical_section():
    global lamport_time
    global transactionQ
    global lamportQ
    global reply_counter
    global f
    next_ts = (0, 0)
    if not lamportQ.empty():
        next_ts = lamportQ.queue[0]
    if (reply_counter == 2 and next_ts[1] == server_id): #DEPENDS ON SERVER
        #UPDATE ledger
        reply_counter = 0
        #print(lamportQ.queue)
        lamport_time += 1
        print("Run Critical Section for <", next_ts[0], ",", next_ts[1], "> (Logical time: ", lamport_time, ")")
        to_send = ""
        print("Ledger opened: ", time.time())
        time.sleep(resource_delay)
        if eval_transaction(transactionQ.queue[0]) == 1:
            print("Updating Ledger: ", transactionQ.queue[0], "Account: ", Money)
            with open(file_name, 'a') as f:
                f.write(transactionQ.queue[0] + "\n")
            to_send = transactionQ.queue[0]
            print("Request is valid")
            clientsocket.send("Transaction Completed".encode("ascii"))
        else:
            print("Request is invalid")
            clientsocket.send("Insufficient Funds".encode("ascii"))
        print("Ledger closed: ", time.time())
        lamport_time += 1
        send_msg1_release = toJson(other_server1, "release", lamportQ.queue[0], to_send)
        send_msg2_release = toJson(other_server2, "release", lamportQ.queue[0], to_send)
        #print("TYPE: ", type(send_msg1_release))
        e_send_msg1_release = json.dumps(send_msg1_release) + '\0'
        e_send_msg2_release = json.dumps(send_msg2_release) + '\0'
        sN.send(e_send_msg1_release.encode('ascii'))
        #lamport_time += 1
        sN.send(e_send_msg2_release.encode('ascii'))
        print("RELEASE for <", next_ts[0],",", next_ts[1], "> sent to all (Logical time: ", lamport_time, ")")

        lamportQ.get()
        transactionQ.get()
        if (not transactionQ.empty()):
            lamport_time += 1
            lt = (lamport_time, server_id)
            lamportQ.put(lt)
            send_msg1 = toJson(other_server1, "request", lt)
            send_msg2 = toJson(other_server2,  "request", lt)
            e_send_msg1 = json.dumps(send_msg1) + '\0'
            e_send_msg2 = json.dumps(send_msg2) + '\0'
            #print("Encoded: ", e_send_msg1)
            sN.send(e_send_msg1.encode('ascii'))
            #lamport_time += 1
            sN.send(e_send_msg2.encode('ascii'))
            print("REQUEST <", lt[0], ",", lt[1], "> sent to all.")

def toJson(destination, type, timestamp, payload = ""):
    return {'d': destination, 't': type, 'ts': timestamp, 'p': payload, 'l':(lamport_time, server_id)}

def network():
    global lamport_time
    global transactionQ
    global lamportQ
    global release_list
    global reply_counter
    global f
    while True:
        msg = sN.recv(1024)
        ##print("From Network: ", msg.decode('ascii').replace("\0", ""))
        txt = msg.decode('ascii')
        messages = list(filter(None, txt.split('\0')))
        for mes in messages:
            ##print("From Network: ", msg.decode('ascii'))
            d_msg = json.loads(mes)
            if (d_msg['t'] == "request"):
                #print("GOT REQUEST")
                lamport_time = max(lamport_time, d_msg['l'][0]) + 1
                #Add request to priority Queue sorted by lamport time
                print("REQUEST <", d_msg['ts'][0], ",", d_msg['ts'][1], "> received from server ", d_msg['l'][1], " (Logical time: ", lamport_time, ")")
                #Send Reply to origin
                #print("DEBUG: ", tuple(d_msg['ts']), " Queue: ", lamportQ.queue)
                lamportQ.put(tuple(d_msg['ts']))
                lamport_time += 1
                send_msg_reply = toJson(d_msg['l'][1], "reply", d_msg['ts'], d_msg['p'])
                e_send_msg_reply = json.dumps(send_msg_reply) + '\0'
                sN.send(e_send_msg_reply.encode('ascii'))
                print("REPLY for <", d_msg['ts'][0],",", d_msg['ts'][1], "> sent to server ", d_msg['l'][1], " (Logical time: ", lamport_time, ")")

            elif (d_msg['t'] == "reply"):
                #print("GOT REPLY")
                lamport_time = max(lamport_time, d_msg['l'][0]) + 1
                #Increment counter
                print("REPLY to <", d_msg['ts'][0],",", d_msg['ts'][1], "> received from server ", d_msg['l'][1], " (Logical time: ", lamport_time, ")")
                #if counter == 2, check if your request is in beginning of priority Queue, if yes update ledger, pop both Qs, Send next request if one
                reply_counter += 1
                #print("LAMPORT QUEUE: ")
                ##print(lamportQ.queue)
                #print("TYPE: ", type(list(lamportQ.items())[0][1]))
                start_new_thread(handle_critical_section, () )


            elif (d_msg['t'] == "release"):
                #print("GOT RELEASE")
                lamport_time = max(lamport_time, d_msg['l'][0]) + 1
                #if not failure
                print("RELEASE <", d_msg['ts'][0],",", d_msg['ts'][1], "> received from server ", d_msg['l'][1], " (Logical time: ", lamport_time, ")")
                #print(lamportQ.queue)
                release_list[tuple(d_msg['ts'])] = d_msg

                #while(result.popitem(last=False))
                while(list(release_list)[0] == lamportQ.queue[0]):
                    f_msg = list(release_list.values())[0]
                    if (f_msg['p']):
                        with open(file_name, 'a') as f:
                            f.write(f_msg['p'] + "\n")
                        eval_transaction(f_msg['p'])
                        print("Updating Ledger: ", f_msg['p'], "Account: ", Money)
                    lamportQ.get()
                    release_list.popitem(last=False)
                    if (len(release_list) == 0):
                        break
                start_new_thread(handle_critical_section, () )

start_new_thread(network, () )
#start_new_thread(client, () )


while True:
    msg = clientsocket.recv(1024)
    lamport_time += 1
    txtm = msg.decode('ascii')
    print("Transaction received from ", client_name, " (Logical time: ", lamport_time, ")")
    if (transactionQ.empty()):
        #Send request
        lamport_time += 1
        lt = (lamport_time, server_id)
        lamportQ.put(lt)
        send_msg1 = toJson(other_server1, "request", lt, txtm)
        send_msg2 = toJson(other_server2,  "request", lt, txtm)
        e_send_msg1 = json.dumps(send_msg1) + '\0'
        e_send_msg2 = json.dumps(send_msg2) + '\0'
        #print("Encoded: ", e_send_msg1)
        sN.send(e_send_msg1.encode('ascii'))
        lamport_time += 1
        sN.send(e_send_msg2.encode('ascii'))
        print("REQUEST <", lt[0], ",", lt[1], "> sent to all.")
    transactionQ.put(txtm)

print("DEAD S1")
