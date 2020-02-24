import socket
import time
import os
import math

from message_wrapper import *

class FileSender(object):
    def __init__(self,filename,fsock,target,chunksize = 1024,timeout=2):
        self.fsock = fsock
        self.targer = target
        self.chunksize = chunksize
        self.timeout = timeout

        self.file = open(filename,'rb')

    def close(self):
        self.file.close()

    def _send_meta(self):
        size = self.file.seek(0,2)
        self.file.seek(0)
        _,filename = os.path.split(self.file.name)
        meta = {'filename':filename
            ,'length': math.ceil(size / self.chunksize)}
        self.chunks = meta['length']
        self.fsock.sendto(wapper(COMMAND_FILETRANSFER_META,meta),self.targer)

    def _receive_acknowledge(self):
        self.fsock.settimeout(self.timeout)
        try:
            while True:
                data,addr = self.fsock.recvfrom(1024)
                command,msg = de_wapper(data)
                if command == COMMAND_FILETRANSFER_META_ACK:
                    if addr == self.targer:
                        return True
        except socket.timeout as e:
            return False
        finally:
            self.fsock.settimeout(None)

    def _send_all(self):
        for c in range(self.chunks):
            data = self.file.read(self.chunksize)
            msg = {'chunk':c,'data':data}
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY,msg),self.targer)
        self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_END,''),self.targer)

    def _receive_missed(self):
        self.fsock.settimeout(self.timeout)
        self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_END,''),self.targer)
        missed = []
        try:
            data , addr = self.fsock.recvfrom(1024)
            command,msg = de_wapper(data)
            if command == COMMAND_FILETRANSFER_BODY_MISS:
                missed.extend(msg)
                return missed
            elif command == COMMAND_FILETRANSFER_BODY_ACK:
                return []
        except socket.timeout as e:
            return None
        finally:
            self.fsock.settimeout(None)


    def _send_chunk(self,missed):
        for c in missed:
            self.file.seek(c * self.chunksize)
            data = self.file.read(self.chunksize)
            msg = {'chunk':c,'data':data}
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY,msg),self.targer)

    def send(self):
        self._send_meta()
        if(self._receive_acknowledge()):
            time.sleep(1)
            self._send_all()
            missed = self._receive_missed()
            if(missed is None):
                raise socket.timeout
            while len(missed) != 0 :
                time.sleep(1)
                self._send_chunk(missed)
                missed = self._receive_missed()
        self.close()
        return

class FileReceiver(object):
    def __init__(self,filepath,fsock,target,chunksize=1024,timeout=2):
        self.filepath = filepath
        self.fsock = fsock
        self.target = target
        self.chunksize = chunksize
        self.timeout = timeout

    def close(self):
        pass

    def _receive_file(self):
        while(True):
            data,addr = self.fsock.recvfrom(self.chunksize)
            if(addr == self.target):
                command,msg = de_wapper(data)
                if(command==COMMAND_FILETRANSFER_META):
                    self._receive_meta(msg)
                elif(command == COMMAND_FILETRANSFER_BODY):
                    self._receive_data(msg)
                elif(command==COMMAND_FILETRANSFER_BODY_END):
                    ret = self._receive_file_end(msg)
                    if(ret):
                        break


    def _receive_meta(self,msg):
        self.chunks = msg['length']
        self.filename = msg['filename']
        self.file = open(os.path.join(self.filepath,self.filename),'wb')
        self.fsock.sendto(wapper(COMMAND_FILETRANSFER_META_ACK,''),self.target)
        self.file_content={}

    def _receive_data(self,msg):
        chunk = msg['chunk']
        data = msg['data']
        self.file_content[chunk] = data

    def _receive_file_end(self,msg):
        missed = []
        for i in range(self.chunks):
            if(self.file_content.get(i) is None):
                missed.append(i)
        if(len(missed)==0):
            contents = sorted(self.file_content.keys())
            for c in contents:
                self.file.write(c)
            self.file.close()
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_ACK,''),self.target)
            return True
        else:
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_MISS,missed),self.target)
            return False


    def run(self):
        self._receive_file()