import os
os.environ["PYRO_LOGFILE"] = "pyro.log"
os.environ["PYRO_LOGLEVEL"] = "DEBUG"

import Pyro4
import sys
import socket

"""
Client side application for the 2017/18 Networks and Distributed Systems
Summative Assignment.

Author: Z0954757
"""


def main():

    """Main function to initiate client application launch.
    """

    print "Client application for the Distributed Systems summative assignment."
    print "Author: Z0954757"
    user_name = raw_input("Please enter your name to use the system >>")
    client = ClientApplication(user_name)
    client.start()

class ClientApplication(object):

    """Class to create an instance of the client applicaiton.
    """

    def __init__(self, name):
        self.name = name
        self.frontend = None
        if os.path.isdir("client_"+name):
            self.path = "client_" + name + "/"
        else:
            os.makedirs("client_"+name)
        self.path = "client_"+name+ "/"

    def send_custom(self, message):

        """Method to allow reliable sending in combination with recv_custom.
        Invokes a custom protocol to ensure message is sent and decipherable.
        """

        # Get size of message in bytes
        length = len(message)
        message_length = str(length)
        print "Sending ", message_length, "bytes."
        # Add the delimiter
        message_length = message_length + "/MSGLEN/"
        # Send length with delimiter
        self.sock.sendall(message_length)
        reply = ""
        # Wait until other side confirms the message length
        while reply != "MSGLEN-OK":
            #print "Sent message length."
            reply = self.sock.recv(46)
            #print reply
            # When message length confirmed, send the data
            if reply == "MSGLEN-OK":
                #print "Message length confirmed. Sending message data."
                self.sock.sendall(message)
                #print "Sent data."

    def recv_custom(self):

        """Method to allow reliable receiving in combination with send_custom.
        Invokes a custom protocol to ensure message is deciphered correctly.
        """

        # Wait for the message length
        message_length = self.sock.recv(1024)
        #print message_length
        if "/MSGLEN/" in message_length:
            message_length = int(message_length[:-8])
            print message_length, "bytes to receive."
            # Make list for chunks of message to accumulate
            chunks = []
            bytes_recd = 0
            #print "Intiating receive."
            self.sock.sendall("MSGLEN-OK")
            while bytes_recd < message_length:
                # Accept a chunk of size 2048 or remaining message length
                chunk = self.sock.recv(2048)
                if chunk == '':
                    raise RuntimeError("socket connection broken")
                # Add current chunk to the accumulator
                chunks.append(chunk)
                #Update how much data has been received
                bytes_recd = bytes_recd + len(chunk)
            mess_recvd =  ''.join(chunks)
            #print "Full message"
            return mess_recvd


    def start(self):

        """Method to provide an entry point to the client application.
        """

        print("Client application started, welcome {0}!".format(self.name))
        self.welcome_state()

    def quit(self):

        """Method to allow the client user to quit the application cleanly.
        """

        quit_prompt = raw_input("Are you sure you want to quit? (y/n) >> ")
        if "y" in quit_prompt.lower():
            sys.exit()
        elif "n" in quit_prompt.lower():
            return
        else:
            print("Input not recognised, please type either y or n.")

    def welcome_state(self):

        """Method to control the welcome state of the client application and
        subsequent control flow.
        """

        while True:
            print("You are not connected to the file system.")
            print("Type CONN to connect to a system or QUIT to exit.")
            prompt = raw_input("Welcome >> ")
            if prompt == "CONN":
                self.frontend = Pyro4.Proxy("PYRONAME:filesystem.frontend")
                print(self.frontend.connect_client(self.name))
                self.command_state()
            elif prompt == "QUIT":
                self.quit()
            else:
                print("Command not recognised.")

    def command_state(self):

        """Method to control the command state of the client application and
        subsequent control flow.
        """

        while True:
            print
            print("Please enter a command for the system to execute.")
            print("For a list of available commands, type HELP.")
            command = raw_input("File System >> ")
            if command == "LIST":
                self.list_files()
            elif command == "DELF":
                self.delete_file()
            elif command == "UPLD":
                self.upload_file()
            elif command == "QUIT":
                self.quit()
            elif command == "DWLD":
                self.download_file()
            elif command == "HELP":
                self.help_guide()
            else:
                print("Command not recognised.")

    def help_guide(self):

        """Method to show the user a help guide whilst in the CLI.
        """

        guide = """
Welcome to the Distributed Systems FTP Utility. This program was made
by Z0954757. This CLI admits the following commands:

HELP - Shows this guide on available commands.
UPLD - Initiates the process to upload a local file to the server.
LIST - Lists the files available in the server directory.
DWLD - Initiates the process to download a file from the server.
DELF - Intiiates the process to delete a file from the server.
QUIT - Closes the connection returns you to the welcome prompt.

This program is made for Section B of the 2017/18 Networks and Systems
module at Durham University.
    """
        print guide

    def list_files(self):

        """Method to list all files currently available on the system.
        """

        print("Retrieving file list from system.")
        file_list = self.frontend.list_all()
        if len(file_list) == 0:
            print("No files found on the file system.")
        else:
            print("The system has the following files:")
            for item in file_list:
                print(item)

    def delete_file(self):

        """Method to delete a user specified file from the system.
        """

        print("Please enter a file name to delete from the system.")
        file_name = raw_input("Delete >> FileSystem/files/")
        print("Calling delete function on the frontend.")
        response = self.frontend.delete_file(file_name)
        print(response)

    def upload_file(self):

        """Method to control the upload of files from the client to the system.
        """

        print("Please enter a file name to upload to the system.")
        file_name = raw_input("Upload >> client_{0}/".format(self.name))
        if os.path.exists(self.path + file_name):
            print("File found on client.")
            print("Would you like to use high or low reliability mode? (type high or low)")
            reliability = raw_input("Reliability >> ")
            if 'high' in reliability.lower():
                # High reliabilty mode
                self.reliable_upload(file_name)
            elif 'low' in reliability.lower():
                #Low
                response = self.frontend.upload_file_low(file_name)
                print("Upload response: {0}".format(response))
                if response == "Server ready.":
                    # Connect over sockets
                    self.connect_server()
                    print("Sending file name to the server.")
                    self.send_custom(file_name)
                    response = self.recv_custom()
                    if response == "Ready.":
                        print("Starting file transfer")
                        f = open(self.path + file_name, 'rb')
                        data = f.read()
                        self.send_custom(data)
                        print("File sent.")
                        f.close()
                        self.sock.close()
                    else:
                        print("Server not ready.")
                else:
                    print(response)
            else:
                print("Reliability choice not recognised, try again.")
        else:
            print("File not found in client directory.")

    def reliable_upload(self, file_name):

        """Method to allow the reliable upload of files from the client to all
        servers on the system.
        """

        no_servers = self.frontend.upload_file_high(file_name, 'start')
        for i in range(0, no_servers):
            response = self.frontend.upload_file_high(file_name, i)
            print("Upload response: {0}".format(response))
            if response == "Server ready.":
                # Connect over sockets
                self.connect_server()
                print("Sending file name to server {0}.".format(i+1))
                self.send_custom(file_name)
                response = self.recv_custom()
                if response == "Ready.":
                    print("Starting file transfer")
                    f = open(self.path + file_name, 'rb')
                    data = f.read()
                    self.send_custom(data)
                    print("File sent.")
                    f.close()
                    status = self.recv_custom()
                    if status == "File sent.":
                        self.sock.close()
                    else:
                        print("File not sent.")
                        break
                else:
                    print("Server not ready.")
                    break
            else:
                print(response)
                break

    def download_file(self):

        """Method to control the download of files from the system to the client.
        """

        print("Please enter a file name to download from the system.")
        file_name = raw_input("Download >> FileSystem/files/")
        if os.path.exists(self.path + file_name):
            print("File found on client, please delete file before downloading.")
        else:
            response = self.frontend.download_file(file_name)
            if response == "Server ready.":
                # Connect over sockets
                self.connect_server()
                self.send_custom(file_name)
                response = self.recv_custom()
                if response == "File doesnt exist.":
                    print "File not found on the server."
                elif response == "File exists, sending file.":
                    print "Downloading file."
                    with open(self.path + file_name, 'w+') as f:
                        #print "File created, file opened"
                        #print "Sending ready to receive."
                        self.send_custom("Ready")
                        data = self.recv_custom()
                        f.write(data)
                        f.close()
                        print "File downloaded successfully."

    def connect_server(self):

        """Method to allow the client to connect to a server by sockets for file
        transfers.
        """

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostname()
        self.port = 3432
        self.sock.connect((self.host, self.port))




if __name__ =="__main__":
    main()
