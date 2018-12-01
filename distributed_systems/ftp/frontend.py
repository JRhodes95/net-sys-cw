import os
os.environ["PYRO_LOGFILE"] = "pyro.log"
os.environ["PYRO_LOGLEVEL"] = "DEBUG"

import Pyro4
import Pyro4.util
import Pyro4.naming
import sys
import pprint

"""
Front end controller for the 2017/18 Networks and Distributed Systems
Summative Assignment.

Author: Z0954757
"""

sys.excepthook = Pyro4.util.excepthook
pp = pprint.PrettyPrinter()

def main():

    """Main function to initiate the front end, expose it to the network, and
    find any servers.
    """

    frontend = FrontEnd()
    frontend.find_servers()
    with Pyro4.Daemon() as daemon:
        frontend_uri = daemon.register(frontend)
        with Pyro4.locateNS() as ns:
            ns.register("filesystem.frontend", frontend_uri)
        print("Frontend available.")
        daemon.requestLoop()


@Pyro4.expose
class FrontEnd(object):

    """Class to represent the front end controller. This class accepts
    connections from a client application, decides the appropriate action to
    perform, dispatches commands to the servers on the file system.
    """

    def __init__(self):
        self.active_servers = []

    def find_servers(self):

        """Method to find any servers existing on the network using the Pryo
        Naming Server to lookup servers.
        """

        with Pyro4.locateNS() as ns:
            for server, server_uri in ns.list(prefix="filesystem.fileserver.").items():
                print("Found server at: {0}".format(server))
                self.active_servers.append(Pyro4.Proxy(server_uri))
        if not self.active_servers:
            raise ValueError("No servers found! (Have you started the servers first?)")

    def connect_client(self,client_name):

        """Method called by the client to initiate a connection between the two.
        """

        print("Client {0} connected.".format(client_name))

        return "Hello {0}, you are now connected to the file system.".format(client_name)

    def list_all(self):

        """Method called by the client list all the files on the file system.
        Queries all currently connected servers for files and returns them as a
        single list to the client, removing duplicate instances where a file is
        sotred on multiple servers.
        """

        raw_file_list = []
        for server in self.active_servers:
            server_contents = server.list_contents()
            raw_file_list.append(server_contents)
        flat_file_list = [item for sublist in raw_file_list for item in sublist]
        #remove duplicates
        file_list = list(set(flat_file_list))
        return file_list

    def delete_file(self, file_name):

        """Method called by the client to delete a file stored on the system.
        Queries all currently connected servers and deletes the file if it
        exists there, ensuringthat the file is removed on all servers.
        """

        print("Deleting file: {0}".format(file_name))
        deleted = False
        print("Searching for file on servers...")
        for server in self.active_servers:
            server_contents = server.list_contents()
            if file_name in server_contents:
                print("Found file on server.")
                response = server.delete_file(file_name)
                if response == "File deleted.":
                    deleted = True
                elif response == "File not found on server.":
                    continue
        if deleted == True:
            return "File deleted."
        else:
            return "File not found on file system."

    def upload_file_low(self, file_name):

        """Method called by the client to upload a file in the low reliability
        mode whereby the file is uploaded to the server with the fewest files.
        """

        print("Starting upload sequence.")
        print("Checking if file exists on system.")
        file_list = self.list_all()
        if file_name in file_list:
            return "File already exists on system."
        else:
            print("No matching file on system")
            print("Low reliability upload.")
            print("Looking for least full server.")

            server_least_files = (self.active_servers[0], len(self.active_servers[0].list_contents()))

            for i in range(1, len(self.active_servers)):
                server =  self.active_servers[i]
                server_no_files = len(server.list_contents())
                if server_least_files[1] > server_no_files:
                    server_least_files = (server, server_no_files)

            print("Preparing server for upload process: server_{0}".format(server_least_files[0].get_name()))
            response = server_least_files[0].init_upload(file_name)
            if response == "Failed to initate server, see server log for details.":
                print(response)
                return response
            else:
                print(response)
                return response

    def upload_file_high(self, file_name, status):

        """Method called by the client to upload a file in high reliability
        mode whereby the file is uploaded to all servers attached to the system.
        """

        if status == 'start':
            print("High reliability upload process started.")
            no_servers = len(self.active_servers)
            return no_servers
        else:
            response = self.active_servers[status].init_upload_high(file_name)
            return response

    def download_file(self, file_name):

        """Method called by the client to download a file from the system.
        Searches the active servers and initiates the download from the first
        it finds containing the specified file.
        """

        print("Starting download process.")
        print("Checking if file exists on system.")
        file_list = self.list_all()
        if file_name not in file_list:
            return "File not on system. Use LIST to check available files."
        else:
            print("Looking for server containing file.")
            for server in self.active_servers:
                if file_name in server.list_contents():
                    print("Found file, readying server.")
                    response = server.init_download()
                    return response



if __name__ == "__main__":
    main()
