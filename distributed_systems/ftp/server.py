import os
os.environ["PYRO_LOGFILE"] = "pyro.log"
os.environ["PYRO_LOGLEVEL"] = "DEBUG"

import socket
import Pyro4
import threading

"""
Server side application for the 2017/18 Networks and Distributed Systems
Summative Assignment.

Author: Z0954757
"""


def main():

    """Main function to start three servers on the system.
    """

    #server_name = input("Server name >>").strip
    server_1 = FileServer("1")
    server_2 = FileServer("2")
    server_3 = FileServer("3")
    with Pyro4.Daemon() as daemon:
        server_1_uri = daemon.register(server_1)
        server_2_uri = daemon.register(server_2)
        server_3_uri = daemon.register(server_3)
        with Pyro4.locateNS() as ns:
            ns.register("filesystem.fileserver.server_1", server_1_uri)
            ns.register("filesystem.fileserver.server_2", server_2_uri)
            ns.register("filesystem.fileserver.server_3", server_3_uri)
        print("Three servers available.")
        daemon.requestLoop()


@Pyro4.expose
class FileServer(object):

    """Class representing a file server on the system.
    """

    def __init__(self, name):
        self.name = name
        if os.path.isdir("server_"+name):
            self.path = "server_" + name + "/"
        else:
            os.makedirs("server_"+name)
        self.path = "server_"+name+"/"

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



    def get_name(self):

        """Method to allow the frontend access to the server's name.
        """

        return self.name

    def list_contents(self):

        """Method to send a list of files currently in the server directory to
        the client application.
        """

        files = os.listdir(self.path)
        return files

    def delete_file(self, file_name):

        """Method to delete a specified file from the server directory.
        """

        try:
            os.remove(self.path + file_name)
            print("{0} deleted file {1}".format(self.name, file_name))
            return "File deleted."
        except OSError:
            return "File not found on server."

    def init_upload(self, file_name):

        """Method to initiate receiving an uploaded file from the client.
        Low reliabilty mode only uploading to this server.
        """

        print("Starting add file process.")
        self.listen_to_client() # Start socket server
        threading.Thread(target = self.client_upload).start()
        print("Thread dispatched to handle upload.")
        return "Server ready."

    def init_upload_high(self, file_name):

        """Method to initiate receiving an uploaded file from the client.
        High reliabilty mode uploading to all servers.
        """

        print("Starting add file process.")
        self.listen_to_client() # Start socket server
        threading.Thread(target = self.client_upload_high).start()
        print("Thread dispatched to handle upload.")
        return "Server ready."


    def client_upload(self):

        """Method to receive an uploaded file from the client.
        Low reliabilty mode only uploading to this server.
        """

        client, address = self.sock.accept()
        client.settimeout(120)  # Set the inactivity timeout to 2 mins

        file_name = self.recv_custom(client)

        with open(self.path + file_name, 'w+') as f:
            print("File {0} created, file opened".format(file_name))
            print("Sending ready to receive.")
            self.send_custom(client, "Ready.")
            data = self.recv_custom(client)
            f.write(data)
            f.close()
        print("Received file. Size: {0} bytes.".format(len(data)))
        self.sock.close()

    def client_upload_high(self):

        """Method to receive an uploaded file from the client.
        High reliabilty mode uploading to all servers.
        """

        client, address = self.sock.accept()
        client.settimeout(120)  # Set the inactivity timeout to 2 mins

        file_name = self.recv_custom(client)

        with open(self.path + file_name, 'w+') as f:
            print("File {0} created, file opened".format(file_name))
            print("Sending ready to receive.")
            self.send_custom(client, "Ready.")
            data = self.recv_custom(client)
            f.write(data)
            f.close()
        print("Received file. Size: {0} bytes.".format(len(data)))
        self.send_custom(client, "File sent.")
        print("Sent received message.")
        self.sock.close()


    def init_download(self):

        """Method to initiate downloading a file to the client.
        """

        print("Starting take file process.")
        # Start socket server
        self.listen_to_client()
        threading.Thread(target = self.client_download).start()
        print("Thread dispatched to handle download.")
        return "Server ready."

    def client_download(self):

        """Method to download a file to the client via sockets.
        """

        client, address = self.sock.accept()
        client.settimeout(120)  # Set the inactivity timeout to 2 mins

        print "Preparing to send files."
        file_name = self.recv_custom(client)
        # Check if file exist on the server already.
        if file_name == "Cancel download":
            print "Download cancelled by client."
            return
        elif os.path.exists(self.path + file_name):
            print "File exists on server."
            # Send file
            self.send_custom(client, "File exists, sending file.")
            response = self.recv_custom(client)
            if response == "Ready":
                print "Starting file transfer"
                f = open(self.path + file_name, 'rb')
                data = f.read()
                self.send_custom(client, data)
                print "File transfer finished."
                f.close()
        else:
            print "File doesn't exist, sending error message"

    def listen_to_client(self):

        """Method to start server listening for incoming client connects on a
        socket. Specified as port 3432.
        """

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostname()
        self.port = 3432
        self.sock.bind((self.host, self.port))
        print("Starting server on port {0}".format(self.port))
        self.sock.listen(5)
        print("Listening on port {0}".format(self.port))


if __name__ == "__main__":
    main()
