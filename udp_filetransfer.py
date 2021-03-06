import socket
import time
import os
import math

from message_wrapper import *

class FileSender(object):
    def __init__(self,filepath,fsock,target,chunksize = 1024,timeout=2):
        self.filepath = filepath
        self.fsock = fsock
        self.targer = target
        self.chunksize = chunksize
        self.timeout = timeout

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

    def process_msg(self,command,msg):
        if(command==COMMAND_FILETRANSFER_META_ACK):
            print('ack received, send all')
            self._send_all()
        elif(command==COMMAND_FILETRANSFER_BODY_MISS):
            self._send_chunk(msg)
        elif(command==COMMAND_FILETRANSFER_BODY_ACK):
            print('body ack, closing')
            self.close()


    def _send_all(self):
        for c in range(self.chunks):
            data = self.file.read(self.chunksize)
            msg = {'chunk':c,'data':data}
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY,msg),self.targer)
        print('total chunk send:',self.chunks, ' sending body end')
        self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_END,''),self.targer)

    def _send_chunk(self,msg):
        missed = msg['missed']
        print('missed chunk:',missed)
        for c in missed:
            self.file.seek(c * self.chunksize)
            data = self.file.read(self.chunksize)
            msg = {'chunk':c,'data':data}
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY,msg),self.targer)
        print('missed sended, sending body end')
        self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_END,''),self.targer)

    def send(self,filename):
        self.file = open(filename,'rb')
        self._send_meta()
        print('meta sended,waiting for ack')

class FileReceiver(object):
    def __init__(self,filepath,fsock,target,chunksize=1024,timeout=2):
        self.filepath = filepath
        self.fsock = fsock
        self.target = target
        self.chunksize = chunksize
        self.timeout = timeout

    def close(self):
        pass

    def process_msg(self,command,msg):
        if (command == COMMAND_FILETRANSFER_META):
            self._receive_meta(msg)
        elif (command == COMMAND_FILETRANSFER_BODY):
            self._receive_data(msg)
        elif (command == COMMAND_FILETRANSFER_BODY_END):
            self._receive_file_end(msg)


    def _receive_meta(self,msg):
        self.chunks = msg['length']
        self.filename = msg['filename']
        self.file = open(os.path.join(self.filepath,self.filename),'wb')
        print('meta received, sending ack')
        self.fsock.sendto(wapper(COMMAND_FILETRANSFER_META_ACK,''),self.target)
        self.file_content={}

    def _receive_data(self,msg):
        try:
            print('receive_data:',type(msg),msg['chunk'])
            chunk = msg['chunk']
            data = msg['data']
            self.file_content[chunk] = data
        except Exception as e:
            print('except in receive file content:',msg)
            pass

    def _receive_file_end(self,msg):
        print(' body end received, begin check missing')
        missed = []
        for i in range(self.chunks):
            if(self.file_content.get(i) is None):
                missed.append(i)
        if(len(missed)==0):
            print('all chunk received, begin write file')
            for s,c in self.file_content.items():
                self.file.seek(s * self.chunksize)
                self.file.write(c)
            # contents = sorted(self.file_content.keys())
            # for c in contents:
            #     self.file.write(c)
            self.file.close()
            print('file saved, sending ack')
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_ACK,''),self.target)
            return True
        else:
            print('missed chunk:',missed,' sending missed')
            msg = {'missed':missed}
            self.fsock.sendto(wapper(COMMAND_FILETRANSFER_BODY_MISS,msg),self.target)
            return False

class FileTransfer(object):
    def __init__(self,file_path,fsock,target_addr,chunksize=900):
        self.file_sender = FileSender(file_path,fsock,target_addr,chunksize)
        self.file_receiver = FileReceiver(file_path,fsock,target_addr,chunksize)

    def process_msg(self,command,msg):
        if (is_file_transfer_send(command)):
            self.file_receiver.process_msg(command,msg)
        elif (is_file_transfer_receive(command)):
            self.file_sender.process_msg(command,msg)

    def send(self,filename):
        self.file_sender.send(filename)

    def receive(self):
        pass

