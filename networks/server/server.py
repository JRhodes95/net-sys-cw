import socket
import threading
import os
import json

"""
Server side application for the 2017/18 Networks and Distributed Systems
Summative Assignment.

Author: Z0954757
"""


def main():

    """Main function to initiate the threaded server on a user specified port.
    """

    print "Welcome to the server!"
    while True:     # Welcome prompt to define port usage.
        print "Please select a port for the server."
        raw_port = raw_input("Server port >>")
        try:
            port = int(raw_port)
            ThreadedServer(port).listen()   # Start a threaded server on port
        except(ValueError):
            print "Please enter valid port number."

class ThreadedServer(object):

    """Class to enable the threaded server once a port has been specified.
    """

    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket.gethostname()
        self.port = port
        self.sock.bind((self.host, self.port))
        self.path = os.path.join('files')  # Sets the path for all files to the directory

    def listen(self):

        """Method to continually listen for incoming connections and create
        new threads for each one.
        """

        self.sock.listen(5)
        print "Listening on port ", self.port
        while True:
            client, address = self.sock.accept()    # Accept connections
            client.settimeout(120)  # Set the inactivity timeout to 2 mins
            threading.Thread(target = self.listenToClient, args = (client,address)).start()

    def listenToClient(self, client, address):

        """Method to listen for client commmands, client should filter the
        sent commands before sending to prevent errors. For each command, this
        method invokes the appropriate handler method.
        """

        print "New connection from ", self.port
        while True:
            print "Waiting for operation from client..."
            # Wait for fixed length operator command 41 bytes long
            command = client.recv(41)
            print "Mode: ", command

            if command == "LIST":
                self.list_files(client)

            elif command == "DELF":
                self.delete_file(client)

            elif command == "UPLD":
                self.receive_file(client)

            elif command == "DWLD":
                self.send_file(client)

            elif command == "QUIT":
                print "Client disconnected."
                print "Server still listening..."
                return False


    def send_custom(self, client, message):

        """Method to allow reliable sending in combination with recv_custom.
        Invokes a custom protocol to ensure message is sent and decipherable.
        """

        message_length = str(len(message))  # Get size of message in bytes
        print "Sending ", message_length, "bytes."
        message_length = message_length + "/MSGLEN/"    # Add the delimiter
        client.sendall(message_length)  # Send length with delimiter
        # Wait until other side confirms the message length
        reply = ""
        while reply != "MSGLEN-OK":
            reply = client.recv(46)
            # When message length confirmed, send the data
            if reply == "MSGLEN-OK":
                client.sendall(message)

    def recv_custom(self, client):

        """Method to allow reliable receiving in combination with send_custom.
        Invokes a custom protocol to ensure message is deciphered correctly.
        """

        # Wait for the message length
        message_length = client.recv(1024)

        if "/MSGLEN/" in message_length:
            message_length = int(message_length[:-8])    # Remove the delimiter
            print message_length, "bytes to receive."
            chunks = [] # Make list for chunks of message to accumulate
            bytes_recd = 0  # Make counter for bytes received
            client.send("MSGLEN-OK")

            while bytes_recd < message_length:
                # Accept a chunk of size 2048 or remaining message length
                chunk = client.recv(2048)
                if chunk == '':
                    raise RuntimeError("socket connection broken")
                chunks.append(chunk)     # Add current chunk to the accumulator
                #Update how much data has been received
                bytes_recd = bytes_recd + len(chunk)

            mess_recvd =  ''.join(chunks)
            return mess_recvd


    def list_files(self, client):

        """Method to send a list of files currently in the server directory to
        the client application.
        """

        print "Listing files."
        files = os.listdir(self.path)
        json_files = json.dumps(files) #Convert to JSON object for transfer
        self.send_custom(client, json_files)

    def delete_file(self, client):

        """Method to delete a specified file from the server directory.
        """

        print "Deleting files."
        file_name = self.recv_custom(client)    # Recv file name from client
        print "File name: ", file_name
        try:
            os.remove(os.path.join(self.path, file_name))    # Remove file
            print "Deleted file ", file_name
            self.send_custom(client, "File deleted.")
        except OSError:
            self.send_custom(client, "File not found on server.")

    def receive_file(self, client):

        """Method to receive an uploaded file from the client.
        """

        print "Receiving files."
        file_name = self.recv_custom(client)    # Recv file name from client

        if os.path.exists(os.path.join(self.path, file_name)):   # Check is file on server
            print "File already exists on server."
            self.send_custom(client, "File exists")
        else:
            with open(os.path.join(self.path, file_name), 'w+') as f:
                self.send_custom(client, "Ready")
                data = self.recv_custom(client)
                f.write(data)   # Write data to file
                f.close()
            print "Received file with ", len(data), "bytes."


    def send_file(self, client):

        """Method to send a file to the client when a download request is sent.
        """

        print "Preparing to send files."
        file_name = self.recv_custom(client)

        # Check if file exists on the server.
        if file_name == "Cancel download":
            print "Download cancelled by client."
            return
        elif os.path.exists(os.path.join(self.path, file_name)):
            print "File exists on server."
            self.send_custom(client, "File exists, sending file.")
            response = self.recv_custom(client)
            if response == "Ready":
                print "Starting file transfer"
                f = open(os.path.join(self.path, file_name), 'rb')
                data = f.read()
                self.send_custom(client, data)  # Send file
                print "finished sending file"
                f.close()
        else:
            print "File doesn't exist, sending error message"






#  Control flow
if __name__ == "__main__":
    main()
