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
        CLOSED = 1
        LISTENING = 2
        ESTABLISHED = 3
        INIT_RCVD = 4
        INIT_SENT = 5
        CNCT_SENT = 6


    # Initliazation of class vars. Local to current instantiated class.
    def __init__(self, srcPort):
        self.state = ConnectionStates.CLOSED
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rcvWindowSize = RxPacket.MAX_WINDOW_SIZE  # Receive Window size in bytes
        self.sendWindowSize = 1 # Send window size in bytes
        self.buffer = None      # Actual memory space for the buffer
        self.srcPort = srcPort     # Local RxP port, not UDP port
        self.desPort = None     # Destination RxP Port, not UDP port
        self.desAddr = None
        self.srcAddr = "127.0.0.1"
        self.timeout = None
        self.resetLimit = 50

        # Note on Sequence and Acknoledgment numbers: The sequence number should
        #  increase every time you SEND data, by the number of bytes. This should be
        #  the entire packet size, not just the data size. The acknowldgement number
        #  should increase every time we RECEIVED data, by the number of bytes. This
        #  should also be the entire packet size, for continuity.

        self.seqNum = 0
        self.ackNum = 0

        

    def gettimeout(self):
        return self.socket.gettimeout()

    def settimeout(self, val):
        return self.socket.settimeout()

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

        # Loop for listening for conneciton attemps.
        while True:
            # Blocks until we have a connecton attempt
            self.socket.settimeout(None)
            self.state = ConnectionState.LISTENING
            UDPpacket, addr = byteArray(self.socket.recvfrom(1024))
            theRxPacket = rxpacket(UDPpacket)
            packetType = None;

            # Do nothing / throw out if invalid packet
            if not theRxPacket.isValid():
                temp = 1
            # Handle the packet if valid.
            elif theRxPacket.isValid():
                # Figure out what kind of packet it is, and pass to appropriate handler.

                # We have an INIT packet
                if theRxPacket.isINIT and self.state == ConnectionStates.LISTENING:
                    # Set src info
                    self.destAddr = addr    # IP adress
                    self.destPort = theRxPacket.srcPort
                    self.state = ConnectionStates.INIT_RCVD

                    # Send ACK
                    ack = rxpacket(None, self.srcPort, self.destPort, self.seqNum, self.ackNum)


                # We have a CNCT packet
                elif theRxPacket.isCNCT and self.state == ConnectionStates.INIT_RCVD:
                    temp = 1
                else:
                    temp = 1




            # Once we get a connection attempt, we can use timeouts to ensure that
            #  lost packets don't cause us to timeout forever.
            self.socket.settimeout(5)




    # Connects to the specified host on the specified port.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is estabilshed, sets up memory and window.
    def connect(self, ip, port):
        if port == None:
            raise Exception("The port has not been set. You cannot connect.")
            sys.exit(1)

        self.destAddr = ip
        self.destDestPort = port

        # Create an Init packet and send it off to the host we wish to connect to.
        ack1 = self.__sendInit()
        self.state = ConnectionStates.INIT_SENT
        self.ackNum = ack1.header['seqNum'] + 1
        
        # Create a Cnct packet and send it off to the other host
        ack2 = self.__sendCnct()
        self.ackNum = ack2.header['seqNum'] + 1
        
    def __sendInit(self):
    
        #create packet
        flags = (True, False, False, False)
        initPacket = RxPacket.getInit(
                    srcPort = self.srcPort,
                    desPort = self.desPort,
                    seqNum = self.seqNum,
                    winSize = self.recvWindow,
                    )
        
        #increment seq num
        self.seqNum = self.seqNum + 20 #increment by number of bytes (20 byte header only)
        if self.seqNum > RxPacket.MAX_SEQUENCE_NUM:
            self.seqNum = 0
        
        #transfer packet
        resetsRemaining = self.resetLimit
        while resetsRemaining:
            self.send(initPacket)
            
            try:
                data = self.recv()
                packet = self.__reconstructPacket(data)
                if not ack:
                    resetsRemaining -= 1
                    continue
            except socket.timeout:
                resendsRemaining -= 1
            else: 
                if packet.isAck() and packet.header['ackNum'] == self.seqNum + 1:
                    break
                    
        if not resetsRemaining:
            raise Exception('socket timeout')
            
        return packet
        
    def __reconstructPacket(data):
        packet = RxPacket.
                
        
        
        
        
        
        
        
        
