import socket
import math
import time
import select
import pickle
import hashlib
from SUDPpacket import Packet
from collections import OrderedDict
from threading import Thread, Lock


class SUDPServer:
    def __init__(self, senderIP, senderPort, recieverIP, recieverPort, seqNumBits=8, N=None):
        self.seqNumBits = seqNumBits
        self.N = N

        self.senderPort = senderPort
        self.senderIP = senderIP
        self.recieverIP = recieverIP
        self.recieverPort = recieverPort
        self.filereceived = "received.txt"

    def open(self):
        try:
            global recvSock
            self.recvSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.recvSock.bind((self.recieverIP, self.recieverPort))
            self.recvSock.setblocking(0)
        except Exception as e:
            print("Error while creating SUDPServer socket", e)

    def recv(self, time_limit=30):
        window = Window(self.N, self.seqNumBits)
        pktHandler = PktHandler(
            self.recvSock, self.senderIP, self.senderPort, window, self.filereceived, time_limit)

        pktThread = Thread(target=pktHandler.run)
        pktThread.start()
        pktThread.join()

    def close(self):
        try:
            if recvSock:
                recvSock.close()
        except Exception as e:
            print("Could not close the SUDPServer Socket! :(")


class Window:
    def __init__(self, N, seqNumBits):
        self.expPkt = 0
        self.maxSeqSpace = int(math.pow(2, seqNumBits))

        if N == None:
            self.N = (int(math.pow(2, seqNumBits-1)))
        else:
            if N > int(math.pow(2, seqNumBits-1)):
                print("window size invalid")
            else:
                self.N = N
        self.finalPkt = self.N-1
        self.recvWindow = OrderedDict()
        self.isPktRecv = False

    def noOrder(self, k):
        if self.expPkt > self.finalPkt:
            if k < self.expPkt and k > self.lastPkt:
                return True
            else:
                return False
        else:
            if k < self.expPkt or k > self.finalPkt:
                return True
            else:
                return False

    def isPresent(self, k):
        if k in self.recvWindow and self.recvWindow[k] != None:
            return True
        else:
            return False

    def exp(self, seqNum):
        if seqNum == self.expPkt:
            return True
        else:
            return False

    def record(self, recvdPkt):
        if not self.exp(recvdPkt.seqNum):
            seqNum = self.expPkt

            while seqNum != recvdPkt.seqNum:
                if seqNum not in self.recvWindow:
                    self.recvWindow[seqNum] = None

                seqNum = seqNum+1
                if seqNum >= self.maxSeqSpace:
                    seqNum = seqNum % self.maxSeqSpace
        self.recvWindow[recvdPkt.seqNum] = recvdPkt

    def nxt(self):
        pkt = None
        if len(self.recvWindow) > 0:
            # print(self.recvWindow.items())
            amt = 0
            for key, val in self.recvWindow.items():
                npkt = [key, val]
                amt += 1
                if(amt == 1):
                    break

            #npkt = self.recvWindow.items()[0]
            if npkt[1] != None:
                pkt = npkt[1]
                del self.recvWindow[npkt[0]]

                self.expPkt = npkt[0]+1
                if self.expPkt >= self.maxSeqSpace:
                    self.expPkt = self.expPkt % self.maxSeqSpace

                self.finalPkt = self.expPkt + self.N-1
                if self.finalPkt >= self.maxSeqSpace:
                    self.finalPkt = self.finalPkt % self.maxSeqSpace

        return pkt

    def strt(self):
        self.isPktRecv = True


class PktHandler:
    def __init__(self, recvSock, senderIP, senderPort, window, filename, time_limit=30):
        Thread.__init__(self)
        self.window = window
        self.time_limit = time_limit
        self.recvSock = recvSock
        self.senderIP = senderIP
        self.senderPort = senderPort
        self.filename = filename
        self.fp = None

    def run(self):
        maxTry = 0
        try:
            self.fp = open(self.filename, "wb")
        except Exception as e:
            print("Error in opening the file")
        while True:
            status = select.select([self.recvSock], [], [], self.time_limit)
            if not status[0]:
                if not self.window.isPktRecv:
                    continue

                else:
                    if maxTry == 7:
                        print("closing...")
                        break
                    else:
                        maxTry = maxTry+1
                        continue
            else:
                maxTry = 0
                if not self.window.isPktRecv:
                    self.window.strt()

            try:
                recvdPkt = self.recvSock.recv(4096)
                recvdPkt = pickle.loads(recvdPkt)
                print("Recieved packet with sequence number: ", recvdPkt.seqNum)
                # print(recvdPkt.data)
                # AckPkt=Packet(recvdPkt.seqNum,recvdPkt.checksum,recvdPkt.data)
                # AckPkt.setAck()
            except Exception as e:
                print("Receiving Failed", e)

            if self.isCorrupt(recvdPkt):
                print("packet corrupt")
                continue

            if self.window.noOrder(recvdPkt.seqNum):
                self.sudp_send(recvdPkt)
                continue

            if self.window.isPresent(recvdPkt.seqNum):
                print("Recieved duplicate")
                continue
            else:
                recvdPkt.setAck()
                try:
                    self.window.record(recvdPkt)
                    self.sudp_send(recvdPkt)
                except Exception as e:
                    print("ack not sent  ", e)

            if self.window.exp(recvdPkt.seqNum):
                self.deliverPkt(recvdPkt.data)

    def isCorrupt(self, recvdPkt):
        cal_hash = hashlib.sha256(recvdPkt.data).hexdigest()
        if(recvdPkt.checksum == cal_hash):
            print("checking...fine")
            return False
        else:
            print("checking...corrupted")
            return True

    def sudp_send(self, packet):
        print("sent ACK", packet.seqNum)
        packet = pickle.dumps(packet)
        self.recvSock.sendto(packet, (self.senderIP, self.senderPort))

    def deliverPkt(self, data):
        while True:
            pkt = self.window.nxt()
            if pkt:
                self.toAppLayer(data)
            else:
                break

    def toAppLayer(self, data):
        #print(self.fp, data)
        try:
            if self.fp != None:
                self.fp.write(data)
            print("Writing this packet to file successful")

        except Exception as e:
            print("Could not write to file %s", self.filename)
            raise FileIOError("Writing to file failed!")
