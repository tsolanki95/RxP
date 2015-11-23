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
            raise Exception("Socket not bound")
            sys.exit(1)

        self.state = ConnectionStates.LISTENING
        
        waitLimit = self.resetLimit * 100
        while waitLimit:
            
            #receive INIT
            try:
                bytes, addr = socket.recvfrom(self.rcvWindowSize)
                packet = self.__reconstructPacket(data = bytearray(bytes), checkSeqNum = False)
                
                if packet is None:
                    waitLimit -= 1
                    continue
                
            except socket.timeout:
                waitLimit -= 1
                continue
                
            else:
                if (packet.isInit()):
                    break
                else:
                    waitLimit -= 1
                    
                
        if not waitLimit:
            raise Exception('socket timeout')
            
        self.ackNum = packet.header['seqNum'] + 1
        
        waitLimit = self.resetLimit * 100
        while waitLimit:
        
            try:
                
            
        




    # Connects to the specified host on the specified port.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is estabilshed, sets up memory and window.
    def connect(self, ip, port):
        if port == None:
            raise Exception("Socket not bound")
            sys.exit(1)

        self.destAddr = ip
        self.destDestPort = port
        
        try:
            # Create an Init packet and send it off to the host we wish to connect to.
            ack1 = self.__sendInit()
            
            # Create a Cnct packet and send it off to the other host
            ack2 = self.__sendCnct()
        except Exception:
            return False
        else:
            self.state = ConnectionStates.ESTABLISHED
            return True
            
        
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
        self.seqNum = self.seqNum + 1 #increment by number of bytes (20 byte header only)
        if self.seqNum > RxPacket.MAX_SEQUENCE_NUM:
            self.seqNum = 0
        
        #transfer packet
        resetsRemaining = self.resetLimit
        while resetsRemaining:
            self.sendto(initPacket.toByteArray())
            
            try:
                data, addr = bytearray(socket.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data), checkSeqNum = False)
                if not ack:
                    resetsRemaining -= 1
                    continue
            except socket.timeout:
                resetsRemaining -= 1
            else: 
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    break
                else:
                    resetsRemaining -= 1
                    
        if not resetsRemaining:
            raise Exception('socket timeout')
            
        return packet
        
    def __sendCnct(self):
    
        #create packet
        flags = (False, True, False, False)
        cnctPacket = RxPacket.getCnct(
                    srcPort = self.srcPort,
                    desPort = self.desPort,
                    seqNum = self.seqNum,
                    winSize = self.recvWindow,
                    )
        
        #increment seq num
        self.seqNum = self.seqNum + 1 #increment by number of bytes (20 byte header only)
        if self.seqNum > RxPacket.MAX_SEQUENCE_NUM:
            self.seqNum = 0
        
        #transfer packet
        resetsRemaining = self.resetLimit
        while resetsRemaining:
            self.sendto(cnctPacket.toByteArray(), self.desAddr)
            
            try:
                data, addr = socket.recvfrom(self.rcvWindowSize)
                packet = self.__reconstructPacket(data = bytearray(data), checkSeqNum = False)
                if not ack:
                    resetsRemaining -= 1
                    continue
            except socket.timeout:
                resetsRemaining -= 1
            else: 
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    break
                else:
                    resetsRemaining -= 1
                    
        if not resetsRemaining:
            raise Exception('socket timeout')
            
        return packet
        
        
    def __reconstructPacket(self, data, checkSeqNum = True, checkAckNum = False):
        packet = RxPocket.fromByteArray(data)
        
        if not packet.isValid():
            return None
        
        return packet
