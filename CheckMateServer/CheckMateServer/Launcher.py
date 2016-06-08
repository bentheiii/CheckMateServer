from CheckMateServer import Server
from time import sleep

#todo semaphores
server = Server(r'D:\my documents\programming\REPOS\VS\MoveValidator\recordings')
port = server.bind()
server.start()
sleep(1)
print "server started: port {}".format(port)
raw_input()
del server