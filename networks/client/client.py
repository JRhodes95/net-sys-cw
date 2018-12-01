#Import nessecary modules
import socket
import sys
import os
import json

"""
Client side application for the 2017/18 Networks and Distributed Systems
Summative Assignment.

Author: Z0954757
"""


def main():

    """Main function to initiate client application launch.
    """

    print "Welcome to the client!"
    while True: # Welcome prompt to initiate connection.
        print """
You are not connected to a server. Type CONN to initiate a connection, or
QUIT to exit this client.
        """
        init_input = raw_input("Welcome >>")
        if init_input == "CONN":
            connect_to_server()
        elif init_input == "QUIT":
            quit_client()
        else:
            print "Input not recognised, please try again."

def connect_to_server():

    """Function to connect to a server on user specified port.
    """

    print """
What port would you like to use?
    """
    port = int(raw_input("Client port >>"))
    try:
        ClientApplication(port).connect()     # Start an instance of the client
    except(socket.error):
        print "Connection refused, please try again."

def quit_client():

    """Function to correctly quit the client.
    """

    sys.exit()

class ClientApplication(object):

    """Class to create an instance of the client applicaiton.
    """

    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket.gethostname()
        self.port = port
        self.path = os.path.join('files')

    def connect(self):

        """Method to connect to a server. Entry point for the application.
        """

        self.sock.connect((self.host, self.port))
        self.application_prompt()   # Enter the command state of the client.

    def send_custom(self, message):

        """Method to allow reliable sending in combination with recv_custom.
        Invokes a custom protocol to ensure message is sent and decipherable.
        """

        length = len(message)   # Get size of message in bytes
        message_length = str(length)    # Stringify to send
        print "Sending ", message_length, "bytes."
        message_length = message_length + "/MSGLEN/"    # Add the delimiter
        self.sock.sendall(message_length)   # Send length with delimiter

        # Wait until other side confirms the message length
        reply = ""
        while reply != "MSGLEN-OK":
            reply = self.sock.recv(46)

            # When message length confirmed, send the data
            if reply == "MSGLEN-OK":
                self.sock.sendall(message)

    def recv_custom(self):

        """Method to allow reliable receiving in combination with send_custom.
        Invokes a custom protocol to ensure message is deciphered correctly.
        """

        message_length = self.sock.recv(1024)   # Wait for the message length

        if "/MSGLEN/" in message_length:
            message_length = int(message_length[:-8])
            print message_length, "bytes to receive."

            chunks = [] # Make list for chunks of message to accumulate
            bytes_recd = 0  # Keep track of how much data has been received
            self.sock.sendall("MSGLEN-OK")  # Confirm message length recvd

            while bytes_recd < message_length:
                chunk = self.sock.recv(2048)  # Accept data in 2048 byte chunk
                if chunk == '': # Check for dead socket
                    raise RuntimeError("socket connection broken")
                chunks.append(chunk)    # Add current chunk to the accumulator
                bytes_recd = bytes_recd + len(chunk) # Update data received

            mess_recvd =  ''.join(chunks)   # Join the chunks for full message
            return mess_recvd

    def application_prompt(self):

        """Method to control the command state of the client application and
        subsequent control flow.
        """

        print "Connection successful!"
        prompt = "To server >> "
        while True:  # While loop to control the CLI.
            print "Message to send to the server (for info on this CLI type HELP):"
            message = raw_input(prompt)

            if message == "QUIT":
                # Close the connection to the server
                print "Closing connection to server."
                self.sock.sendall("QUIT")
                self.sock.close()
                print "Connection successfully closed."
                # Return to the welcome prompt by breaking the while loop.
                break

            elif message == "HELP":
                self.help_guide()

            elif message == "LIST":
                self.list_request()

            elif message == "DELF":
                self.file_delete()

            elif message == "UPLD":
                self.file_upload()

            elif message == "DWLD":
                self.file_download()

            else:
                print message, "is not a defined command."
                print "For a list of defined commands type HELP."


    def help_guide(self):

        """Method to show the user a help guide whilst in the CLI.
        """

        guide = """
Welcome to the Networks FTP Utility. This program was made
by Z0954757. This CLI admits the following commands:

HELP - Shows this guide on available commands.
UPLD - Initiates the process to upload a local file to the server.
LIST - Lists the files available in the server directory.
DWLD - Initiates the process to download a file from the server.
DELF - Intiiates the process to delete a file from the server.
QUIT - Closes the connection returns you to the welcome prompt.

This program is made for Section A of the 2017/18 Networks and Systems
module at Durham University.
    """
        print guide


    def list_request(self):

        """Method to list all files currently available on the server.
        """

        self.sock.sendall("LIST")   # Send LIST command
        data = self.recv_custom()   # Receive listed data
        data = json.loads(data)     # Convert from JSON to List
        print "Files on server: "   # Print list nicely
        for entry in data:
            print entry

    def file_delete(self):

        """Method to delete a user specified file from the server.
        """

        self.sock.sendall("DELF")   # Send DELF command
        file_name = raw_input("File to be deleted >> Server:files/")
        self.send_custom(file_name) # Send file name to be deleted
        response = self.recv_custom()
        if response == "File deleted.":
            print "File successfully deleted"
        elif response == "File not found on server.":
            print response
        else:
            print "Delete failed for unknown reason, please try again."

    def file_upload(self):

        """Method to control the upload of files from the client to the server.
        """

        self.sock.sendall("UPLD")   # Send UPLD command
        file_name = raw_input("File to be sent >> Client:files/")
        self.send_custom(file_name)
        response = self.recv_custom()
        if response == "File exists":
            print "File exists on the server. Use DELF to delete file to upload new."
        elif response == "Ready":
            print "Starting file transfer"
            f = open(os.path.join(self.path, file_name), 'rb')
            data = f.read()
            self.send_custom(data)
            print "File sent."
            f.close()


    def file_download(self):

        """Method to control the download of files from the server to the client.
        """

        self.sock.sendall("DWLD")
        # Start prompt to enter file_name
        file_name = raw_input("File to be sent >> Client:files/")
        # Check that file with that name isn't on Client
        if os.path.exists(os.path.join(self.path, file_name)):
            print "File with that name already exists in client directory."
            print "Cancelling download"
            self.send_custom("Cancel download")
        else:
            self.send_custom(file_name)
            response = self.recv_custom()
            if response == "File doesnt exist.":
                print "File not found on the server."
            elif response == "File exists, sending file.":
                print "Downloading file."
                with open(os.path.join(self.path, file_name), 'w+') as f:
                    self.send_custom("Ready")
                    data = self.recv_custom()
                    f.write(data)
                    f.close()
                    print "File downloaded successfully."

#  Control flow
if __name__ == "__main__":
    main()
