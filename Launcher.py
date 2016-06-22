import urllib
from CheckMateServer import Server
from time import sleep
import os
import socket
import sys
#get ip methods, hot from SO
if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def getPrivateIp():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

def getPublicIp():
    raw = urllib.urlopen('http://icanhazip.com').read()
    rawind = str.find(raw,' ')
    return raw[:rawind]

server = Server(sys.argv[1])
port = server.bind(int(sys.argv[2]))
server.start()
sleep(1)
print "server started: public ip: {}, private ip: {} port: {}".format(getPublicIp(), getPrivateIp(), port)
raw_input()
print 'goodbye'
server.close()