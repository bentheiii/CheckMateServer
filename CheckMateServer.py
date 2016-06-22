from os import listdir
from os.path import isfile, join, getctime, getmtime
from time import time
from serverThreads import *
import threading
#def chunkRead(f):

#a simple class that handles data caching
class Cache:
    def __init__(self,datagenerator):
        self.lastUpdateTime = None
        self.data = None
        self.generator = datagenerator
    #generate the data
    def gen(self):
        self.data = self.generator()
        self.lastUpdateTime = time()
    #generate the data if none generated yet
    def ensureData(self):
        if self.lastUpdateTime is None:
            self.gen()
        return self.data
    #consider generating by update time
    def update(self,newestinfoTime):
        if (self.lastUpdateTime is None) or self.lastUpdateTime < newestinfoTime:
            self.gen()
        return self.data
#GLOBAL LISTEN
TCP_IP = '0.0.0.0'

class Server:
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
        #dicrtionary of game names with their latest update time
        self.gameList = {}
        #dictionary of games with their respective caches
        self.gameCache = {}
        #dicrtionary of games along with their listener count
        self.gameListeners = {}
        self.portListener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.portListener.settimeout(1)
        self.managedThreads = []
        self.gameSem = threading.Semaphore()
        self.moveSem = threading.Semaphore()
    #binds the socket to a port and returns the port bound
    def bind(self,port = 0):
        self.portListener.bind((TCP_IP,port))
        self.portListener.listen(10)
        return self.portListener.getsockname()[1]
    #refreshes the games list (not cached because we trust the file system to be optimized)
    def updateGames(self):
        files = [f for f in listdir(self.gamesPath) if isfile(join(self.gamesPath, f))]
        self.gameSem.acquire()
        self.gameList = {}
        for f in files:
            self.gameList[f] = getctime(join(self.gamesPath, f))
        self.gameSem.release()
    #add listener to specific game, keeping it cached
    def addGame(self,filename):
        self.gameListeners[filename] = self.gameListeners.get(filename,0)+1
        if filename in self.gameCache:
            return
        self.gameCache[filename] = Cache(lambda: open(join(self.gamesPath, filename),'rb').read())
    #removes listener for game
    def popGame(self,filename):
        if not filename in self.gameCache:
            return
        self.gameListeners[filename] -= 1
        if self.gameListeners[filename] <= 0:
            self.gameCache.pop(filename)
            self.gameListeners.pop(filename)
    #update moves for cached games
    def updateMoves(self):
        for f, c in self.gameCache.iteritems():
            self.moveSem.acquire()
            c.update(getmtime(join(self.gamesPath, f)))
            self.moveSem.release()
    #generate connection from server socket
    def getConnection(self):
        conn, addr = self.portListener.accept()
        print "got connection at {}".format(str(addr))
        ret = Connection(self,conn)
        return ret
    #unmanage a stoppable thread
    def unManage(self,t,remove = False):
        t.stop()
        if remove:
            self.managedThreads.remove(t)
    #start and manage a stoppable thread
    def startManage(self,managable):
        managable.start()
        self.managedThreads.append(managable)
    #start threads
    def start(self):
        self.startManage(listUpdater(self))
        self.startManage(moveUpdater(self))
        self.startManage(conGenerator(self))
    #unmanages all threads
    def close(self):
        for i in self.managedThreads:
            self.unManage(i)


