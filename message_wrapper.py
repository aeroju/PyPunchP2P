# coding:utf-8

import pickle

__version__ = "0.0.1"

COMMAND_FILETRANSFER=100
COMMAND_FILETRANSFER_META=101
COMMAND_FILETRANSFER_BODY=102
COMMAND_FILETRANSFER_BODY_END=103
COMMAND_FILETRANSFER_META_ACK=104
COMMAND_FILETRANSFER_BODY_MISS=105
COMMAND_FILETRANSFER_BODY_ACK=106

COMMAND_TEXT = 200

COMMAND_SIGN = 300
COMMAND_SIGN_ACK = 301

COMMAND_REQUEST_PEER = 400
COMMAND_REQUEST_PEER_ACK = 401
COMMAND_REQUEST_PEER_CLIENT = 402

Commands_File_Transfer_Receive=[COMMAND_FILETRANSFER_META_ACK
                            ,COMMAND_FILETRANSFER_BODY_MISS
                            ,COMMAND_FILETRANSFER_BODY_ACK
                            ]
Commands_File_Transfer_Send = [COMMAND_FILETRANSFER
            ,COMMAND_FILETRANSFER_META
            ,COMMAND_FILETRANSFER_BODY
            ,COMMAND_FILETRANSFER_BODY_END]

Commands_File_Transfer=[]
Commands_File_Transfer.extend(Commands_File_Transfer_Receive)
Commands_File_Transfer.extend((Commands_File_Transfer_Send))
Commands_Text = [COMMAND_TEXT]
Commands = []
Commands.extend(Commands_Text)
Commands.extend(Commands_File_Transfer)

def is_file_transfer(command):
    return command in Commands_File_Transfer

def is_file_transfer_receive(command):
    return command in Commands_File_Transfer_Receive

def is_file_transfer_send(command):
    return command in Commands_File_Transfer_Send


def wapper(command,msg):
    # if command not in Commands:
    #     return None
    content = {'command':command,'body':msg}
    return pickle.dumps(content)

def de_wapper(msg_body):
    try:
        content = pickle.loads(msg_body)
        command = content['command']
        msg = content['body']
        return command,msg
    except :
        print('error when de_wapper:',msg_body)
        return None,None