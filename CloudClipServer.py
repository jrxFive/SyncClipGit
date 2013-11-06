__author__ = 'jxfivex1c-xubuntu'
#!/usr/bin/env python


import logging
import sys
import SocketServer
import threading
import cPickle as pickle
import pprint
from CloudClipClient import PickleClipAndComputer
import sqlite3
from collections import namedtuple


class DatabaseFunctions(object):

    db_fh = 'cloudClipPrototype.db'

    def NamedTuple(self,pickleData):

        TupleInsert = namedtuple('TupleInsert','unique_id comp_id ip message date')
        self.current_data_to_tuple =  TupleInsert(unique_id = pickleData['unique_id'],
                                                  comp_id = pickleData['comp_name'],
                                                  ip = pickleData['ip'],
                                                  message = pickleData['message'],
                                                  date = pickleData['date_time'])




    def insertIntoDB(self):
        db_cursor = self.db.cursor()
        db_cursor.execute('INSERT INTO ONE_TABLE VALUES (?,?,?,?,?)', self.current_data_to_tuple)
        self.db.commit()


    def connectToDB(self):
        try:
            self.db = sqlite3.connect(DatabaseFunctions.db_fh)
            return self.db
        except Exception:
            raise


    def closeDBConnection(self):
        try:
            self.db.close()
        except Exception:
            raise



class ServerRequestHandler(SocketServer.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self,request,client_address,server)

    def setup(self):
        self.dbConnection = DatabaseFunctions()
        self.dbConnection.connectToDB()

    def handle(self):
        data = self.request.recv(1024)

        pprint.pprint(data)
        pprint.pprint(pickle.loads(data))
        pickle_data = pickle.loads(data)

        self.dbConnection.NamedTuple(pickle_data)
        self.dbConnection.insertIntoDB()

        self.request.send("Received")

    def finish(self):
        self.dbConnection.closeDBConnection()



class SetupServer(object):

    def __init__(self):
        self.server_address = ('localhost',36088)
        self.ip = 0
        self.port_number = 0
        self.server = SocketServer.TCPServer(self.server_address, ServerRequestHandler)
        print self.server.server_address

        t = threading.Thread(target=self.server.serve_forever())
        t.start()


    def printServerInfo(self):
        print self.ip

if __name__ == "__main__":
    s = SetupServer()
    s.printServerInfo()


