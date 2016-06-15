from CheckMateServer import Server
from time import sleep
from urllib2 import urlopen

def getip():
    return urlopen('http://ip.42.pl/raw').read()

server = Server(r'/home/ben/Documents/python/MoveValidator/recordings')
port = server.bind()
server.start()
sleep(1)
print "server started: ip: {} port: {}".format(getip(),port)
raw_input()
print 'goodbye'
del server