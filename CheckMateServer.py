from os import listdir
from os.path import isfile, join, getctime, getmtime
from time import time, sleep
import socket
from serverThreads import *
import threading
#def chunkRead(f):


class Cache:
    def __init__(self,datagenerator):
        self.lastUpdateTime = None
        self.data = None
        self.generator = datagenerator
    def gen(self):
        self.data = self.generator()
        self.lastUpdateTime = time()
    def ensureData(self):
        if self.lastUpdateTime is None:
            self.gen()
        return self.data
    def update(self,newestinfoTime):
        if (self.lastUpdateTime is None) or self.lastUpdateTime < newestinfoTime:
            self.gen()
        return self.data
TCP_IP = '127.0.0.1'

class Server:
    #TODO LOCKS

    #threads the server manages:
    #
    #games list updater thread
    #move updater thread
    #port listener
    #port answerers
    def __init__(self,gamesPath,gamesupdateinterval=1,specificgameupdateinterval=1):
        self.gamesPath = gamesPath
        self.gamesInterval = gamesupdateinterval
        self.moveInterval = specificgameupdateinterval
        self.gameList = {}
        self.gameCache = {}
        self.gameListeners = {}
        self.portListener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.managedThreads = []
        self.gameSem = threading.Semaphore()
        self.moveSem = threading.Semaphore()
    def bind(self,port = 0):
        self.portListener.bind((TCP_IP,port))
        self.portListener.listen(10)
        if port == 0:
            return self.portListener.getsockname()[1]
    def updateGames(self):
        files = [f for f in listdir(self.gamesPath) if isfile(join(self.gamesPath, f))]
        self.gameSem.acquire()
        self.gameList = {}
        for f in files:
            self.gameList[f] = getctime(join(self.gamesPath, f))
        self.gameSem.release()
    def addGame(self,filename):
        self.gameListeners[filename] = self.gameListeners.get(filename,0)+1
        if filename in self.gameCache:
            return
        self.gameCache[filename] = Cache(lambda: open(join(self.gamesPath, filename),'rb').read())
    def popGame(self,filename):
        if not filename in self.gameCache:
            return
        self.gameListeners[filename] -= 1
        if self.gameListeners[filename] <= 0:
            self.gameCache.pop(filename)
            self.gameListeners.pop(filename)
    def updateMoves(self):
        for f, c in self.gameCache.iteritems():
            self.moveSem.acquire()
            c.update(getmtime(join(self.gamesPath, f)))
            self.moveSem.release()
    def getConnection(self):
        conn, addr = self.portListener.accept()
        print "got connection at {}".format(str(addr))
        ret = Connection(self,conn)
        return ret
    def unManage(self,t,remove = False):
        t.stop()
        if remove:
            self.managedThreads.remove(t)
    def startManage(self,managable):
        managable.start()
        self.managedThreads.append(managable)
    def start(self):
        self.startManage(listUpdater(self))
        self.startManage(moveUpdater(self))
        self.startManage(conGenerator(self))
    def __del__(self):
        for i in self.managedThreads:
            self.unManage(i)


