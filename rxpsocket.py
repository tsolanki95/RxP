import socket
from enum import Enum

class RxPSocket:


    # Enum to store possible connection states.
    # Global.
    class ConnectionStates(Enum):
        notConnected = 1
        connected = 2

    #Initliazation of class vars.
    __init__(self)
        self.state = ConnectionStates.notConnected
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = None
        self.timeout = None
        self.destAddr = None
        self.srcAddr = None
        self.
