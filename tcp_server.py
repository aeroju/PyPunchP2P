import socket
import logging
import threading
import time

from message_wrapper import *
logger = logging.getLogger('tcp_server')
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(message)s')

class TcpServer(object):
    def __init__(self,port):
        self.port = port
        self.clients={}
        self.peers = {}

    def _addr_to_key(self,addr):
        return addr[0] + ':' + str(addr[1])

    def get_client(self,addr):
        return self.clients.get(self._addr_to_key(addr))

    def set_client(self,addr,client_info):
        self.clients[self._addr_to_key(addr)] = client_info

    def _client_handler(self,conn,client_addr,stop_event):
        while(not stop_event.is_set()):
            try:
                data = conn.recv(1024)
                command,msg = de_wapper(data)
                logger.info('from client command: %d,%s', command,msg.__str__())
                if(command==COMMAND_SIGN):
                    client_local_addr = msg['local_addr']
                    peer_key = msg['peer_key']
                    client_info = self.get_client(client_addr)
                    client_info['local_addr'] = client_local_addr
                    client_info['peer_key'] = peer_key
                    self.set_client(client_addr,client_info)
                    msg = {'public_addr':client_addr}
                    logger.info('message send to client:%s', msg.__str__())
                    conn.send(wapper(COMMAND_SIGN_ACK,msg))
                elif(command==COMMAND_REQUEST_PEER):
                    peer_key = msg['peer_key']
                    peers = []
                    logger.info('begin to get peer for:%s:%d',client_addr[0],client_addr[1])
                    for key,item in self.clients.items():
                        if(item.get('peer_key') is not None and item.get('peer_key')==peer_key):
                            if(key!=self._addr_to_key(client_addr)):
                                peers.append(item.get('public_addr'))
                                #send peers to A
                                item['conn'].send(wapper(COMMAND_REQUEST_PEER_CLIENT,{'peers':client_addr}))
                    if len(peers)>0: peers.append(())
                    msg={'peers':peers}
                    logger.info('message send to client:%s', msg.__str__())
                    conn.send(wapper(COMMAND_REQUEST_PEER_ACK,msg))

            except socket.timeout:
                conn.close()
                break

    def _accept(self,fsock,stop_event):
        while(not stop_event.is_set()):
            try:
                conn,addr = fsock.accept()
            except socket.timeout:
                logger.info('timeout waiting for next connect')
                continue
            logger.info('connection from: %s:%d',addr[0],addr[1])
            client_thread = threading.Thread(target=self._client_handler,args=(conn,addr,stop_event))
            client_info = {}
            client_info['thread'] = client_thread
            client_info['public_addr'] = addr
            client_info['conn'] = conn
            self.set_client(addr,client_info)
            client_thread.start()


    def run(self):
        self.stop_event = threading.Event()

        self.fsock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.fsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.fsock.bind(('0.0.0.0',self.port))
        self.fsock.listen()
        # self.fsock.settimeout(2)
        logger.info('server start at %d' , self.port)

        self.run_thread =  threading.Thread(target=self._accept,args=(self.fsock,self.stop_event,))
        self.run_thread.start()

    def stop(self):
        self.stop_event.set()
        time.sleep(1)
        self.fsock.close()

if __name__ == '__main__':
    server = TcpServer(12345)
    server.run()
    input()
    logger.info('waiting connections to close')
    server.stop()