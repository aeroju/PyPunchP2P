import socket
import threading
import time
import logging

from message_wrapper import *
logger = logging.getLogger('tcp_client')
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(message)s')


class TcpClient(object):
    def __init__(self,server_addr,server_port,timeout=5):
        self.server = (server_addr,server_port)
        self.timeout = timeout

    def _local_server_hanlder(self,conn):
        while not self.stop_event.is_set():
            try:
                data = conn.recv(1024)
                if(len(data)>0):
                    command,msg = de_wapper(data)
                    logger.info('message from peer: %d,%s',command,msg.__str__())
            except:
                time.sleep(1)
                continue
        conn.close()

    def _accept(self,port):
        logger.info('starting local server on port %d for peer to connect...',port)
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(('',port))
        sock.listen()
        while(not self.stop_event.is_set()):
            try:
                conn,addr = sock.accept()
                logger.info('connection received----------------------')
                conn.settimeout(self.timeout)
                conn.send(wapper(COMMAND_TEXT,{'msg':'ping'}))
                server_thread = threading.Thread(target=self._local_server_hanlder,args=(conn,))
                server_thread.start()
            except socket.timeout:
                logger.info('_accept timeout')
                time.sleep(1)
                continue
        sock.close()


    def _connect(self,local,peer):
        logger.info('begin to connect to peer:%s:%d',peer[0],peer[1])
        for i in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                sock.bind(local)
                sock.settimeout(2)
                sock.connect(peer)
                logger.info('connect to peer success, begin send hello')
                bts = sock.send(wapper(COMMAND_TEXT, {'msg': 'hello'}))
                print(sock.getpeername(),':',bts)
                logger.info('hello send, send next 20 hello')
                for _ in range(20):
                    sock.send(wapper(COMMAND_TEXT, {'msg': 'hello'}))
                while not self.stop_event.is_set():
                    try:
                        data = sock.recv(1024)
                        if(len(data)>0):
                            command, msg = de_wapper(data)
                            logger.info('message send to peer:%d,%s', command, msg.__str__())
                            sock.send(data)
                    except socket.error:
                        time.sleep(1)
                        continue
                sock.close()
                break
            except socket.error as e:
                print('trying:',i,e)
                time.sleep(0.5)
                continue


    def run(self,port = 1234,key = 100):
        self.fsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.fsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.fsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
        logger.info('trying to connect to:%s:%d',self.server[0],self.server[1])
        self.fsock.connect(self.server)
        logger.info('connect to server and regist for peer key %s',key)
        self.local_addr = self.fsock.getsockname()

        self.stop_event = threading.Event()

        msg = {'local_addr':self.local_addr,'peer_key':key}
        self.fsock.send(wapper(COMMAND_SIGN,msg))

        data = self.fsock.recv(1024)
        command,msg = de_wapper(data)
        if(command==COMMAND_SIGN_ACK):
            self.public_addr = msg['public_addr']
            logger.info('public address: %s:%d',self.public_addr[0],self.public_addr[1])
            self.local_server_thread_0 = threading.Thread(target=self._accept,args=(self.local_addr[1],))
            self.local_server_thread_0.start()
            # self.local_server_thread_1 = threading.Thread(target=self._accept, args=(self.public_addr[1],))
            # self.local_server_thread_1.start()

        logger.info('requesting peer...')
        self.fsock.send(wapper(COMMAND_REQUEST_PEER,{'peer_key':key}))
        while True:
            try:
                data = self.fsock.recv(1024)
                command,msg = de_wapper(data)
                if(command==COMMAND_REQUEST_PEER_ACK):
                    peers_raw = msg['peers']
                    if(type(peers_raw)==tuple):
                        peers =[]
                        peers.append(peers_raw)
                    else:
                        peers = peers_raw
                    # logger.info('peers: %s',peers.__str__())
                    self.peers_thread=[]
                    for peer in peers:
                        # peer = tuple(peer)
                        # print(peer)
                        if(len(peer)==2):
                            peer_thread = threading.Thread(target=self._connect,args=(self.local_addr,peer,))
                            self.peers_thread.append(peer_thread)
                            peer_thread.start()
                elif(command==COMMAND_REQUEST_PEER_CLIENT): #there will be connection from client, act like server
                    peers_raw = msg['peers']
                    if(type(peers_raw)==tuple):
                        peers =[]
                        peers.append(peers_raw)
                    else:
                        peers = peers_raw
                    for i in range(10):
                        try_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        try_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        try_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                        try_sock.bind(self.local_addr)
                        try_sock.connect_ex(peers[0])
                        try_sock.close()
                        logger.info('send %d ack to peer(%s:%d) finished',i+1,peers[0][0],peers[0][1])
                        time.sleep(1)

            except:
                break


if __name__ == '__main__':
    TcpClient('13.115.178.224',12345).run(key=100)

