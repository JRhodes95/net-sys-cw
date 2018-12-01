# Networks and Distributed Systems Summative Assignment

**Auhtor: Z0954757**

## Networks - Socket Programming FTP Client-Server

The submission is written in Python 2, and has been tested in a Python 2.7.12 environment. It has no additional requirements.

It consists of two source files, server.py and client.py. They are stored in separate directories. Within each directory is a folder called files which is used to store the files needed for operation of the file transfer system.

They are command line interface applications which can be started by navigating to the correct diretories and using the commands:
`$ python server.py`
`$ python client.py`

Once the server application is started, it prompts the operator for a port number to run the server on. After a port is successfully specified, no user input is expected. The server can be terminated using the `Ctrl C` command in the terminal window (UNIX).

Once the client application is started, it displays a welcome message with instructions on how to use the CONN command to connect to the server. Once connected successfully, there is an extra HELP command which displays a guide to the CLI in the terminal.
