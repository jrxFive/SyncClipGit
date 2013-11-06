__author__ = 'jxfivex1c-xubuntu'

from datetime import datetime
import time
import threading
import socket
import cPickle as pickle
import pprint
import os
import sys
import logging
import fcntl
from logging.handlers import RotatingFileHandler
from ConfigParser import SafeConfigParser
import platform

#TODO Implement queueing for when connection is not available
#TODO Implement check for working connection with db
#TODO Quit signal handler
#TODO Logging
#TODO Configuration file
#TODO Thread-safe queue for NonInserted Data
#TODO Thread-safe queue for new clip Data


#TODO Add unicode support for sockets


def GlobalLogging():
    global log
    try:
        loggingFileLocation = 'clientRotateLog.dat'

        log = logging.getLogger('global')
        log.setLevel(logging.INFO)

        loggingFormatter = logging.Formatter('%(asctime)s - '
                                             '%(levelname)s - '
                                             '%(lineno)d - '
                                             '%(message)s - '
                                             '%(thread)d - '
                                             '%(threadName)s')

        fileHandler = RotatingFileHandler(loggingFileLocation, maxBytes=1048576, backupCount=3)

        debugStreamHandler = logging.StreamHandler()
        debugStreamHandler.setLevel(logging.DEBUG)
        debugStreamHandler.setFormatter(loggingFormatter)

        fileHandler.setFormatter(loggingFormatter)
        log.addHandler(fileHandler)
        log.addHandler(debugStreamHandler)
    except Exception:
        log.error("Unknown Exception")


class DatabaseFunctions(object):
    def __init__(self):
        self.functionNames = dict(newClip=1,
                                  updateRequest=2,
                                  register=3)

    def newClip(self):
        self.userID = ""
        self.userComputerID = ""
        self.DateTime = ""
        self.Message = ""
        self.MessageLengthInBytes = ""
        self.TwoDaysOldDateTime = ""

    def pushNonSyncedData(self):
        pass


    def registerNewComputer(self):
        self.ComputerName = ""
        self.OSType = ""
        self.ReachableStatus = ""
        self.DateTime = ""
        pickle.dumps(dict(function="REG"))

    def updateRequest(self):
        pass


class PickleClipAndComputer(object):
    def __init__(self, unique_id, comp_name, ip, message):
        self.unique_id = unique_id
        self.comp_name = comp_name
        self.ip = ip
        self.message = message
        self.date_time = datetime.now()
        self.pickleClip = dict(unique_id=self.unique_id, comp_name=self.comp_name, ip=self.ip, message=self.message,
                               date_time=self.date_time)

    def returnPickleDumps(self):
        return pickle.dumps(self.pickleClip)


    def pickleDumpsString(self):
        return pprint.pprint(self.pickleClip)


class ComputerInformation(object): #TESTING W/OUT DB SETUP, SHOULD BE JUST ENUM
    unique_id = "JON"
    comp_name = "X1C"
    ip_address = "0"

    def __init__(self):
        pass


class NewClipData(threading.Thread):
    def __init__(self, clipData, threadName):
        super(NewClipData, self).__init__(name=threadName)
        self.clipData = clipData
        self.lock = threading.RLock()

    def createAndReturnPickle(self):
        self.packetData = PickleClipAndComputer(ComputerInformation.unique_id,
                                                ComputerInformation.comp_name,
                                                ComputerInformation.ip_address,
                                                self.clipData)

        return self.packetData.returnPickleDumps()

    def run(self): #TODO IS this thread safe with multiple connections of the same SocketClient?

        self.lock.acquire()
        client = NetworkClient()

        try:
            client.connectToServer()
        except socket.error as s:
            q = InsertNonSyncedData()
            q.runAfterStartup()
            q.writeData(self.createAndReturnPickle())
            q.closeFH()
            self.lock.release()

        client.sendDataToServer(self.createAndReturnPickle())

        client.closeNetWorkClient()
        del client
        self.lock.release()


def WriteConfigurationFile():
    configFile = SafeConfigParser()

    #Sections
    configFile.add_section('credentials')
    configFile.add_section('computer')
    configFile.add_section('files')
    configFile.add_section('db')


    #Computer Section
    osType = platform.system()
    compName = platform.node()
    configFile.set('computer', 'os', value=osType)
    configFile.set('computer', 'name', value=compName)

    #Files Section
    scriptPath = sys.argv[0]
    directoryPath = os.path.dirname(scriptPath)
    configFile.set('files', 'install_location', value=os.path.join(directoryPath, ''))
    configFile.set('files', 'process_control_file_location', value=os.path.join(directoryPath, 'syncClipClient.pid'))
    configFile.set('files', 'log_file_location', value=os.path.join(directoryPath, 'clientRotateLog.dat'))
    configFile.set('files', 'db_location', value=os.path.join(directoryPath, 'syncClipClientDB.db'))

    #DB Section
    db_ip = raw_input('Enter IP where SyncClipServer is running: ')
    db_port = raw_input('Enter PORT associated with SyncClipServer: ')
    configFile.set('db', 'db_ip', value=db_ip)
    configFile.set('db', 'db_port', value=db_port)
    configFile.set('db', 'db_function_push', 'PUSH')
    configFile.set('db', 'db_function_pull', 'PULL')
    configFile.set('db', 'db_function_register_new_user', 'REG_NEW_USER')
    configFile.set('db', 'db_function_register_new_computer', 'REG_NEW_COMP')
    configFile.set('db', 'db_pull_interval', '15')


    #Credentials Section
    regValue = None
    userName = ''
    while regValue is None:
        regDecision = raw_input('First time registering? Press Y/N')
        if regValue != 'Y' or 'y' or 'N' or 'n' or 'None':
            regValue = None
            print "Invalid decision press Y or N"
    if regValue == 'Y' or 'y':
        pass
    elif regValue == 'N' or 'n':
        pass
        #IF NOT FOUND

    #ELIF ERROR

    #ELSE ADD USERNAME AND RETURNED UC_ID
    configFile.set('credentials', 'username', value='')
    configFile.set('credentials', 'uc_id', value='')



    fh = open('SyncClip.config','w+')
    configFile.write(fh)
    fh.close()


def ConfigurationFile():
    global config

    configFileLocation = 'SyncClip.ini'
    configFileStat = os.stat(configFileLocation)

    if os.path.exists(configFileLocation):
        config = SafeConfigParser()
        try:
            config.read(configFileLocation)
        except Exception:
            log.error()
    else:
        WriteConfigurationFile()

    if configFileStat.st_size == 0:
        temp_logger = logging.basicConfig(level=logging.ERROR, stream=logging.StreamHandler)
        temp_logger.error("Config File Empty Process Exiting")
        sys.exit(1)


def InstanceCheck():
    pidFile = 'cloudClipClient.pid'

    try:
        if os.path.exists(pidFile):
            fh = open(pidFile, 'r')
        else:
            fh = open(pidFile, 'w')

        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError as exc:
        log.error("CloudClipClient Process Already Running")
        sys.exit(1)
        # some other error	 raise	 # The previous invocation of the job is still running	 return # Return without doing anything
    try:
        time.sleep(5)
    except Exception:
        pass
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN | fcntl.LOCK_NB)


class InsertNonSyncedData(object):
    def __init__(self): #TODO File descriptor for runStartUp and runAfterStartUp
        self.queueFile = 'nonSyncedPickleDataFile.dat'


    def runAfterStartup(self):
        self.fh = open(self.queueFile, 'a+')

    def runStartUp(self): #Startup #TODO Remove transmitted data
        if self.FileIfDoesNotExist() == False:
            self.fh = open(self.queueFile, 'r')
            print self.fh
            if self.checkForData() is True and self.testDBConnection() is True:
                print "TRUE"
                self.transmitToDB()
            else:
                print "FAIL"
            self.closeFH()

    def FileIfDoesNotExist(self):
        if not os.path.exists(self.queueFile):
            self.fh = open(self.queueFile, 'w+')
            self.fh.close()
            return True
        else:
            return False

    def checkForData(self):
        osStatObject = os.stat(self.queueFile)
        if osStatObject.st_size == 0:
            print osStatObject.st_size
            return False
        else:
            return True

    def writeData(self, pickleData):
        try:
            self.fh.write('%s\n' % (pickleData))
        except IOError as io:
            log.error('%d' % io.errno)
            self.closeFH()


    def testDBConnection(self):
        self.testNetworkResultBinary = False
        self.testNetwork = NetworkClient()
        try:
            self.testNetwork.connectToServer()
            self.testNetworkResultBinary = True
        except socket.error as e:
            if e.errno == 111:
                log.error("Socket Error Connection Refused")
                del self.testNetwork
                self.testNetworkResultBinary = False
                return False
            else:
                log.error("Error")
                del self.testNetwork
                self.testNetworkResultBinary = False
                return False
        else:
            return True

    def transmitToDB(self):
        threadName = ComputerInformation.comp_name
        threadCount = 0
        if self.testNetworkResultBinary is True:
            for line in self.fh.readline():
                thread = NewClipData(line, threadName + '-' + str(threadCount))
                thread.start()
                threadCount += 1
            else:
                pass
        os.remove(self.queueFile)


    def closeFH(self):
        self.fh.close()


class NetworkClient(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = ('localhost', 36088)


    def connectToServer(self):
        try:
            self.sock.connect(self.server_address)
            log.info("Connected to SocketServer")
        except Exception:
            raise
            #TODO Kill Thread

    def sendDataToServer(self, dataToSend):
        try:
            length_of_sent_message = self.sock.send(dataToSend)
            response = self.sock.recv(length_of_sent_message)
            log.info('%s' % response)
        except socket.error as e:
            if e.errno == 32:
                logging.error("Broken Pipe to Database..Most likely DB is down")
            raise
            #TODO Kill Thread


    def closeNetWorkClient(self):
        self.sock.close()
        #TODO Kill Thread


class RunCloudClip(object):
    def __init__(self):
        pass

    def bootUpProcess(self):
        ReadConfigurationFile()
        print "here"
        GlobalLogging()

    def quit_signal_handler(classObj, signum, stack):
    #TODO What threads are open? and close all sockets
        # print dir(classObj), type(classObj)
        # print dir(signum), type(signum)
        # print dir(stack), type(stack)
        t = threading.activeCount()
        if t > 1:
            for th in threading.enumerate()[1:]:
                del th #TODO check that thread/object is gone
        else:
            log.info("No additional threads active")
        sys.exit()

    def run(self):
        threadName = ComputerInformation.comp_name
        threadCount = 0

        signal.signal(signal.SIGTERM, self.quit_signal_handler)
        signal.signal(signal.SIGINT, self.quit_signal_handler)

        r = Tk()
        r.withdraw()
        startingClipData = r.clipboard_get()

        while True:
            currentClip = r.clipboard_get()
            print startingClipData, currentClip
            time.sleep(5)
            if currentClip != startingClipData:

                startingClipData = currentClip
                startThread = NewClipData(startingClipData, threadName + '-' + str(threadCount))

                startThread.start()
                #startThread.join()

                threadCount += 1
                print "where am I"
                time.sleep(1)
            else:
                time.sleep(1)

        r.destroy()


    def singleCloudClipProcess(self):
        pidFile = 'cloudClipClient.pid'

        try:
            if os.path.exists(pidFile):
                self.fh = open(pidFile, 'r')
            else:
                self.fh = open(pidFile, 'w')

            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as exc:
            log.error("CloudClipClient Process Already Running")
            sys.exit(1)

        try:
            i = InsertNonSyncedData()
            print "Initiated NonSyncData Instance"
            i.runStartUp()
            #InsertNonSyncedData().runStartUp() #TODO Broken
            print "made it to startup"
            self.run()
        except Exception as e:
            logging.error("something broke")
            raise
        finally:
            fcntl.flock(self.fh, fcntl.LOCK_UN | fcntl.LOCK_NB)


class ArgumentParser(object):
    global parser

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--get", help="Put integer value from list as current copy on clipboard", type=int,
                        dest="g")
    parser.add_argument("-l", "--list", help="List most recent synced clips")
    parser.add_argument("-u", "--update", help="Request update from server database")
    parser.add_argument("-x", "--exit", help="Terminate program")


if __name__ == "__main__":
    a = AP.ArgumentParser()
    parameters = a.argSetup()
    if parameters['list'] == None and parameters['get'] == None and parameters['exit'] == None:
        ConfigurationFile()
    else:
        if parameters['list'] == None:
            pass
        if parameters['get'] == None:
            pass
        if parameters['exit'] == None:
            pass

    r = RunCloudClip()
    r.bootUpProcess()
    r.singleCloudClipProcess()









