import pickle

COMMAND_FILETRANSFER=100
COMMAND_FILETRANSFER_META=101
COMMAND_FILETRANSFER_BODY=102
COMMAND_FILETRANSFER_BODY_END=102
COMMAND_FILETRANSFER_META_ACK=103
COMMAND_FILETRANSFER_BODY_MISS=104
COMMAND_FILETRANSFER_BODY_ACK=105

COMMAND_TEXT = 200

Commands = [COMMAND_FILETRANSFER
            ,COMMAND_FILETRANSFER_META
            ,COMMAND_FILETRANSFER_BODY
            ,COMMAND_FILETRANSFER_BODY_END
            ,COMMAND_FILETRANSFER_META_ACK
            ,COMMAND_FILETRANSFER_BODY_MISS
            ,COMMAND_FILETRANSFER_BODY_ACK

            ,COMMAND_TEXT

            ]




def wapper(command,msg):
    if command not in Commands:
        return None
    content = {'command':command,'body':msg}
    return pickle.dumps(content)

def de_wapper(msg_body):
    content = pickle.loads(msg_body)
    command = content['command']
    msg = content['body']
    if command not in Commands:
        return None,None
    return command,msg