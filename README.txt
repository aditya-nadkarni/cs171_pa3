# cs171_pa3

Final Project: Erez Hajaj and Aditya Nadkarni


server.py and clienty.py should be placed in a folder together


From the file path of that folder, do the following:


Non-partition run:


Run each of these commands 5 times, replacing # with each of the following numbers: 1, 2, 3, 4, 5. There should be 10 total processes running


python3 server.py #


python3 clienty.py #


Partition run:


The following example partitions the servers into two sets, [1, 2, 3] and [4, 5]. These partitions cannot communicate with each other. To change the partition structure, understand that every number after the first number represents all the server ids the server is unable to communicate with. So server 1 can only communicate with all the servers except 4 and 5, ect. There should still be 10 total processes running


python3 server.py 1 4 5
python3 server.py 2 4 5
python3 server.py 3 4 5
python3 server.py 4 1 2 3
python3 server.py 5 1 2 3


python3 clienty.py #
