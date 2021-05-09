import hashlib
import socket
import math
import time
import select
import pickle
from collections import OrderedDict
from threading import Thread
from threading import Lock
from SUDPpacket import Packet


class SUDPClient:
    def __init__(self, filename, senderIP, senderPort, recieverIP, recieverPort, seqNumBits=8, mss=1000, N=None):
        self.seqNumBits = seqNumBits
        self.mss = mss
        self.N = N
        self.filename = filename
        self.senderPort = senderPort
        self.senderIP = senderIP
        self.recieverIP = recieverIP
        self.recieverPort = recieverPort

    def open(self):
        try:
            global senderSock
            senderSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            senderSock.bind((self.senderIP, self.senderPort))
            senderSock.setblocking(0)
        except Exception as e:
            print("Error creating SUDP Client socket")

    def send(self, time_limit=30):
        window = Window(self.N, self.seqNumBits)
        pktHandler = PktHandler(
            self.recieverIP, self.recieverPort, self.filename, window, self.mss, time_limit)
        ackHandler = AckHandler(self.recieverIP, window)

        pktThread = Thread(target=pktHandler.run)
        ackThread = Thread(target=ackHandler.run)

        pktThread.start()
        ackThread.start()

        pktThread.join()
        ackThread.join()

    def close(self):
        try:
            if senderSock:
                senderSock.close()
        except Exception as e:
            print("Could not close SUDP Client Socket")


class Window:
    def __init__(self, N, seqNumBits):
        self.nxtSeqNum = 0
        self.expAck = 0
        self.nxtPkt = 0
        self.maxSeqSpace = int(math.pow(2, seqNumBits))
        self.tranWindow = OrderedDict()
        self.isPktTrans = True

        if N == None:
            self.N = (int(math.pow(2, seqNumBits-1)))
        else:
            if N > int(math.pow(2, seqNumBits-1)):
                print("SUDPClient Window size invalid")
            else:
                self.N = N

    def isEmpty(self):
        if len(self.tranWindow) != 0:
            return False
        else:
            return True

    def isFull(self):
        if len(self.tranWindow) < self.N:
            return False
        else:
            return True

    def isPresent(self, k):
        if k in self.tranWindow:
            return True
        else:
            return False

    def absorb(self, k):
        with Lock():
            self.tranWindow[k] = [None, False]

            self.nxtSeqNum += 1
            if self.nxtSeqNum >= self.maxSeqSpace:
                self.nxtSeqNum %= self.maxSeqSpace

            self.nxtPkt += 1
            # print(self.tranWindow[k])
            # if self.nxtSeqNum<self.maxSeqSpace:
            #     self.nxtSeqNum=self.nxtSeqNum+1

            # else:
            #     self.nxtSeqNum=self.nxtSeqNum+1
            #     self.nxtSeqNum=(self.nxtSeqNum)%self.maxSeqSpace

            # self.nextPkt=self.nxtPkt+1

    def strt(self, k):
        with Lock():
            self.tranWindow[k][0] = time.time()

    def stop(self, k):
        if self.isPresent(k):
            self.tranWindow[k][0] = None

        if k == self.expAck:
            for key, val in self.tranWindow.items():
                if val[0] == None and val[1] == True:
                    del self.tranWindow[key]
                else:
                    break

            if not self.isEmpty():
                self.expAck = self.tranWindow.items()[0][0]
            else:
                self.expAck = self.nxtSeqNum

    def unacked(self, k):
        if self.isPresent(k) == False or self.tranWindow[k][1] == True:
            return False
        else:
            return True

    def ackit(self, k):
        with Lock():
            self.tranWindow[k][1] = True

    def stop_tran(self):
        with Lock():
            self.isPktTrans = False


class PktHandler:
    def __init__(self, recieverIP, recieverPort, filename, window, mss, time_limit=30):
        Thread.__init__(self)
        self.window = window
        self.mss = mss
        self.time_limit = time_limit
        self.filename = filename
        self.recieverIP = recieverIP
        self.recieverPort = recieverPort

    def run(self):
        packets = self.get_pkts(self.recieverIP, self.recieverPort)
        print(len(packets))
        while(self.window.isEmpty() == False or self.window.nxtPkt < len(packets)):
            if (self.window.isFull()) or (not self.window.isFull() and self.window.nxtPkt >= len(packets)):
                break
            else:
                packet = packets[self.window.nxtPkt]
                self.window.absorb(packet.seqNum)
                #print("sending info", packet.data)
                threadName = "Pkt:"+str(packet.seqNum)
                singlePkt = SinglePkt(
                    self.recieverIP, self.recieverPort, self.window, packet, self.time_limit, threadName)
                singlePkt.run()

        print("PacketHandler run complete, gracefully exiting the transfer")
        self.window.stop_tran()

    def get_pkts(self, recieverIP, recieverPort):
        pkts = []
        fptr = open(self.filename, "rb")
        cnt = 0
        limit = self.mss-6
        print("Packets being generated")

        while True:
            bin_data = fptr.read(limit)
            if not bin_data:
                break
            sno = cnt % self.window.maxSeqSpace
            packet = Packet(sno, self.chcksum(bin_data), bin_data)
            pkts.append(packet)
            cnt = cnt+1
        return pkts

    def chcksum(self, bin_data):
        s = hashlib.sha256(bin_data).hexdigest()
        return s


class SinglePkt:
    def __init__(self, recieverIP, recieverPort, window, packet, time_limit, threadName):
        Thread.__init__(self)
        self.window = window
        self.packet = packet
        self.time_limit = time_limit
        self.threadName = threadName
        self.recieverIP = recieverIP
        self.recieverPort = recieverPort

    def run(self):
        self.sudp_send(self.packet)
        self.window.strt(self.packet.seqNum)
        while self.window.unacked(self.packet.seqNum):
            timeTaken = time.time() - \
                self.window.tranWindow[self.packet.seqNum][0]
            if timeTaken > self.time_limit:
                self.sudp_send(self.packet)
                self.window.strt(self.packet.seqNum)
        with Lock():
            self.window.stop(self.packet.seqNum)

    def sudp_send(self, packet):
        x = packet.seqNum
        packet = pickle.dumps(packet)
        try:
            with Lock():

                senderSock.sendto(packet, (self.recieverIP, self.recieverPort))
                print("sent packet", x)

        except Exception as e:
            print("Error in sending a Sinlge Packet instance", e)


class AckHandler:
    def __init__(self, recieverIP, window, time_limit=30, threadName="ACKhandle"):
        Thread.__init__(self)
        self.window = window
        self.time_limit = time_limit
        self.threadName = threadName
        self.recieverIP = recieverIP

    def run(self):
        while self.window.isPktTrans:
            if self.window.isEmpty():
                continue

            status = select.select([senderSock], [], [], self.time_limit)
            if not status[0]:
                continue

            try:
                recvData, recvAddr = senderSock.recvfrom(4096)
                recvData = pickle.loads(recvData)
                print("recvied ack", recvData.seqNum)
            except Exception as e:
                print("Recv error")

            if recvAddr[0] != self.recieverIP:
                print("not safe")
                continue

            if recvData.Ack == 0:
                print("Not Acked by server", recvData.seqNum)
                continue

            if self.isCorrupt(recvData):
                print("corrupted ack")
                continue

            if not self.window.isPresent(recvData.seqNum):
                print("lost Ack")
                continue

            self.window.ackit(recvData.seqNum)

    def isCorrupt(self, recvData):
        cal_hash = hashlib.sha256(recvData.data).hexdigest()
        if(recvData.checksum == cal_hash):
            print("checking...fine")
            return False
        else:
            print("checking...corrupted")
            return True
