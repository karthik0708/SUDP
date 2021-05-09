class Packet:

    def __init__(self,seqNum,Chk,data):
        self.seqNum = seqNum
        self.Ack = 0
        self.packetLength = 0
        self.Rst = 0
        self.Chk = 0
        self.checksum = Chk
        self.data = data  #data in byte stream

    def setRst(self):
        self.Rst = 1

    def setAck(self):
        self.Ack = 1

    # def __str__(self):
    #     s = "-" * 30 + "\n" + \
    #         f"Seqno: {self.seqNum}, ACK: {self.Ack}, FIN: {self.fin}" + "\n" + \
    #         "-" * 30 + "\n"
    #     return s
    

