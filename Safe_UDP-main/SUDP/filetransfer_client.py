from SUDPClient import SUDPClient
import time
import os
import sys
import argparse

if __name__ == "__main__":
    print('Simple file client \n Upload your files to the server')
    filename = str(input('Enter the file you want to send: '))
    #parser.add_argument('--filename', default='tosend.txt', type=str)
    #args = parser.parse_args()

    senderIP_ft = "127.0.0.1"
    senderPort_ft = 8081
    recieverIP_ft = "127.0.0.1"
    recieverPort_ft = 8080
    client = SUDPClient(filename, senderIP_ft,
                        senderPort_ft, recieverIP_ft, recieverPort_ft)
    client.open()
    client.send()
