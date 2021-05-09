from SUDPServer import SUDPServer
import time
import os
import sys
import argparse

if __name__ == "__main__":
    print('Welcome to this simple file-transfer server! \n That accepts the files...')

    senderIP_ft = "127.0.0.1"
    senderPort_ft = 8081
    recieverIP_ft = "127.0.0.1"
    recieverPort_ft = 8080

    server = SUDPServer(senderIP_ft, senderPort_ft,
                        recieverIP_ft, recieverPort_ft)
    server.open()
    server.recv()
