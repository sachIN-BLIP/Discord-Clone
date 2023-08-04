import zmq
import json
import uuid
import datetime
import time

LOCALHOST = '127.0.0.1'
class Client:
    def __init__(self,address,registry_server_addr):
        self.address = address
        self.registry_server_addr = registry_server_addr
    

    def make_JoinServer(self, uuid):
        message = {
            'type': 'JoinServer',
            'uuid': uuid 
        }
        message =  json.dumps(message)
        return message

    def make_LeaveServer(self, uuid):
        message =  {
            'type': 'LeaveServer',
            'uuid': uuid
        }
        message =  json.dumps(message)
        return message

    def make_GetArticle(self, type, author,time, uuid):
        message = {
            'type' : 'GetArticle',
            'ArticleType': type,
            'Author': author,
            'time': time,
            'uuid': uuid
        }
        return message
    
    def make_PublishArticle(self, type, author, content, uuid):
        message = {
        'type': 'PublishArticle',
        'ArticleType': type,
        'Author' : author,
        'Content': content,
        'uuid' : uuid
        }
        return message

    def make_GetServerList(self,uuid):
        message = {
            'type': 'GetServerList',
            'uuid': uuid
        }
        message = json.dumps(message)
        return message

    def make_Response(self,status):
        message = {
            'status': status
        }
        message = json.dumps(message)
        return message

    def invalidChoice(self):
        print("----------INVALID CHOICE. CHOOSE AGAIN----------",end = '\n\n')
        self.start()    


    def send_message(self,routing_key,message):
        context = zmq.Context()
        context.setsockopt(zmq.LINGER, 2000)
        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.RCVTIMEO, 5000)
        socket.setsockopt(zmq.SNDTIMEO, 5000)
        socket.connect(f"tcp://localhost:{routing_key}")



        try:
            socket.send_string(message)
            message = socket.recv()
        except:
            print("SERVER NOT AVAILABLE!")
            message = self.make_Response("FAIL")
            # return message
        finally:
            socket.close()
            context.term()
            
        try:
            message = json.loads(message)
        except Exception as e:
            print("NO RESPONSE FROM SERVER")
            return self.make_Response("FAIL")
        return message
        
    def GetServerList(self):
        message = self.make_GetServerList(self.address)
        ServerListResponse = self.send_message(self.registry_server_addr,message)
        return ServerListResponse['servers']
       
    def joinServer(self,server_addr):
        message = self.make_JoinServer(self.address)
        try:
            JoinResponse = self.send_message(server_addr,message)
        except Exception as e:
            print("-----SERVER DOWN. TRY AGAIN LATER!------")
            self.start()
        if(JoinResponse['status'] == 'FAIL'):
            print("FAIL",end = '\n\n')
        elif(JoinResponse['status'] == 'SUCCESS'):
            print("SUCCESS",end = '\n\n')

    def leaveServer(self,server_addr):
        message = self.make_LeaveServer(self.address)
        try:
            LeaveResponse = self.send_message(server_addr,message)
        except Exception as e:
            print("-----SERVER DOWN. TRY AGAIN LATER!------")
            self.start()
        if(LeaveResponse['status'] == 'FAIL'):
            print("FAIL",end = '\n\n')
        elif(LeaveResponse['status'] == 'SUCCESS'):
            print("SUCCESS", end = '\n\n')

    def getArticle(self,server_addr):
        article = self.make_GetArticle('','','','')
        article['uuid'] = self.address
        print("CHOOSE 1 CATEGORY FROM OPTIONS:")
        print("1) SPORTS")
        print("2) FASHION")
        print("3) POLITICS")
        print("4) <BLANK>")

        inp = int(input("Input: "))
        match inp:
            case 1:
                article['ArticleType'] = 'SPORTS'
            case 2:
                article['ArticleType'] = 'FASHION'
            case 3:
                article['ArticleType'] = 'POLITICS'
            case 4:
                pass
            case default:
                print("INVALID CHOICE. CHOOSE AGAIN")
                self.getArticle(server_addr)
                return

        print("CHOOSE 1 CATEGORY FROM OPTIONS:")
        print("1) ENTER AUTHOR NAME")
        print("2) LEAVE AUTHOR NAME <BLANK>")

        try:
            inp = int(input("Input: "))
        except ValueError:
            print("----------INVALID OPTION. CHOOSE AGAIN----------")
            self.getArticle(server_addr)
            return

        match inp:
            case 1:
                article['Author'] = input("Enter Author Name: ")
            case 2:
                pass
            case default:
                print("INVALID CHOICE. CHOOSE AGAIN")
                self.getArticle(server_addr)
                return
            
        print("CHOOSE 1 CATEGORY FROM OPTIONS:")
        print("1) ENTER DATE")
        print("2) LEAVE DATE <BLANK>")

        try:
            inp = int(input("Input: "))
        except ValueError:
            print("----------INVALID OPTION. CHOOSE AGAIN----------")
            self.getArticle(server_addr)
            return

        match inp:
            case 1:
                date_string = input("ENTER DATE IN FORMAT YYYY-MM-DD:")
                try:
                    date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
                    article['time'] = date_string
                except Exception as e:
                    print("----INVALID INPUT FOR DATE. CHOOSE AGAIN-----")
                    self.getArticle(server_addr)
                    return
            case 2:
                pass
            case default:
                print("INVALID CHOICE. CHOOSE AGAIN")
                self.getArticle(server_addr)
                return
        
        
        article = json.dumps(article)  

        try:
            ArticleResponse = self.send_message(server_addr,article)
        except Exception as e:
            print("-----SERVER DOWN. TRY AGAIN LATER!------")
            self.start()
            return

        if(ArticleResponse['status'] == 'FAIL'):
            print("FAILED")
            return
        
        i=1
        for article in ArticleResponse['articles']:
            print(f"{i}){article['ArticleType']} \n {article['Author']} \n {article['time']} \n {article['Content']}")
            i+=1
        print()

    def publishArticle(self,server_addr):
        article = self.make_PublishArticle('','','','')
        article['uuid'] = self.address
        print("CHOOSE 1 CATEGORY FROM OPTIONS:")
        print("1) SPORTS")
        print("2) FASHION")
        print("3) POLITICS")

        inp = int(input("Input: "))
        match inp:
            case 1:
                article['ArticleType'] = 'SPORTS'
            case 2:
                article['ArticleType'] = 'FASHION'
            case 3:
                article['ArticleType'] = 'POLITICS'
            case default:
                print("INVALID CHOICE. CHOOSE AGAIN")
                self.publishArticle(server_addr)
                return
        while(article['Author'] == ''):
            article['Author'] = input("Enter the author name: ")
            if(article['Author'] == ''):
                print("------BLANK FIELD NOT ALLOWED. ENTER AGAIN-----")

        while(article['Content'] == ''):        
            article['Content'] = input("Enter the content of the article: ")
            if(article['Content'] == ''):
                print("------BLANK FIELD NOT ALLOWED. ENTER AGAIN------")

        article = json.dumps(article)
        print()
        
        PublishResponse = self.send_message(server_addr,article)
        print("SEND MESSAGE RETURNED")
        if(PublishResponse['status'] == 'FAIL'):
            print("FAIL",end = "\n\n")
        elif(PublishResponse['status'] == 'SUCCESS'):
            print("SUCCESS", end = "\n\n")


    def server_menu(self,server):
        server_name,server_addr = server[0],server[1]
        print(f"SERVER MENU: {server_name}")
        while True:
            print("1) Join Server")
            print("2) Leave Server")
            print("3) Get Articles")
            print("4) Publish Article")

            try:
                inp = int(input("CHOOSE FROM OPTIONS (0 to go MAIN MENU): "))
            except Exception as e:
                print("----INVALID INPUT. CHOOSE AGAIN----")
                continue
            print()
            if(inp == 0):
                self.start()
            elif(inp == 1):
                self.joinServer(server_addr)
            elif(inp == 2):
                self.leaveServer(server_addr)
            elif(inp == 3):
                self.getArticle(server_addr)
            elif(inp == 4):
                self.publishArticle(server_addr)
            else:
                print("INVALID CHOICE. CHOOSE AGAIN")

    def start(self):
        
        print("LIST OF SERVERS ON REGISTRY SERVER:",end = '\n\n')
        servers = self.GetServerList()
        i = 1
        for server in servers:
            print(f"{i}) {server[0]} - {f'tcp://{LOCALHOST}:{server[1]}'}")
            i+=1
        print()

        try:
            inp = int(input("CHOOSE NUMBER FROM ABOVE TO ENTER SERVER MENU (1001 to request list of servers again, 0 to exit): "))
            print()
        except ValueError:
            self.invalidChoice()

        if inp == 1001:
            self.start()
        elif inp<0 or inp>=i:
            self.invalidChoice()
        elif(inp == 0):
            exit(1)
        else:
            self.server_menu(servers[inp-1])
            

if __name__ == '__main__':
    UUID = str(uuid.uuid1())
    REGISTRY_SERVER_ADDR = 5555
    client = Client(UUID,REGISTRY_SERVER_ADDR)
    # client.channel.start_consuming()
    print(f'Client started with UUID:{UUID}')
    client.start()
