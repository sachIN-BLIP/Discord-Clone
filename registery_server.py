import json
import time
import zmq


MAXSERVERS = 10
LOCALHOST = '127.0.0.1'
class RegistryServer:
    def __init__(self):
        self.servers = {}
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{LOCALHOST}:5555")
    
    def make_RegisterResponse(self,status):
        message  = {
            'type': 'RegisterResponse',
            'status': status
        }
        message = json.dumps(message)
        return message

    def make_ServerListResponse(self,servers):
        message = {
            'type': 'ServerListResponse',
            'servers' : servers
        }
        message = json.dumps(message)
        return message
    
    def reply_message(self,message):
        self.socket.send_string(message)

    def Register(self,message):
        server_name,server_address = message['name'],message['address']
        print(f"JOIN REQUEST FROM {f'tcp://{LOCALHOST}:{server_address}'}")

        if(len(self.servers) >= MAXSERVERS):
            RegisterResponse = self.make_RegisterResponse('FAIL')
            return self.reply_message(RegisterResponse)
        if server_name in self.servers.keys():
            print(f"{server_name} already Registered")
            RegisterResponse = self.make_RegisterResponse('FAIL')
            self.reply_message(RegisterResponse)
            return

        self.servers[server_name] = server_address
        print(f"Registered server {server_name} at address {f'tcp://{LOCALHOST}:{server_address}'}")
        RegisterResponse = self.make_RegisterResponse('SUCCESS')
        self.reply_message(RegisterResponse)
        
    def GetServerList(self,message):
        server_list = []
        for server in self.servers:
            server_list.append([server,self.servers[server]])

        ServerListResponse = self.make_ServerListResponse(server_list)
        self.reply_message(ServerListResponse) 

    def handle_registry_message(self,body):
        message = json.loads(body)
        
        if message['type'] == 'Register':
            self.Register(message)
            
        elif message['type'] == 'GetServerList':
            self.GetServerList(message)
        
    def start(self):
        print("Registry server started")
        while True:
            message = self.socket.recv()
            self.handle_registry_message(message)

if __name__ == "__main__":
    registry_server = RegistryServer()
    registry_server.start()
