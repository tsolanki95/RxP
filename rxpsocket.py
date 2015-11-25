import socket
import rxpacket

class RxPSocket:

    def log(self, message):
        if DEBUG:
            print message

    # Class-wide port to use for NetEmu
    NetEmuPort = 5000

    # Enum to store possible connection states.
    # Global.
    class ConnectionStates():
        CLOSED = 1
        ESTABLISHED = 2


    # Initliazation of class vars. Local to current instantiated class.
    def __init__(self, srcPort, debug = True):
        self.state = ConnectionStates.CLOSED
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rcvWindowSize = RxPacket.MAX_WINDOW_SIZE  # Receive Window size in bytes
        self.sendWindowSize = 1 # Send window size in bytes
        self.buffer = None      # Actual memory space for the buffer
        self.srcPort = srcPort     # Local RxP port, not UDP port
        self.desPort = None     # Destination RxP Port, not UDP port
        self.desAddr = None
        self.bindPort = None
        self.srcAddr = "127.0.0.1"
        self.timeout = None
        self.resetLimit = 50
        self.finalCnctAckNum = 2
        self.debug = debug

        # Note on Sequence and Acknoledgment numbers: The sequence number should
        #  increase every time you SEND data, by the number of bytes. This should be
        #  the entire packet size, not just the data size. The acknowldgement number
        #  should increase every time we RECEIVED data, by the number of bytes. This
        #  should also be the entire packet size, for continuity.

        self.seqNum = 0
        self.ackNum = 0

    def log(self, message):
        if self.debug:
            print message
        
    def gettimeout(self):
        return self.socket.gettimeout()

    def settimeout(self, val):
        return self.socket.settimeout()

    # Bind the socket to a specific local RxP port.
    # Set the object's port var.
    def bind(self, aPort):
        try:
            if aPort:
                self.socket.bind((self.srcAddr,self.aPort))
                self.bindPort = aPort
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
                bytes, address = self.recvfrom(self.rcvWindowSize)
                packet = self.__reconstructPacket(data = bytearray(bytes))
                
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
        self.desAddr = addr[0]
        self.desPort = addr[1]
        
        #Send Ack 1
        waitLimit = self.resetLimit * 100
        while waitLimit:
        
            try:
                #create packet
                flags = (False, False, True, False, False, False)
                initPacket = RxPacket(
                            srcPort = self.srcPort,
                            desPort = self.desPort,
                            seqNum = self.seqNum,
                            ackNum = self.ackNum,
                            flagList = flags,
                            winSize = self.recvWindow,
                            )
                self.sendto(initPacket.toByteArray(), (self.desAddr, self.desPort))
                    
                
                data, address = bytearray(self.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data))
                if not packet:
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else: 
                if packet.isCnct():
                    break
                else:
                    resetsLeft -= 1
                    
        if not waitLimit:
            raise Exception('socket timeout')
            
        self.ackNum = packet.header['seqNum'] + 1
        self.finalCnctAckNum = self.ackNum
        
        #send the second ACK
        flags = (False, False, True, False, False, False)
        initPacket = RxPacket(
                    srcPort = self.srcPort,
                    desPort = self.desPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = flags,
                    winSize = self.recvWindow,
                    )
        self.sendto(initPacket.toByteArray(), (self.desAddr, self.desPort))
        
        self.state = ConnectionStates.ESTABLISHED
        
        
    # Connects to the specified host on the specified port.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is estabilshed, sets up memory and window.
    def connect(self, (ip, port)):
        if port == None:
            raise Exception("Socket not bound")
            sys.exit(1)

        self.desAddr = ip
        self.desPort = port
        
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
            
            
            
    def send(self, msg):
        if self.srcPort is None:
            raise Exception("Socket not bound")
            
        if self.state != ConnectionStates.ESTABLISHED:
            raise Exception("Connection not established")
            
        dataQueue = deque()
        packetQueue = deque()
        sentQueue = deque()
        lastSeqNum = self.seqNum
            
        #fragment data and add it to data queue
        for i in range(stop = len(msg), step = RxPacket.DATA_LEN):
            if (i + RxPacket.DATA_LEN > len(msg)):
                dataQueue.append(bytearray(msg[i : ]))
            else:
                dataQueue.append(bytearray(msg[i : i + RxPacket.DATA_LEN]))
                
        #construct packet queue from data queue
        for data in dataQueue:
            if data == dataQueue[0]:
                flags = (False, False, False, False, True, False)
            if data == dataQueue[-1]:
                flags = (False, False, False, False, False, True)
            else:
                flags = (False, False, False, False, False, False)
                
            packet = RxPacket(
                    srcPort = self.srcPort,
                    desPort = self.desPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = flags,
                    winSize = self.recvWindow,
                    data = data
                    )
                    
            self.seqNum += 1
            if self.seqNum >= RxPacket.MAX_SEQUENCE_NUM:
                self.seqNum = 0
                
            packetQueue.append(packet)
            
        resetsLeft = self.resetLimit
        while packetQueue and resetsLeft:
            #send packets in send window
            window = self.sendWindowSize
            while window and packetQueue:
                packetToSend = packetQueue.popLeft()
                self.sendto(packet.toByteArray(), (self.desAddr, self.desPort))
                lastSeqNum = packet.header['seqNum']
                
                window -= 1
                sentQueue.append(packet)
                
            try:
                data, address = self.recvfrom(self.recvWindowSize)
                handShakeFinishedCheck = self.__reconstructPacket(bytearray(data))
                packet = self.__reconstructPacket(data = bytearray(data),  checkAckNum = lastSeqNum)
                
                if not packet:
                    sentQueue.reverse()
                    packetQueue.extendleft(sentQueue)
                    sentQueue.clear()
                    resetsLeft -= 1
                    continue
                
            except socket.timeout:
                window = 1
                resetsLeft -= 1
                sentQueue.reverse()
                packetQueue.extendleft(sentQueue)
                sentQueue.clear()
                
            else:
                window += 1
                if (isinstance(packet, int)):
                    while packet < 0:
                        packetQueue.appendleft(sentQueue.pop())
                        packet += 1
                elif handShakeFinishedCheck.isAck() and handShakeFinishedCheck.header['ackNum'] == self.finalCnctAckNum:
                    
                    flags = (False, False, True, False, False, False)
                    ackPacket = RxPacket(
                                srcPort = self.srcPort,
                                desPort = self.desPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = flags,
                                winSize = self.recvWindow,
                                )
                    self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desPort))
                    
                    resetsLeft = self.resetLimit

                    sentQueue.reverse()
                    packetQueue.extendleft(sentQueue)
                    sentQueue.clear()
                elif packet.isAck():
                    self.seqNum = packet.header['ackNum']
                    resetsLeft = self.resetLimit
                    sentQueue.clear()
                    
        if not resetsLeft:
            raise Exception('socket timeout')
            
    def recv(self):
        if self.srcPort is None:
            self.log("Socket already closed")
        
        if self.state != ConnectionStates.ESTABLISHED:
            self.log("Socket already closed")
            
        message = bytes()
            
        resetsLeft = self.resetLimit
        while resetsLeft:
            try:
                data, address = self.recvfrom(self.recvWindowSize)
                
            except socket.timeout:
                resetsLeft -= 1
                continue
                
            packet = self.__reconstructPacket(bytearray(data))
            
            if not packet:
                resetsLeft -= 1
                continue
                
            else:
                self.ackNum = packet.header['seqNum'] + 1
                if self.ackNum > RxPacket.MAX_ACK_NUM:
                    self.ackNum = 0
                message += packet.data
                
                flags = (False, False, True, False, False, False)
                ackPacket = RxPacket(
                            srcPort = self.srcPort,
                            desPort = self.desPort,
                            seqNum = self.seqNum,
                            ackNum = self.ackNum,
                            flagList = flags,
                            winSize = self.recvWindow,
                            )
                self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desPort))
                
                if (packet.isEndOfMessage()):
                    break
                    
                if (packet.isFin()):
                    flags = (False, False, True, False, False, False)
                    ackPacket = RxPacket(
                                srcPort = self.srcPort,
                                desPort = self.desPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = flags,
                                winSize = self.recvWindow,
                                )
                    self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desPort))
                    self.__closePassive(ackPacket)
                    break
                
                return message
                
        
        if not resetsLeft:
            raise Exception('socket timeout')
        
        
        return message
        
    def sendto(self, data, address):
        self.socket.sendto(data, address)
        
    def recvfrom(self, recvWindow):
        while True:
            try:
                packet = self.socket.recvfrom(recvWindow)
            except socket.error as error:
                if error.errno is 35:
                    continue
                else:
                    raise e
        
        return packet
        
    def close(self):
        if self.srcPort is None:
            self.socket.close()
            raise RxPException("Socket not bound")
            
        
        if self.state != ConnectionStates.ESTABLISHED:
            self.socket.close()
            raise Exception("Connection not established")
            
        fin_flags = (False, False, False, True, False, False)
        finPacket = RxPacket(
                    srcPort = self.srcPort,
                    desPort = self.desPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = fin_flags,
                    winSize = self.recvWindow,
                    )
        
        self.seqNum += 1
        if self.seqNum > RxPacket.MAX_SEQUENCE_NUM:
            self.seqNum = 0
            
        resetsLeft = self.resetLimit()
        
        waitingForHostB = True
        isFinAcked = False
        
        while resetsLeft and (not isFinAcked or waitingForHostB):
            self.sendto(finPacket.toByteArray(), (self.desAddr, self.desPort))
            
            try:
                data, address = self.recvfrom(self.recvWindow)
                packet = self.__reconstructPacket(data)
                
                if not packet:
                    resetsLeft -= 1
            except socket.timeout:
                resetsLeft -= 1
                continue
            else:
                if (packet.isAck() and packet.header['ackNum'] == self.seqNum):
                    isFinAcked = True
                    
                if (packet.isFin()):
                    ack_flags = (False, False, False, True, False, False)
                    finPacket = RxPacket(
                                srcPort = self.srcPort,
                                desPort = self.desPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = fin_flags,
                                winSize = self.recvWindow,
                                )
                                
                    self.sendto(finPacket.toByteArray(), (self.desAddr, self.desPort))
                    waitingForHostB = False
            
        self.socket.close()
        self = RxSocket(self.srcPort, self.debug)
            
    def __closePassive(self, ackPacket):
        if self.srcPort is None:
            self.socket.close()
            raise RxPException("Socket not bound")
            
        
        if self.state != ConnectionStates.ESTABLISHED:
            self.socket.close()
            raise Exception("Connection not established")
            
        fin_flags = (False, False, False, True, False, False)
        finPacket = RxPacket(
                    srcPort = self.srcPort,
                    desPort = self.desPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = fin_flags,
                    winSize = self.recvWindow,
                    )
        
        self.seqNum += 1
        if self.seqNum > RxPacket.MAX_SEQUENCE_NUM:
            self.seqNum = 0
            
        resetsLeft = self.resetLimit()
        
        isFinAcked = False
        
        while resetsLeft and (not isFinAcked):
            self.sendto(finPacket.toByteArray(), (self.desAddr, self.desPort))
            
            try:
                data, address = self.recvfrom(self.recvWindow)
                packet = self.__reconstructPacket(data)
                
                if not packet:
                    resetsLeft -= 1
            except socket.timeout:
                resetsLeft -= 1
                continue
            else:
                if (packet.isAck() and packet.header['ackNum'] == self.seqNum):
                    isFinAcked = True
                    
                if (packet.isFin()):
                    ack_flags = (False, False, False, True, False, False)
                    finPacket = RxPacket(
                                srcPort = self.srcPort,
                                desPort = self.desPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = fin_flags,
                                winSize = self.recvWindow,
                                )
                                
                    self.sendto(finPacket.toByteArray(), (self.desAddr, self.desPort))
        
        self.socket.close()
        self = RxSocket(self.srcPort, self.debug)
        
        
    def __sendInit(self):
    
        #create packet
        flags = (True, False, False, False, False, False)
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
        resetsLeft = self.resetLimit
        while resetsLeft:
            self.sendto(initPacket.toByteArray(), (self.desAddr, self.desPort))
            
            try:
                data, address = bytearray(self.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data))
                
                if not packet:
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else: 
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    break
                else:
                    resetsLeft -= 1
                    
        if not resetsLeft:
            raise Exception('socket timeout')
            
        return packet
        
    def __sendCnct(self):
    
        #create packet
        flags = (False, True, False, False, False, False)
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
        resetsLeft = self.resetLimit
        while resetsLeft:
            self.sendto(initPacket.toByteArray(), (self.desAddr, self.desPort))
            
            try:
                data, address = self.recvfrom(self.rcvWindowSize)
                packet = self.__reconstructPacket(data = bytearray(data))
                if not packet:
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else: 
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    break
                else:
                    resetsLeft -= 1
                    
        if not resetsLeft:
            raise Exception('socket timeout')
            
        return packet
        
        
    def __reconstructPacket(self, data, checkAckNum = False):
        packet = RxPocket.fromByteArray(data)
        
        if not packet.isValid():
            return None
        
        if checkAckNum:
			
			packetAckNum = packet.header['ackNum']

			ackMismatch = (int(packetAckNum) - checkAckNum - 1)

			if packetAckNum and ackMismatch:
				return ackMismatch
        
        return packet
