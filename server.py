'''A P2P-CI Server for CSC 401-001 Project 1'''
import os
from socket import AF_INET, SOCK_STREAM, socket
import sys
from _thread import*
from urllib3 import get_host

class Peer:
    '''Defines a Peer'''
    def __init__(self, host, port):
        self.host = host
        self.port = port

class RFC:
    '''Defines an RFC'''
    def __init__(self, num, title, host, port):
        self.number = num
        self.title = title
        self.host = host
        self.port = port



def get_peer_host(peer):
    '''Retreives the peer host name'''
    return peer.host

def get_peer_port(peer):
    '''Retreives the peer port number'''
    return peer.port

def get_rfc_number(rfc):
    '''Retreives the RFC number'''
    return rfc.number

def get_rfc_title(rfc):
    '''Retreives the RFC title'''
    return rfc.title

def get_rfc_host(rfc):
    '''Retreives the RFC host name'''
    return rfc.host

VERSION = 'P2P-CI/1.0'

# The port the server uses
SERVERPORT = 7734

peerList = []
rfcList = []
global running
running = 1

def add(rfcnum, rfctitle, peer_hostname, peer_port):
    '''Add an RFC and peer to the lists'''

    add_to_rfc = 0
    add_to_peer = 0

    global rfcList
    global peerList

    for j in range(len(rfcList)):
        if rfcList[j].number == rfcnum and rfcList[j].host == peer_hostname:
            for i in range(peerList):
                if peerList[i].host == peer_hostname and peerList[i].port == peer_port:
                    add_to_rfc = 1
    for j in range(len(peerList)):
        if peerList[j].host == peer_hostname and peerList[j].port == peer_port:
            add_to_peer = 1

    if add_to_rfc == 0:
        rfcList.append(RFC(int(rfcnum), rfctitle, peer_hostname, peer_port))
        rfcList.sort(key=get_rfc_number)
    if add_to_peer == 0:
        peerList.append(Peer(peer_hostname, peer_port))

def lookup(rfc_num):
    '''Checks to see if an RFC is available'''
    found_list = []
    num_found = 0

    global rfcList
    global peerList

    for j in range(len(rfcList)):
        rfc_num_to_compare = get_rfc_number(rfcList[j])
        if rfc_num_to_compare == int(rfc_num):
            found_list.append(rfcList[j])
            num_found += 1

    if num_found > 0:
        found_list.sort(key=get_rfc_number)
        return found_list
    else:
        return None

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', SERVERPORT))
serverSocket.listen(1)

print('Server is Ready')


def new_thread(connectionSocket, addr):
    global running
    global rfcList
    global peerList

    print(str(addr) + " Connected")
    peer_version = ''
    peer_hostname = ''

    # loop while peer is connected to receive more messages
    while running == 1:
        message = connectionSocket.recv(1024)
        # if not message: break
        received = message.decode()
        print('INCOMING MESSAGE:\n' + received)
        lines = received.split('\r\n')
        line = lines[0].split(' ')

        # Process an ADD request
        if line[0] == 'ADD':
            rfcnum = line[2]
            peer_version = line[3]
            # Send code 505 if version number doesn't match
            if peer_version != VERSION:
                message = VERSION + ' 505 Version Not Supported\r\n'
                message_bytes = message.encode('utf-8')
                connectionSocket.send(message_bytes)
                break

            line = lines[1].split(' ')
            peer_hostname = line[1]
            line = lines[2].split(' ')
            peer_port = line[1]
            rfctitle = lines[3]
            rfctitle = rfctitle[7:len(lines[3])]

            add(rfcnum, rfctitle, peer_hostname, peer_port)
            message = VERSION + ' 200 OK\r\nRFC ' + str(rfcnum) + ' ' + rfctitle + ' ' + peer_hostname + ' ' + peer_port + '\r\n'
            message_bytes = message.encode('utf-8')
            connectionSocket.send(message_bytes)

        # Process a LOOKUP request
        elif line[0] == 'LOOKUP':
            # Send Code 404 if no RFCs are known
            if len(rfcList) == 0:
                message = VERSION + ' 404 Not Found\r\n'
                message_bytes = message.encode('utf-8')
                connectionSocket.send(message_bytes)
            else:
                rfcnum = line[2]
                peer_version = line[3]
                # Send code 505 if version number doesn't match
                if peer_version != VERSION:
                    message = VERSION + ' 505 Version Not Supported\r\n'
                    message_bytes = message.encode('utf-8')
                    connectionSocket.send(message_bytes)
                    break

                line = lines[1].split(' ')
                peer_hostname = line[1]
                line = lines[2].split(' ')
                peer_port = line[1]
                rfctitle = lines[3]
                rfctitle = rfctitle[7:len(lines[3])]

                available = lookup(rfcnum)
                # Send Code 404 if no RFCs were found that match the RFC to look up
                if available is None:
                    message = VERSION + ' 404 Not Found\r\n'
                    message_bytes = message.encode('utf-8')
                    connectionSocket.send(message_bytes)

                else:
                    # Else send the RFCs that were found
                    outmessage = VERSION + ' 200 OK\r\n'                                
                    for m in range(len(available)):
                        peer_host = get_rfc_host(available[m])
                        peer_port = available[m].port
                        
                        outmessage += 'RFC: ' + str(get_rfc_number(available[m])) + ' ' + get_rfc_title(available[m]) + ' ' + get_rfc_host(available[m]) + ' ' + peer_port + '\r\n'
  
                    connectionSocket.send(outmessage.encode('utf-8'))

        # Process a LIST request
        elif line[0] == 'LIST':
            # Send Code 404 if no RFCs are known
            if len(rfcList) == 0:
                message = VERSION + ' 404 Not Found\r\n'
                message_bytes = message.encode('utf-8')
                connectionSocket.send(message_bytes)

            else:
                peer_version = line[2]
                # Send code 505 if version number doesn't match
                if peer_version != VERSION:
                    message = VERSION + ' 505 Version Not Supported\r\n'
                    message_bytes = message.encode('utf-8')
                    connectionSocket.send(message_bytes)
                    break

                peer_hostname = line[1]
                line = lines[2]
                peer_port = line[1]
                # Send message with all known RFCs
                outmessage = VERSION + ' 200 OK\n'
                for m in range(len(rfcList)):
                    peer_host = get_rfc_host(rfcList[m])
                    peer_port = rfcList[m].port
                    outmessage += 'RFC: ' + str(get_rfc_number(rfcList[m])) + ' ' + get_rfc_title(rfcList[m]) + ' ' + peer_host + ' ' + str(peer_port) + '\r\n'
                connectionSocket.send(outmessage.encode('utf-8'))

        elif line[0] == 'STOP':
            clientname = line[1]
            clientport = line[2]

            indexes = []

            for i in range(len(rfcList)):
                if rfcList[i].host == clientname and rfcList[i].port == clientport:
                    indexes.append(i)

            indexes.sort(reverse=True)

            for each_idx in indexes:
                del rfcList[each_idx]

            indexes.clear()

            for i in range(len(peerList)):
                if peerList[i].host == clientname and peerList[i].port == clientport:
                    indexes.append(i)

            indexes.sort(reverse=True)

            for each_idx in indexes:
                del peerList[each_idx]

            connectionSocket.close()
            print(str(addr) + ' Disconnected.')
            sys.exit()

        elif line[0] == 'SHUTDOWN':
            running = 0
            break
            
        else:
            message = VERSION + ' 400 Bad Request\r\n'
            message_bytes = message.encode('utf-8')
            connectionSocket.send(message_bytes)

serverSocket.settimeout(2)
while running == 1:
    try:
        connectionSocket, addr = serverSocket.accept()
    except:
        pass

    else:
        start_new_thread(new_thread, (connectionSocket,addr))

serverSocket.close()
print('Server has been shutdown')
exit()
