from StoppableThread import StoppableThread
from time import sleep
import socket

class listUpdater(StoppableThread):
    def __init__(self,server):
        StoppableThread.__init__(self)
        self.server = server
    def run(self):
        print "List updater started"
        while StoppableThread.stopped(self):
            self.server.updateGames()
            #print "pooling game list, current list:\n{}".format(self.server.gameList)
            sleep(self.server.gamesInterval)
        print "List updater stopped"

class moveUpdater(StoppableThread):
    def __init__(self,server):
        StoppableThread.__init__(self)
        self.server = server
    def run(self):
        print "Move updater started"
        while StoppableThread.stopped(self):
            self.server.updateMoves()
            sleep(self.server.gamesInterval)
        print "Move updater stopped"

class conGenerator(StoppableThread):
    def __init__(self,server):
        StoppableThread.__init__(self)
        self.server = server
    def run(self):
        print "Connection generator started"
        while StoppableThread.stopped(self):
            print "scanning for connection"
            con = self.server.getConnection()
            #print "accepted connection"
            self.server.startManage(con)
        print "Connection generator stopped"

class Connection(StoppableThread):
    ListGamesCommand = '0'
    ListMovesCommand = '1'
    SetGameCommand = '2'
    BufferSize = 4096
    connectionCount = 0
    def __init__(self,server,socket):
        StoppableThread.__init__(self)
        self.server = server
        self.socket = socket
        self.gameName = None
        self.identifier = Connection.connectionCount
        Connection.connectionCount+=1
    def handleListGames(self,inp):
        print "#{} got list games request".format(self.identifier)
        try:
            inp = int(inp)
        except ValueError:
            return None
        self.server.gameSem.acquire()
        games = list(reversed(map(lambda x:x[0],sorted(self.server.gameList.items(), key=lambda x:x[1]))))
        self.server.gameSem.release()
        if len(games) > inp:
            games = games[:inp]
        ret = "\n".join(games)
        return ret
    def handleListMoves(self,inp,p = True):
        if p:
            print "#{} got list move request".format(self.identifier)
        if self.gameName is None:
            return None
        self.server.moveSem.acquire()
        ret = self.server.gameCache[self.gameName].ensureData()
        self.server.moveSem.release()
        return ret
    def handleSetGame(self,inp):
        print "#{} got change game request to {}".format(self.identifier,inp)
        self.server.gameSem.acquire()
        if not inp in self.server.gameList:
            self.server.gameSem.release()
            return None
        self.server.gameSem.release()
        if not self.gameName is None:
            self.server.popGame(self.gameName)
        self.gameName = inp
        self.server.addGame(inp)
        return self.handleListMoves(None,False)
    def run(self):
        print "#{} connection started".format(self.identifier)
        try:
            while StoppableThread.stopped(self):
                inp = self.socket.recv(self.BufferSize)
                if inp == '':
                    raise socket.error("connection terminated")
                command, inp = inp[0],inp[1:]
                out = None
                if command == self.ListGamesCommand:
                    out = self.handleListGames(inp)
                elif command == self.ListMovesCommand:
                    out = self.handleListMoves(inp)
                elif command == self.SetGameCommand:
                    out = self.handleSetGame(inp)
                if out is None:
                    self.socket.close()
                    raise socket.error("got bad command {}".format(command+inp))
                self.socket.send(out)
        except socket.error as e:
            print "#{} Connection Error: {}".format(self.identifier,e)
            pass
        finally:
            self.server.unManage(self,True)
        print "#{} connection ended".format(self.identifier)