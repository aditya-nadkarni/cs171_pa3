import os
import threading
from threading import Lock
import config
import sys
import queue
import random
from _thread import *
import socket
import json
import time
import hashlib
import string
from queue import PriorityQueue
from collections import OrderedDict

host = "127.0.0.1"

'''
    ** TODO:
        * LOCKS
        * Finish rest of client functions
'''

'''
    ***** CONFIG VARIABLES *****
'''
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
TRANS_LOCK = Lock() #Lock for TRANS

BLOCKCHAIN = [] #Make global
BLOCKCHAIN_LOCK = Lock()

SEQUENCE_NUMBER = 0 #Make global
SEQUENCE_NUM_LOCK = Lock()
DEPTH = 0 #Make global
DEPTH_LOCK = Lock()

BLOCK_SIZE = 2
moneyz = {"A": 100, "B": 100, "C": 100, "D": 100, "E": 100}
moneyz_LOCK = Lock()

'''
    ***** HELPER FUNCTIONS *****
'''
def send_msg(socketName, msg):
    #rand int between 1 and 5
    delay = random.randint(1,2)
    time.sleep(delay)
    socketName.send(msg)

def decodeStringTuple(str):
    stripped_msg = str.replace(" ", "")
    open_paren = stripped_msg.find("(")
    comma1 = stripped_msg.find(",", open_paren + 2)
    comma2 = stripped_msg.find(",", comma1 + 2)
    close_paren  = stripped_msg.find(")", comma2 + 2)
    if (open_paren != -1 and comma1 != -1 and comma2 != -1 and close_paren != -1):
        amount = int(stripped_msg[open_paren + 1: comma1])
        client1 = stripped_msg[comma1 + 1: comma2]
        client2 = stripped_msg[comma2 + 1: close_paren]
        return amount, client1, client2
    return -1, -1, -1



'''
    ***** PROPOSER GLOBAL VARIABLES *****
'''
ACK_COUNTER = 0 # Number of acknowledgements received by proposer in phase 1
ACK_COUNTER_LOCK = Lock()

ACC_COUNTER = 0 # Number of accepts received by proposer in phase 2
ACC_COUNTER_LOCK = Lock()

PROP_BAL_NUM = (DEPTH, 0, 0) # Highest received ballot number by Proposer from an ack in phase 1
PROP_BAL_NUM_LOCK = Lock()

PROP_BAL_VAL = None # Highest received ballot number's value by Proposer from an ack in phase 1
PROP_BAL_VAL_LOCK = Lock()

'''
    ***** ACCEPTOR GLOBAL VARIABLES *****
'''
MY_VAL = 0
MY_VAL_LOCK = Lock()

ACC_NUM = (DEPTH, 0, 0) # Last accepted ballot number in phase 2
ACC_NUM_LOCK = Lock()

ACC_VAL = None # last accepted value in phase 2
ACC_VAL_LOCK = Lock()

BALLOT_NUM = (DEPTH, 0, 0) # Highest received ballot number by acceptor
BALLOT_NUM_LOCK = Lock()

'''
    ***** PAXOS FUNCTIONS *****
'''
#Create paxos message dict from params
def toPaxosDict(message_type, depth, seq_num, proc_id, value = None, acceptNum = None, acceptVal = None):
    return {'msg': message_type, 'bal': (depth, seq_num, proc_id), 'val': value, 'aNum': acceptNum, 'aVal': acceptVal}

#Initializes the PAXOS run
# Checks if 2 transactions in Trans. If true, continue
#     Get currentDepth, sequence, number from globals, 2 top transactions from q. Form a partial block
#     MineNonce() from partial block. Create full block
#     Call paxosProposal() with Block
#     Call TimeOut Function
def initiatePaxos(n = 2):
    global TRANS
    if len(TRANS) >= BLOCK_SIZE:
        #Form block (just transactions concatenated for now)
        # blockVal = ""
        # for i in range(BLOCK_SIZE):
        #     if i < (BLOCK_SIZE - 1):
        #         blockVal = blockVal + TRANS[i] + ";"
        #     else:
        #         blockVal = blockVal + TRANS[i]

        #Verify transaction are legal
        allLegal = True
        for i in range(BLOCK_SIZE):
            amount, src, dest = decodeStringTuple(TRANS[i])

            if (moneyz[src]-amount) < 0:
                allLegal = False

                TRANS_LOCK.acquire()
                del TRANS[i]
                TRANS_LOCK.release()

                print("Invalid Transaction Detected..")

        #Form block if all legal
        if allLegal:
            blockVal = create_block()
            #Mine nonce

            #Call paxosProposal() with block
            paxosProposal(blockVal)

            #Call timeOut Function
            if n < 32:
                timeOut(n)
            else:
                timeOut(2)
        else:
            initiatePaxos()


#Sleep exponentially increasing seconds, then call initiatePaxos() again
def timeOut(n):
    time.sleep(15 + n)
    initiatePaxos(2**n)

#Sends "prepare" request to start Phase 1 of Proposer
def paxosProposal(blockVal):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    global PROP_BAL_NUM
    global PROP_BAL_VAL
    global MY_VAL

    MY_VAL_LOCK.acquire()
    MY_VAL = blockVal
    MY_VAL_LOCK.release()

    SEQUENCE_NUM_LOCK.acquire()
    SEQUENCE_NUMBER += 1
    SEQUENCE_NUM_LOCK.release()

    proposal = toPaxosDict("prepare", DEPTH, SEQUENCE_NUMBER, server_id_int)
    
    PROP_BAL_NUM_LOCK.acquire()
    PROP_BAL_NUM = (DEPTH, SEQUENCE_NUMBER, server_id_int)
    PROP_BAL_NUM_LOCK.release()

    PROP_BAL_VAL_LOCK.acquire()
    PROP_BAL_VAL = MY_VAL
    PROP_BAL_VAL_LOCK.release()

    proposal_string = json.dumps(proposal) + '\0' #MAYBE ADD SEPERATING CHARACTERS
    for s_id in other_server_ids: #To do: add partition functionality, make other_server_ids a parameter
        if s_id in sockets:
            start_new_thread(send_msg, (sockets[s_id], proposal_string.encode('ascii')))
            #sockets[s_id].send(proposal_string.encode('ascii'))
    # NOW gotta wait for acks from everyone, then listener thread will start Proposal Phase 2 thread

#Listening on given server socket (Only used for PAXOS messages)
#Gets message, decides what to do with it
#Job of proposer/acceptor in paxos
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
    global MY_VAL

    while True:
        try:
            all_msg = conn_socket.recv(1024)
            # print("Message: ", msg)
            if (not all_msg):
                print ("Disconnected from:", socketName)
                del sockets[socketName]
                break
        except socket.error:
            print ("Disconnected")
            del sockets[socketName]
            break
        except KeyError:
            print("We fucked up")
        #msg = conn_socket.recv(1024)
        #print(socketName, "received the message: ", msg.decode('ascii'))


        txt = all_msg.decode('ascii')
        messages = list(filter(None, txt.split('\0')))

        # print("*  <*> ALL MESSAGES:", messages)
        print("NUMBER OF MESSAGES: ", len(messages))
        if(len(messages) > 1):
            print (messages)
        for msg in messages:
            print("MSG:", msg)

            msg_dict = json.loads(msg)

            msg_type = msg_dict['msg']

            #On acceptor
            if (msg_type == "prepare"):
                bal = tuple(msg_dict['bal'])
                if (bal >= BALLOT_NUM):
                        #USE LOCK
                        BALLOT_NUM_LOCK.acquire()
                        BALLOT_NUM = bal
                        BALLOT_NUM_LOCK.release()

                        SEQUENCE_NUM_LOCK.acquire()
                        SEQUENCE_NUMBER = bal[1]
                        SEQUENCE_NUM_LOCK.release()
                        #LOCK

                        # SEND "ACK" to bal[1] (proc_id)
                        ack_msg = toPaxosDict("ack", bal[0], bal[1], bal[2], None, ACC_NUM, ACC_VAL)
                        ack_string = json.dumps(ack_msg) + '\0'
                        start_new_thread(send_msg, (sockets[str(bal[2])], ack_string.encode('ascii')))
                elif(bal[0] < DEPTH):
                    #Update the sucker with blockchain
                    #print("Need to send updated block chain to:", bal[1])
                    #pass
                    origin = bal[2]
                    #Send UPDATE back to origin
                    up_msg = toPaxosDict("update", DEPTH, SEQUENCE_NUMBER, server_id_int, BLOCKCHAIN)
                    up_string = json.dumps(up_msg) + '\0'
                    start_new_thread(send_msg, (sockets[str(origin)], up_string.encode('ascii')))
            #On proposer
            elif (msg_type == "ack"):
                bal = tuple(msg_dict['bal'])
                if bal == (DEPTH, SEQUENCE_NUMBER, server_id_int):
                    ACK_COUNTER_LOCK.acquire()
                    ACK_COUNTER += 1
                    ACK_COUNTER_LOCK.release()

                    if(msg_dict['aVal'] and bal >= PROP_BAL_NUM):
                            SEQUENCE_NUM_LOCK.acquire()
                            SEQUENCE_NUMBER = bal[1]
                            SEQUENCE_NUM_LOCK.release()

                            PROP_BAL_NUM_LOCK.acquire()
                            PROP_BAL_NUM = bal
                            PROP_BAL_NUM_LOCK.release()

                            PROP_BAL_VAL_LOCK.acquire()
                            PROP_BAL_VAL = msg_dict['aVal']
                            PROP_BAL_VAL_LOCK.release()

                            MY_VAL_LOCK.acquire()
                            MY_VAL = PROP_BAL_VAL
                            MY_VAL_LOCK.release()

                    if(ACK_COUNTER >= majority):
                        ACK_COUNTER_LOCK.acquire()
                        ACK_COUNTER = 0
                        ACK_COUNTER_LOCK.release()

                        #send accept-request to everyone
                        # print("MY_VAL (acc-req):", MY_VAL)
                        acc_req_msg = toPaxosDict("accept-request", bal[0], bal[1], bal[2], MY_VAL)
                        acc_req_string = json.dumps(acc_req_msg) + '\0'

                        ACC_NUM_LOCK.acquire()
                        ACC_NUM = bal
                        ACC_NUM_LOCK.release()
                        
                        ACC_VAL_LOCK.acquire()
                        ACC_VAL = MY_VAL
                        ACC_VAL_LOCK.release()

                        ACC_COUNTER_LOCK.acquire()
                        ACC_COUNTER += 1
                        ACC_COUNTER_LOCK.release()

                        for s_id in other_server_ids: #To do: add partition functionality, make other_server_ids a parameter
                            if s_id in sockets:
                                start_new_thread(send_msg, (sockets[s_id], acc_req_string.encode('ascii')))
            #On acceptor
            elif (msg_type == "accept-request"):
                bal = tuple(msg_dict['bal'])
                # print("BALLOT_NUM:", BALLOT_NUM)
                if(bal >= BALLOT_NUM):
                    SEQUENCE_NUM_LOCK.acquire()
                    SEQUENCE_NUMBER = bal[1]
                    SEQUENCE_NUM_LOCK.release()

                    ACC_NUM_LOCK.acquire()
                    ACC_NUM = bal
                    ACC_NUM_LOCK.release()

                    ACC_VAL_LOCK.acquire()
                    ACC_VAL = msg_dict['val']
                    ACC_VAL_LOCK.release()

                    #send accept back to bal[1]
                    acc_msg = toPaxosDict("accept", bal[0], bal[1], bal[2], ACC_VAL, ACC_NUM, ACC_VAL)
                    acc_string = json.dumps(acc_msg) + '\0'

                    start_new_thread(send_msg, (sockets[str(bal[2])], acc_string.encode('ascii')))
            #On proposer
            elif (msg_type == "accept"):
                bal = tuple(msg_dict['bal'])
                if bal == (DEPTH, SEQUENCE_NUMBER, server_id_int):
                    ACC_COUNTER_LOCK.acquire()
                    ACC_COUNTER += 1
                    ACC_COUNTER_LOCK.release()

                    if(ACC_COUNTER >= majority):
                        print("Adding Block to Blockchain: ", msg_dict['val'])

                        BLOCKCHAIN_LOCK.acquire()
                        BLOCKCHAIN.append(msg_dict['val'])
                        BLOCKCHAIN_LOCK.release()

                        DEPTH_LOCK.acquire()
                        DEPTH += 1
                        DEPTH_LOCK.release()

                        #get transactions from block value
                        blockTrans = json.loads(msg_dict['val'])['transactions']
                        print("Block Trans: ", blockTrans)
                        print("TRANS: ", TRANS)
                        #Delete from TRANS if your transactions were added
                        if len(TRANS) >= BLOCK_SIZE:
                            isSame = True
                            for i in range(BLOCK_SIZE):
                                if blockTrans[i] != TRANS[i]:
                                    isSame = False
                                    break
                            if(isSame):
                                TRANS_LOCK.acquire()
                                del TRANS[0:BLOCK_SIZE]
                                TRANS_LOCK.release()

                        for trans in blockTrans:
                            amount, src, dest = decodeStringTuple(trans)

                            moneyz_LOCK.acquire()
                            moneyz[dest] += amount
                            moneyz[src] -= amount
                            moneyz_LOCK.release()

                        #send accept-request to everyone
                        dec_msg = toPaxosDict("decision", bal[0], bal[1], bal[2], msg_dict['val'])
                        dec_string = json.dumps(dec_msg) + '\0'
                        
                        # ** Delay sending decision (for testing purposes)
                        time.sleep(10)
                        for s_id in other_server_ids: #To do: add partition functionality, make other_server_ids a parameter
                            if s_id in sockets:
                                start_new_thread(send_msg, (sockets[s_id], dec_string.encode('ascii')))

                        ACK_COUNTER_LOCK.acquire()
                        ACK_COUNTER = 0 # Number of acknowledgements received by proposer in phase 1
                        ACK_COUNTER_LOCK.release()

                        ACC_COUNTER_LOCK.acquire()
                        ACC_COUNTER = 0 # Number of accepts received by proposer in phase 2
                        ACC_COUNTER_LOCK.release()

                        ACC_NUM_LOCK.acquire()
                        ACC_NUM = (DEPTH, 0, 0) # Last accepted ballot number in phase 2
                        ACC_NUM_LOCK.release()

                        ACC_VAL_LOCK.acquire()
                        ACC_VAL = None # last accepted value in phase 2
                        ACC_VAL_LOCK.release()

                        BALLOT_NUM_LOCK.acquire()
                        BALLOT_NUM = (DEPTH, 0, 0) # Highest received ballot number by acceptor
                        BALLOT_NUM_LOCK.release()

                        PROP_BAL_NUM_LOCK.acquire()
                        PROP_BAL_NUM = (DEPTH, 0, 0) # Highest received ballot number by Proposer from an ack in phase 1
                        PROP_BAL_NUM_LOCK.release()

                        PROP_BAL_VAL_LOCK.acquire()
                        PROP_BAL_VAL = None # Highest received ballot number's value by Proposer from an ack in phase 1
                        PROP_BAL_VAL_LOCK.release()

                        MY_VAL_LOCK.acquire()
                        MY_VAL = 0
                        MY_VAL_LOCK.release()

            #On acceptor and proposer side
            elif (msg_type == "decision"):
                val = msg_dict['val']
                bal = tuple(msg_dict['bal'])
                #Depth is stale, need an update
                if (bal[0] > DEPTH):
                    #SEND UPDATE-REQUEST + '\0'
                    origin = bal[2]
                    #Send UPDATE back to origin
                    up_req_msg = toPaxosDict("update-request", DEPTH, SEQUENCE_NUMBER, server_id_int)
                    up_req_string = json.dumps(up_req_msg) + '\0'
                    start_new_thread(send_msg, (sockets[str(origin)], up_req_string.encode('ascii')))
                #Going to add to blockchain
                else:
                    if not bal[0] < DEPTH:
                        #Verify transactions are legal & Update moneyz
                        blockTrans = json.loads(val)['transactions']
                        allLegal = True
                        for trans in blockTrans:
                            amount, src, dest = decodeStringTuple(trans)

                            if (moneyz[src]-amount) < 0:
                                allLegal = False

                        if allLegal:
                            for trans in blockTrans:
                                amount, src, dest = decodeStringTuple(trans)

                                moneyz_LOCK.acquire()
                                moneyz[dest] += amount
                                moneyz[src] -= amount
                                moneyz_LOCK.release()

                            #Add transaction to blockchain
                            print("Adding Block to Blockchain: ", val)

                            BLOCKCHAIN_LOCK.acquire()
                            BLOCKCHAIN.append(val)
                            BLOCKCHAIN_LOCK.release()

                            DEPTH_LOCK.acquire()
                            DEPTH+=1
                            DEPTH_LOCK.release()

                            if(bal[1] > SEQUENCE_NUMBER):
                                SEQUENCE_NUM_LOCK.acquire()
                                SEQUENCE_NUMBER = bal[1]
                                SEQUENCE_NUM_LOCK.release()

                            #get transactions from block value
                            print("Block Trans: ", blockTrans)
                            print("TRANS: ", TRANS)
                            #Delete from TRANS if your transactions were added
                            if len(TRANS) >= BLOCK_SIZE:
                                isSame = True
                                for i in range(BLOCK_SIZE):
                                    if blockTrans[i] != TRANS[i]:
                                        isSame = False
                                        break

                                if(isSame):
                                    TRANS_LOCK.acquire()
                                    del TRANS[0:BLOCK_SIZE]
                                    TRANS_LOCK.release()

                            print("New TRANS:", TRANS)

                            ACK_COUNTER_LOCK.acquire()
                            ACK_COUNTER = 0 # Number of acknowledgements received by proposer in phase 1
                            ACK_COUNTER_LOCK.release()

                            ACC_COUNTER_LOCK.acquire()
                            ACC_COUNTER = 0 # Number of accepts received by proposer in phase 2
                            ACC_COUNTER_LOCK.release()

                            ACC_NUM_LOCK.acquire()
                            ACC_NUM = (DEPTH, 0, 0) # Last accepted ballot number in phase 2
                            ACC_NUM_LOCK.release()

                            ACC_VAL_LOCK.acquire()
                            ACC_VAL = None # last accepted value in phase 2
                            ACC_VAL_LOCK.release()

                            BALLOT_NUM_LOCK.acquire()
                            BALLOT_NUM = (DEPTH, 0, 0) # Highest received ballot number by acceptor
                            BALLOT_NUM_LOCK.release()

                            PROP_BAL_NUM_LOCK.acquire()
                            PROP_BAL_NUM = (DEPTH, 0, 0) # Highest received ballot number by Proposer from an ack in phase 1
                            PROP_BAL_NUM_LOCK.release()

                            PROP_BAL_VAL_LOCK.acquire()
                            PROP_BAL_VAL = None # Highest received ballot number's value by Proposer from an ack in phase 1
                            PROP_BAL_VAL_LOCK.release()

                            MY_VAL_LOCK.acquire()
                            MY_VAL = 0
                            MY_VAL_LOCK.release()
                        else:
                            print("Did not add block after decision. Idk how. Someone fked up")
            elif (msg_type == "update"):
                new_blockchain = msg_dict['val']
                new_depth = msg_dict['bal'][0]
                if(new_depth > DEPTH):
                    BLOCKCHAIN_LOCK.acquire()
                    BLOCKCHAIN = new_blockchain
                    BLOCKCHAIN_LOCK.release()

                    DEPTH_LOCK.acquire()
                    DEPTH = new_depth
                    DEPTH_LOCK.release()

            elif (msg_type == "update-request"):
                origin = msg_dict['bal'][2]
                #Send UPDATE back to origin
                up_msg = toPaxosDict("update", DEPTH, SEQUENCE_NUMBER, server_id_int, BLOCKCHAIN)
                up_string = json.dumps(up_msg) + '\0'
                start_new_thread(send_msg, (sockets[str(origin)], up_string.encode('ascii')))


'''
    ***** BLOCKCHAIN FUNCTIONS *****

    Block = {
        header: {curr_depth: , prev_hash: , nonce: }
        transactions: [t1, t2]
    }
'''

def create_block():
    if len(TRANS) >= BLOCK_SIZE:
        nonce = mine_nonce(TRANS[0:BLOCK_SIZE])
        if DEPTH != 0:
            block_dict = {
                "header": {"depth": DEPTH,"prev_hash": hashlib.sha256(BLOCKCHAIN[DEPTH-1].encode('ascii')).hexdigest(), "nonce": nonce},
                "transactions": TRANS[0:BLOCK_SIZE]
            }
            return json.dumps(block_dict)
        else:
            block_dict = {
                "header": {"depth": DEPTH,"prev_hash": None, "nonce": nonce},
                "transactions": TRANS[0:BLOCK_SIZE]
            }
            return json.dumps(block_dict)
    else:
        return -1

def check_transactions():
    ## Find a way to do this
    pass

def mine_nonce(trans):
    combined_trans = ""
    for t in trans:
        combined_trans += t
    while True:
        potential_nonce = ""
        for i in range(10):
            potential_nonce += random.choice(string.ascii_letters)
        pre_hash = combined_trans+potential_nonce
        hash = hashlib.sha256(pre_hash.encode('ascii')).hexdigest()
        if hash[len(hash)-1] == '0' or hash[len(hash)-1] == '1':
            return potential_nonce




'''
    ***** CLIENT FUNCTIONS *****
'''
def moneyTransfer(socketName, conn_socket, amount, client1, client2):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    global MY_VAL
    # print("Sending Transaction to server: ", socketName)

    TRANS_LOCK.acquire()
    TRANS.append("(" + str(amount) + "," + str(client1) + "," + str(client2) + ")")
    TRANS_LOCK.release()

    conn_socket.send("Added Transaction To TRANS: ".encode('ascii'))
    #Initiate Paxos
    #MY_VAL = amount
    start_new_thread(initiatePaxos, ()) #Thread




def printBlockchain(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    print("Printing Blockchain: ")
    bc = ""
    for block in BLOCKCHAIN:
        blockchain_json = json.loads(block)
        block_trans = blockchain_json["transactions"]

        bc += str(block_trans) + "\n"
    if (not BLOCKCHAIN):
        conn_socket.send("Blockchain is empty".encode('ascii'))
    else:
        conn_socket.send(bc.encode('ascii'))

def printBalance(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    print("Printing Balance: ")
    conn_socket.send(json.dumps(moneyz).encode('ascii'))

def printSet(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    print("Printing Set: ")
    trans_str = str(TRANS)
    if (not TRANS):
        conn_socket.send("Set is empty".encode('ascii'))
    else:
        conn_socket.send(trans_str.encode('ascii'))


def listen_to_client(socketName, conn_socket):
    global sockets
    global TRANS
    global BLOCKCHAIN
    global SEQUENCE_NUMBER
    global DEPTH
    while True:
        # print("listen_to_client")
        try:
            msg = conn_socket.recv(1024)
            # print("Message: ", msg)
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

'''
    ***** NETWORK FUNCTIONS *****
'''
def handle_connection(socketName, clientSocket):
    print("handle_connection with ", socketName)
    if (socketName == "client"):
        start_new_thread(listen_to_client, (socketName, clientSocket) )
    else:
        #OPTIONAL: SEND UPDATE to socket
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
                sockets[s_id] = s
                s.send(server_id_name.encode('ascii'))
                start_new_thread(listen_to_server, (s_id, s) )
            except:
                print("Failed to connect with", s_id)
                pass
        else:
            print("Already connected with ", s_id, ". Is this even possible?")


'''
    fin
'''



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
