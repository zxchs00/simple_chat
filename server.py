#-*-coding:utf-8-*-
import socket
import hashlib
import base64
import struct
import time
from _thread import *

add_key = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

message_for_send = []
client_list = []
nicknames = {}
sending = 0

def receive_message(client_socket):
    byte1, byte2 = client_socket.recv(2)

    opcode = byte1 & 15
    is_mask = byte2 & 128
    payload_length = byte2 & 127

    if not byte1 or opcode == 8 or not is_mask:
        return ''
    if payload_length == 126:
        payload_length = struct.unpack('>H', client_socket.recv(2))[0]
    elif payload_length == 127:
        payload_length == struct.unpack('>Q', client_socket.recv(4))[0]
    
    masks = client_socket.recv(4)
    payload = client_socket.recv(payload_length)
    message_array = bytearray()

    for byte in payload:
        byte ^= masks[len(message_array) % 4]
        message_array.append(byte)
    message = message_array.decode('utf-8')

    return message

def send_message(client_socket, msg):
    sending = 1
    header = bytearray()
    payload = msg.encode('utf-8')
    payload_length = len(payload)

    header.append(129)
    if payload_length <= 125:
        header.append(payload_length)
    elif payload_length >= 126 and payload_length <= pow(2, 16):
        header.append(126)
        header.extend(struct.pack('>H', payload_length))
    elif payload_length <= pow(2,64):
        header.append(127)
        header.extend(struct.pack('>Q', payload_length))
    else:
        print('Not Valid Send payload length')
        return
    try:
        client_socket.send(header + payload)
    except:
        print('something error')
        client_list.remove(client_socket)
    sending = 0

def send_system_message(msg):
    for i in client_list:
        send_message(i, '{}:{}:{}'.format('syst', '', msg))

def threaded(client_socket, addr):
    print('Connected by ', addr[0] + ':' + str(addr[1]))
    global sending
    nicknames[client_socket] = addr[0].split('.')[-1]

    while True:
        try:
            data = receive_message(client_socket)
            if not data:
                print('Disconnected by', addr[0]+':'+str(addr[1]))
                while sending:
                    time.sleep(0.5)
                client_list.remove(client_socket)
                send_system_message('{}님이 나갔습니다.'.format(nicknames[client_socket]))
                break
            print('Received from', addr[0]+':'+str(addr[1]), data)
            nick = nicknames[client_socket]
            
            if data[:5] == 'nick:':
                nicknames[client_socket] = data[5:9]
                send_system_message('[닉변] {} -> {}'.format(nick, data[5:9]))
            elif data[:5] == 'mesg:':
                sending = 1
                for i in client_list:
                    if i == client_socket:
                        msg_type = 'send'
                    else:
                        msg_type = 'recv'
                    now = time.localtime()
                    timedata = '{}{}'.format(str(now.tm_hour).zfill(2), str(now.tm_min).zfill(2))
                    send_message(i, '{}:{}:{}:{}'.format(msg_type, nick, timedata, data))
                sending = 0
            else:
                send_message(client_socket, '{}:{}:{}'.format('syst', '', '무언가 문제가 발생했습니다.'))

        except ConnectionResetError as e:
            print('Disconnected by', addr[0]+':'+str(addr[1]))
            client_list.remove(client_socket)
            send_system_message('{}님이 나갔습니다.'.format(nicknames[client_socket]))
            break
    client_socket.close()

HOST = ''
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

print('server start port:', PORT)

while True:
    print('waiting')
    client_socket, addr = server_socket.accept()
    data = client_socket.recv(1024).decode().split('\r\n')

    for i in data:
        if 'Sec-WebSocket-Key:' in i:
            #print(i.split(' ')[-1])
            key = i.split(' ')[-1].encode() + add_key.encode()
            key_data = base64.b64encode(hashlib.sha1(key).digest()).strip().decode()
            handshake_msg = 'HTTP/1.1 101\r\nUpgrade: WebSocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {}\r\n\r\n'.format(key_data)
            client_socket.send(handshake_msg.encode())
    while sending == 1:
        time.sleep(1)
    client_list.append(client_socket)
    send_system_message(addr[0].split('.')[-1] +' 님이 참여하셨습니다.')
    start_new_thread(threaded, (client_socket, addr))

server_socket.close()