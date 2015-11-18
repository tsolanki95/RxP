import socket
import rxpacket
from enum import Enum

class RxPSocket:

    # Class-wide list of current RxP ports in use.
    portsInUse = []

    # Class-wide port to use when sending UDP messages.
    UDPport = 65

    # Enum to store possible connection states.
    # Global.
    class ConnectionStates(Enum):
        notConnected = 1
        listening = 2
        connected = 3

    # Initliazation of class vars. Local to current instantiated class.
    def __init__(self):
        self.state = ConnectionStates.notConnected
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.windowSize = None  # Window size in bytes
        self.buffer = None      # Actual memory space for the buffer
        self.LocPort = None     # Local RxP port, not UDP port
        self.DestPort = None     # Destination RxP Port, not UDP port
        self.destAddr = None
        self.srcAddr = "127.0.0.1"
        self.timeout = None

        # Note on Sequence and Acknoledgment numbers: The sequence number should
        #  increase every time you SEND data, by the number of bytes. This should be
        #  the entire packet size, not just the data size. The acknowldgement number
        #  should increase every time we RECEIVED data, by the number of bytes. This
        #  should also be the entire packet size, for continuity.

        self.seqNum = 0
        self.ackNum = 0

    # Bind the socket to a specific local RxP port.
    # Set the object's port var.
    def bind(self, aPort):
        # Check and make sure the supplied port isn't in use!
        if aPort in portsInUse:
            raise Exception("The port, " + aPort + " is already in use!")
            sys.exit(1)
        try:
            self.socket.bind(srcAddr,aPort)
            self.port = aPort
            portsInUse.append(port)
        except:
            print("The socket could not be bound to " + aPort + ".")

    # Listen for incoming connectins, and accepts them.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is established, sets up memory and window.
    def listen(self):
         if port == None:
             raise Exception("The port has not been set. You cannot listen.")
             sys.exit(1)


    # Connects to the specified host on the specified port.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is estabilshed, sets up memory and window.
    def connect(self, ip, port):
        if port == None:
            raise Exception("The port has not been set. You cannot connect.")
            sys.exit(1)

        self.destAddr = ip
        self.destDestPort = port

        # Create an init packet and send it off to the host we wish to connect to.
        rxpacket.getInit(locPort, destPort, seqNum, ackNum)
        
