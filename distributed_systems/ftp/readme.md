# Networks and Distributed Systems Summative Assignment

**Auhtor: Z0954757**

## Distributed Systems - Distributed File System

The submission is written in Python 2, and has been tested in a Python 2.7.12 environment. It requires pyro4 to be installed in the environment

It consists of three python files:
* client.py - the client side application
* frontend.py - the frontend application which acts as a controller,
* server.py - the server application.

To start the system perform the following:
1) In one terminal, start the pyro naming server with `$ pyro4-ns`.
2) In a second terminal, start the servers with `$ python server.py`.
3) In a third terminal, start the frontend with `$ python frontend.py`.
4) In a fourth terminal, start the client application with `python client.py`.

When the client applciation is started, it will promt the user for thier name and create a folder in the directory for their files of the form `/client_[NAME]/`. If a directory already exists it sets this as the active directory
