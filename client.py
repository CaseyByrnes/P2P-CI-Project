import email
from importlib.resources import path
from socket import*
import platform
import datetime
import os
from _thread import*
from datetime import datetime
import time

today = str(datetime.fromtimestamp(1887639468))

OS = platform.platform()
VERSION = 'P2P-CI/1.0'
OK = '200 OK'
SERVERPORT = 7734
SERVERNAME = 'ubuntu-razer'
CLIENTHOST = platform.node()
print('Enter Port Number. Currently using 5678.')
CLIENTPORT = int(input())
print('Enter RFC Path:')
rfc_path = os.getcwd() + input()

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((SERVERNAME,SERVERPORT))

rfcList = []

def GET_REQUEST(rfc_num, host):
    numberRequest = "GET RFC " + rfc_num + ' ' + VERSION
    hostRequest = "Host: " + host
    OSrequest = "OS:" + OS
    return numberRequest + "\r\n" + hostRequest + "\r\n" + OSrequest + "\r\n"

def ADD_REQUEST(rfc_num, rfc_title):
    numberRequest = "ADD RFC " + rfc_num + ' ' + VERSION
    hostRequest = "Host: " + CLIENTHOST
    portRequest = "Port: " + str(CLIENTPORT)
    titleRequest = "Title: " + rfc_title
    request = numberRequest + "\r\n" + hostRequest + "\r\n" + portRequest  + "\r\n" + titleRequest + "\r\n\r\n"
    # print(request)
    return request

def LOOKUP_REQUEST(rfc_num, rfc_title):
    numberRequest = "LOOKUP RFC " + rfc_num + ' ' + VERSION
    hostRequest = "Host: " + CLIENTHOST
    portRequest = "Port: " + str(CLIENTPORT)
    titleRequest = "Title: " + rfc_title
    return numberRequest + "\r\n" + hostRequest + "\r\n" + portRequest  + "\r\n" + titleRequest + "\r\n\r\n"

def LIST_REQUEST():
    numberRequest = "LIST ALL " + VERSION
    hostRequest = "Host: " + CLIENTHOST
    portRequest = "Port: " + str(CLIENTPORT)

    return numberRequest + "\r\n" + hostRequest + "\r\n" + portRequest  + "\r\n\r\n"

def upload_thread():
    uploadSocket = socket(AF_INET, SOCK_STREAM)
    uploadSocket.bind(('', CLIENTPORT))
    uploadSocket.listen(1)

    running = 1

    while running == 1:
        peerSocket, peerAddress = uploadSocket.accept()
        message_bytes = peerSocket.recv(1024)
        message = message_bytes.decode()
        print('INCOMING MESSAGE:\n' + message)

        lines = message.split('\r\n')
        line = lines[0].split(' ')
        if line[0] == 'GET':
            rfc_num = int(line[2])
            version = line[3]
            
            if version == VERSION:
                peer_host = lines[1]
                peer_host = peer_host[6:len(peer_host)]
                peer_os = lines[2]
                peer_os = peer_os[4:len(peer_os)]
                rfctitle = ''

                file_list = os.listdir(rfc_path)
                for eachFile in file_list:
                    name = eachFile.split(' - ')
                    file_rfc_num = int(name[0])
                    if file_rfc_num == rfc_num:
                        rfctitle = name[1]
                        rfctitle = rfctitle[0:len(rfctitle) - 4]
                        break

                rfc_file_path = rfc_path + str(rfc_num) + ' - ' + rfctitle + '.txt'

                current_file = open(rfc_file_path, 'r')
                data = current_file.read()

                response = VERSION + ' ' + OK + '\r\n'
                response += 'Date: ' + today + '\r\n'
                response += 'OS: ' + OS + '\r\n'
                response += 'Last-Modified: ' + str(time.ctime(os.path.getmtime(rfc_file_path))) + '\r\n'
                response += 'Content-Length: ' + str(len(data)) + '\r\n'
                response += 'Content-Type: text/plain\r\n'

                response_bytes = response.encode('utf-8')
                peerSocket.send(response_bytes)
                data_bytes = data.encode('utf-8')
                peerSocket.sendall(data_bytes)


            else:
                message = VERSION + ' 505 Version Not Supported\n'
                message_bytes = message.encode('utf-8')
                peerSocket.send(message_bytes)

        else:
            message = '400 Bad Request\r\n'
            message_bytes = message.encode('utf-8')
            peerSocket.send(message_bytes)

def recvall(sock, size):
    data = bytearray()
    while len(data) < size:
        packet = sock.recv(1024)
        if not packet:
            return None
        data.extend(packet)
    return data

def download_thread(peer_request_bytes, peer_host,peer_port, rfc_num, rfc_title):

    peerSocket = socket(AF_INET, SOCK_STREAM)
    peerSocket.connect((peer_host,int(peer_port)))
    peerSocket.send(peer_request_bytes)
    peer_response_bytes = peerSocket.recv(1024)
    peer_response = peer_response_bytes.decode()
    print('INCOMING MESSAGE:\n' + peer_response.rsplit('\r\n', 6)[0])

    if 'OK' in peer_response:
        print('Downloading RFC: ' + str(rfc_num) + ' from peer.')
        lines = peer_response.split('\r\n')

        size_line = lines[4].split(' ')
        file_size = int(size_line[1])
        data_bytes = recvall(peerSocket, file_size)
        data = data_bytes.decode()
        
        rfc_path_name = rfc_path + str(rfc_num) + ' - ' + rfc_title + '.txt'
        try:
            with open(rfc_path_name, 'w') as f:
                f.write(data)
        except:
            print('File already downloaded.')
            print("Enter LIST, LOOKUP, GET, EXIT or SHUTDOWN")
        else:
            add_request = ADD_REQUEST(rfc_num, rfc_title)
            add_request_bytes = add_request.encode('utf-8')
            clientSocket.send(add_request_bytes)
            response_bytes = clientSocket.recv(1024)
            response = response_bytes.decode()
            
            if 'OK' in response:
                print('RFC: ' + str(rfc_num) + ' downloaded and added to server.')
                print("Enter LIST, LOOKUP, GET, EXIT or SHUTDOWN")

    peerSocket.close()

def UI(clientSocket):
    running = 1
    initial_rfcs(clientSocket)
    while running == 1:
        print("Enter LIST, LOOKUP, GET, EXIT or SHUTDOWN")
        user_input = input().upper()
        print()

        if user_input == 'GET':
            print('Enter RFC number:')
            rfc_num = input()
            print('Enter Title:')
            rfc_title = input()
            
            request = LOOKUP_REQUEST(rfc_num, rfc_title)
            request_bytes = request.encode('utf-8')
        
            clientSocket.send(request_bytes)
            response_bytes = clientSocket.recv(1024)
            response = response_bytes.decode()
            print('INCOMING MESSAGE:\n' + response)
            

            if 'Not Found' in response or 'Not Supported' in response or 'Bad Request' in response:
                pass
            else:
                lines = response.split('\r\n')
                info_line = lines[1].split(' ')
                peer_port = info_line[len(info_line) - 1]
                peer_host = info_line[len(info_line) - 2]

                peer_request = GET_REQUEST(rfc_num, peer_host)
                peer_request_bytes = peer_request.encode('utf-8')
                
                start_new_thread(download_thread, (peer_request_bytes, peer_host, peer_port, rfc_num, rfc_title))
                


        elif user_input == 'LOOKUP':
            print('Enter RFC number:')
            rfc_num = input()
            print('Enter Title:')
            rfc_title = input()
            request = LOOKUP_REQUEST(rfc_num, rfc_title)
            request_bytes = request.encode('utf-8')
        
            clientSocket.send(request_bytes)
            response_bytes = clientSocket.recv(1024)
            response = response_bytes.decode()
            print('INCOMING MESSAGE:\n' + response)

        elif user_input == 'LIST':
            request = LIST_REQUEST()
            request_bytes = request.encode('utf-8')
            clientSocket.send(request_bytes)
            response_bytes = clientSocket.recv(1024)
            response = response_bytes.decode()
            print('INCOMING MESSAGE:\n' + response)

        elif user_input == 'EXIT':
            message = 'STOP ' + CLIENTHOST + ' ' + str(CLIENTPORT) + '\r\n'
            message_bytes = message.encode('utf-8')
            clientSocket.send(message_bytes)
            clientSocket.close()
            running = 0

        elif user_input == 'SHUTDOWN':
            message = 'SHUTDOWN Server\r\n'
            message_bytes = message.encode('utf-8')
            clientSocket.send(message_bytes)
            clientSocket.close()
            shutdown_command()

        else:
            message = 'Bad Message\r\n'
            message_bytes = message.encode('utf-8')
            clientSocket.send(message_bytes)
            response_bytes = clientSocket.recv(1024)
            response = response_bytes.decode()
            print('INCOMING MESSAGE:\n' + response)


def initial_rfcs(clientSocket):
    num_files = 0
    file_list = os.listdir(rfc_path)
    for eachFile in file_list:
        name = eachFile.split(' - ')
        rfc_num = name[0]
        rfc_title = name[1]
        rfc_title = rfc_title[0:len(rfc_title)-4]
        request = ADD_REQUEST(rfc_num, rfc_title)
        request_bytes = request.encode('utf-8')
        clientSocket.send(request_bytes)
        response_bytes = clientSocket.recv(1024)
        response = response_bytes.decode()
        print('INCOMING MESSAGE:\n' + response)
        if 'OK' in response:
            num_files += 1
        else:
            print(response)
    return num_files

def shutdown_command():
    print('Sever has been shutdown.\nExiting.')
    exit()


start_new_thread(upload_thread,())

UI(clientSocket)
