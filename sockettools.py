def getFromSocket(theSocket, length):
    expectedLength = length
    receivedLength = 0
    chunks = []
    while receivedLength < expectedLength:
        chunk = theSocket.recv(min(expectedLength - receivedLength, 1024))
        if chunk == b'':
            raise ConnectionResetError("No data received")
        chunks.append(chunk)
        receivedLength += len(chunk)
    data = b''.join(chunks)
    return data


if __name__ == "__main__":
    pass
