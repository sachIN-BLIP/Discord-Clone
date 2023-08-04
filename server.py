import json
import uuid
import datetime
import time
import zmq

MAXCLIENTS = 10
LOCALHOST = '127.0.0.1'

class Server:
    def __init__(self,name,registry_server_addr):
        self.name = name
        while True:
            port = int(input("Enter the port for this server:"))
            try:
                self.context = zmq.Context()
                self.socket = self.context.socket(zmq.REP)
                # self.socket.setsockopt(zmq.RCVTIMEO, 5000)
                self.socket.bind(f"tcp://{LOCALHOST}:{port}")
                self.address = port
                break
            except Exception as e:
                print(f"Port {port} is already in use. Enter another port number")


        self.registry_server_addr = registry_server_addr        
        self.CLIENTELE = set()
        self.articles = []

    def make_Register(self, server_name,server_addr):
        message = {
            'type': 'Register',
            'name': server_name,
            'address': server_addr
        }
        message =  json.dumps(message)
        return message

    def make_JoinResponse(self,status):
        message = {
            'type': 'JoinResponse',
            'status': status
        }
        message = json.dumps(message)
        return message

    def make_LeaveResponse(self,status):
        message = {
            'type' : 'LeaveResponse',
            'status': status
        }
        message = json.dumps(message)
        return message

    def make_ArticleResponse(self,status,articles):
        message = {
            'type' : 'ArticleResponse',
            'status': status,
            'articles': articles
        }
        return message

    def make_PublishResponse(self,status):
        message = {
            'type' : 'PublishResponse',
            'status': status
        }
        message = json.dumps(message)
        return message
    
    def make_Article(self, ArticleType, author, content):
        message = {
        'ArticleType': ArticleType,
        'Author' : author,
        'Content': content,
        'time': '000',
        }
        return message
    
    def send_message(self,routing_key,message):
        context_new = zmq.Context()
        context_new.setsockopt(zmq.LINGER, 2000)
        socket_new = context_new.socket(zmq.REQ)
        socket_new.setsockopt(zmq.RCVTIMEO, 5000)
        socket_new.setsockopt(zmq.SNDTIMEO, 5000)
        socket_new.connect(f"tcp://localhost:{routing_key}")

        try:
            socket_new.send_string(message)

            message = socket_new.recv()
        except:
            print("REGISTRY SERVER NOT AVAILABLE!")
            message = self.make_JoinResponse("FAIL")
            print()
        finally:
            socket_new.close()
            context_new.term()
        message = json.loads(message)
        return message

    def reply_message(self,message):
        self.socket.send_string(message)

    def callback(self,body):
        message = json.loads(body)

        if message['type'] == 'JoinServer':
            self.JoinServer(message)
        elif message['type'] == 'LeaveServer':
            self.LeaveServer(message)
        elif message['type'] == 'PublishArticle':
            self.PublishArticle(message)
        elif message['type'] == 'GetArticle':
            self.GetArticle(message)
    
    def JoinServer(self,message):
        print()
        print(f"JOIN REQUEST FROM {message['uuid']}")
        if(len(self.CLIENTELE) >= MAXCLIENTS):
            JoinResponse = self.make_JoinResponse("FAIL")
            return self.reply_message(JoinResponse)
        else:
            if(message['uuid'] in self.CLIENTELE):
                print("CLIENT ALREADY PART OF SERVER")
                JoinResponse = self.make_JoinResponse("FAIL")
                return self.reply_message(JoinResponse)
            self.CLIENTELE.add(message['uuid'])
            JoinResponse = self.make_JoinResponse("SUCCESS")
            return self.reply_message(JoinResponse)
            
    def LeaveServer(self,message):
        print()
        print(f"LEAVE REQUEST FROM {message['uuid']}")
        if(message['uuid'] not in self.CLIENTELE):
            print("CLIENT NOT A PART OF SERVER")
            LeaveResponse = self.make_LeaveResponse("FAIL")
            return self.reply_message(LeaveResponse)
        else:
            self.CLIENTELE.remove(message['uuid'])
            LeaveResponse = self.make_LeaveResponse("SUCCESS")
            return self.reply_message(LeaveResponse)
            
    def PublishArticle(self,message):
        print()
        print(f"ARTICLES PUBLISH FROM {message['uuid']}")
        if(message['uuid'] not in self.CLIENTELE):
            print("CLIENT NOT PART OF SERVER")
            PublishResponse = self.make_PublishResponse("FAIL")
            return self.reply_message(PublishResponse)

        current_time = datetime.datetime.now()
         
        new_article = self.make_Article(message['ArticleType'],message['Author'],message['Content'])
        new_article['time'] = current_time
        print(new_article)
        self.articles.append(new_article)
        PublishResponse = self.make_PublishResponse("SUCCESS")
        return self.reply_message(PublishResponse)

    def GetArticle(self,message):
        print()
        print(f"ARTICLES REQUEST FROM {message['uuid']}")
        ArticleResponse = self.make_ArticleResponse("FAIL",[])

        if(message['uuid'] not in self.CLIENTELE):
            print("CLIENT NOT PART OF SERVER")
            ArticleResponse = json.dumps(ArticleResponse)
            return self.reply_message(ArticleResponse)

        # if(message['Author'] == '' and message['ArticleType'] == ''):
        #     print("BOTH FIELDS CANNOT BE LEFT BLANK. CHOOSE AGAIN!")
        #     ArticleResponse = json.dumps(ArticleResponse)
        #     return self.reply_message(properties,channel, ArticleResponse)

        skip = False
        if message['time'] == '':
            skip = True
        else:
            timeString = message['time']
            message['time'] = datetime.datetime.strptime(timeString, '%Y-%m-%d')

        # ArticleResponse['articles'] = []
        for article in self.articles:

            # print(f"article time: {article['time']} message time: {message['time']} response: {(article['time'] <= message['time'])}")
            if (message['Author'] == '' or article['Author'] == message['Author']) and (message['ArticleType']=='' or article['ArticleType'] == message['ArticleType']) and (skip or message['time'] <= article['time']):
                new_article = self.make_Article(article['ArticleType'],article['Author'],article['Content'])
                new_article['time'] = article['time'].strftime("%Y-%m-%d")
                ArticleResponse['articles'].append(new_article)

        if(len(ArticleResponse['articles']) == 0):
            print("NO ARTCLES FOUND")
            ArticleResponse = json.dumps(ArticleResponse)
            return self.reply_message(ArticleResponse)

        ArticleResponse['status'] = 'SUCCESS'
        print("SUCCESS HERE")
        ArticleResponse = json.dumps(ArticleResponse)
        return self.reply_message(ArticleResponse)
    
    def Register(self):
        message = self.make_Register(self.name,self.address)
        RegisterResponse = self.send_message(self.registry_server_addr,message)
        print()
        print(RegisterResponse['status'],end='\n\n')
        self.run()

        
    def run(self):
        print("SERVER RUNNING")
        while True:
            message = self.socket.recv()
            self.callback(message)

    def start(self):
        print()
        print("OPTIONS")
        print("1) Register")
        try:
            inp = int(input("Enter the appropriate option (0 to terminate): "))
        except ValueError:
            print("------INVALID OPTION.CHOOSE AGAIN------")
            self.start()
        print()
        if(inp == 0):
            exit(1)
        elif(inp == 1):
            self.Register()
        else:
            print("INVALID OPTION. EXITING!")
            exit(1)
        
        

if __name__ == '__main__':
    SERVER_NAME = ''
    while SERVER_NAME == '':
        SERVER_NAME = input("Enter the name of the server:")
        if(SERVER_NAME == ''):
            print("SERVER NAME CANNOT BE BLANK! ENTER AGAIN")
    
    REGISTRY_SERVER_ADDR = 5555
    server = Server(SERVER_NAME,REGISTRY_SERVER_ADDR)
    print(f'{server.name} server started at {f"tcp://{LOCALHOST}:{server.address}"}')
    server.start()
      
