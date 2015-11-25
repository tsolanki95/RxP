import socket
import rxpacket
from rxpacket import RxPacket

class RxPSocket:

    def log(self, message):
        if DEBUG:
            print message

    # Class-wide port to use for NetEmu
    NetEmuPort = 500

    # Initliazation of class vars. Local to current instantiated class.
    def __init__(self, srcRxPPort, debug = True):
        self.state = 'CLOSED'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvWindowSize = RxPacket.maxWinSize()  # Receive Window size in bytes
        self.sendWindowSize = 1 # Send window size in bytes
        self.buffer = None      # Actual memory space for the buffer
        self.srcRxPPort = srcRxPPort  # Local RxP port, not UDP port
        self.desRxPPort = None     # Destination RxP Port, not UDP port
        self.desAddr = None
        self.srcAddr = "127.0.0.1"
        self.srcUDPPort = None
        self.desUDPPort = None
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

    def UDPdesSet(self, UDPdesport):
        self.log("Setting destination UDP port...\n")
        self.desUDPPort = UDPdesport

    def UDPbind(self, UDPsrcport):
        self.log("Setting source UDP port...\n")
        self.srcUDPPort = UDPsrcport

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
        self.log("Attempting to bind to RxP port " + str(aPort))
        try:
            if aPort:
                self.socket.bind((self.srcAddr, aPort))
                self.bindPort = aPort
        except Exception as e:
            print("The socket could not be bound to " + aPort + ".")
            self.log(str(e))

    # Listen for incoming connectins, and accepts them.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is established, sets up memory and window.
    def listen(self):
        if self.bindPort is None:
            self.log("An attempt to listen an un unbound port was made...\n")
            raise Exception("Socket not bound")
            sys.exit(1)

        self.state = 'LISTENING'

        waitLimit = self.resetLimit * 100

        self.log("Waiting for init packet...\n")
        while waitLimit:

            #receive INIT
            try:
                self.log("Calling recvfrom to see if we have anything...\n")
                theBytes, address = self.recvfrom(self.rcvWindowSize)
                self.log("Recvfrom called....\n")
                packet = self.__reconstructPacket(data = bytearray(theBytes))

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
            log("Socket timed out!\n")
            raise Exception('socket timeout')

        self.ackNum = packet.header['seqNum'] + 1
        self.log("Setting destination RxPPort to " + packet.header['desPort'])
        self.desRxPPort = packet.header['desPort']
        self.desAddr = addr[0]
        self.log("Setting destination UDP port to " + str(addr[1]))
        self.desUDPPort = addr[1]

        #Send Ack 1
        waitLimit = self.resetLimit * 100
        while waitLimit:

            try:
                #create packet
                flags = (False, False, True, False, False, False)
                initPacket = RxPacket(
                            srcPort = self.srcRxPPort,
                            desPort = self.desRxPPort,
                            seqNum = self.seqNum,
                            ackNum = self.ackNum,
                            flagList = flags,
                            winSize = self.recvWindowSize,
                            )
                self.sendto(initPacket.toByteArray(), (self.desAddr, self.desUDPPort))


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
                    srcPort = self.srcRxPPort,
                    desPort = self.desRxPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = flags,
                    winSize = self.recvWindowSize,
                    )
        self.sendto(initPacket.toByteArray(), (self.desAddr, self.desUDPPort))

        self.state = 'ESTABLISHED'


    # Connects to the specified host on the specified port.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is estabilshed, sets up memory and window.
    def connect(self, (ip, port)):
        if port == None:
            self.log("Socket not bound\n")
            raise Exception("Socket not bound")
            sys.exit(1)

        self.desAddr = ip
        self.desRxPPort = port

        try:
            self.log("Sending INIT packet....\n")
            # Create an Init packet and send it off to the host we wish to connect to.
            ack1 = self.__sendInit()

            # Create a Cnct packet and send it off to the other host
            self.log("Sending CNCT packet...\n")
            ack2 = __sendCnct()
        except Exception:
            self.log("Could not connect...\n")
            raise Exception("Could not connect")
        else:
            self.log("Connection established\n")
            self.state = 'ESTABLISHED'



    def send(self, msg):
        log("Entered send. Attempting to send message...\n")

        if self.srcRxPPort is None:
            raise Exception("Socket not bound")

        if self.state != 'ESTABLISHED':
            raise Exception("Connection not established")

        dataQueue = deque()
        packetQueue = deque()
        sentQueue = deque()
        lastSeqNum = self.seqNum

        log("Fragmenting data, adding it to que...\n")
        #fragment data and add it to data queue
        for i in range(stop = len(msg), step = RxPacket.getDataLength()):
            if (i + RxPacket.getDataLength() > len(msg)):
                dataQueue.append(bytearray(msg[i : ]))
            else:
                dataQueue.append(bytearray(msg[i : i + RxPacket.getDataLength()]))

        log("Constructing to data queue...\n")
        #construct packet queue from data queue
        for data in dataQueue:
            if data == dataQueue[0]:
                flags = (False, False, False, False, True, False)
            if data == dataQueue[-1]:
                flags = (False, False, False, False, False, True)
            else:
                flags = (False, False, False, False, False, False)

            packet = RxPacket(
                    srcPort = self.srcRxPPort,
                    desPort = self.desRxPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = flags,
                    winSize = self.recvWindowSize,
                    data = data
                    )

            self.seqNum += 1
            if self.seqNum >= RxPacket.maxSeqNum():
                self.seqNum = 0

            packetQueue.append(packet)

        log("Packet queue created...\n")

        log("Preparing to send packets...\n")

        resetsLeft = self.resetLimit
        while packetQueue and resetsLeft:
            #send packets in send window
            window = self.sendWindowSize
            while window and packetQueue:
                packetToSend = packetQueue.popLeft()
                log("Sending RxPPacket to IP: " + destAddr + " and port + " + desUDPPort + "...\n")
                self.sendto(packet.toByteArray(), (self.desAddr, self.desUDPPort))
                log("RxPPacket sent!\n")
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
                                srcPort = self.srcRxPPort,
                                desPort = self.desRxPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = flags,
                                winSize = self.recvWindowSize,
                                )
                    self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desUDPPort))

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
        if self.srcRxPPort is None:
            self.log("Socket already closed")

        if self.state != 'ESTABLISHED':
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
                if self.ackNum > RxPacket.maxAckNum():
                    self.ackNum = 0
                message += packet.data

                flags = (False, False, True, False, False, False)
                ackPacket = RxPacket(
                            srcPort = self.srcRxPPort,
                            desPort = self.desRxPPort,
                            seqNum = self.seqNum,
                            ackNum = self.ackNum,
                            flagList = flags,
                            winSize = self.recvWindowSize,
                            )
                self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desUDPPort))

                if (packet.isEndOfMessage()):
                    break

                if (packet.isFin()):
                    flags = (False, False, True, False, False, False)
                    ackPacket = RxPacket(
                                srcPort = self.srcRxPPort,
                                desPort = self.desRxPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = flags,
                                winSize = self.recvWindowSize,
                                )
                    self.sendto(ackPacket.toByteArray(), (self.desAddr, self.desUDPPort))
                    self.__closePassive(ackPacket)
                    break

                return message


        if not resetsLeft:
            raise Exception('Socket timeout')


        return message

    def sendto(self, data, address):
        self.log("Sending packet to " + str(address) + "\n")
        self.socket.sendto(data, address)

    def recvfrom(self, recvWindow):
        while True:
            try:
                packet = self.socket.recvfrom(recvWindow)
                self.log("Recieving message from " + str(packet[1]) + "\n")
            except socket.error as error:
                if error.errno is 35:
                    continue
                else:
                    raise e

        return packet

    def close(self):
        if self.srcRxPPort is None:
            self.socket.close()
            raise RxPException("Socket not bound")


        if self.state != 'ESTABLISHED':
            self.socket.close()
            raise Exception("Connection not established")

        fin_flags = (False, False, False, True, False, False)
        finPacket = RxPacket(
                    srcPort = self.srcRxPPort,
                    desPort = self.desRxPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = fin_flags,
                    winSize = self.recvWindowSize,
                    )

        self.seqNum += 1
        if self.seqNum > RxPacket.maxSeqNum():
            self.seqNum = 0

        resetsLeft = self.resetLimit()

        waitingForHostB = True
        isFinAcked = False

        while resetsLeft and (not isFinAcked or waitingForHostB):
            self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                data, address = self.recvfrom(self.recvWindowSize)
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
                                srcPort = self.srcRxPPort,
                                desPort = self.desRxPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = fin_flags,
                                winSize = self.recvWindowSize,
                                )

                    self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))
                    waitingForHostB = False

        self.socket.close()
        self = RxSocket(self.srcRxPPort, self.debug)
        self.state = 'CLOSED'

    def __closePassive(self, ackPacket):
        if self.srcRxPPort is None:
            self.socket.close()
            raise RxPException("Socket not bound")


        if self.state != 'ESTABLISHED':
            self.socket.close()
            raise Exception("Connection not established")

        fin_flags = (False, False, False, True, False, False)
        finPacket = RxPacket(
                    srcPort = self.srcRxPPort,
                    desPort = self.desRxPPort,
                    seqNum = self.seqNum,
                    ackNum = self.ackNum,
                    flagList = fin_flags,
                    winSize = self.recvWindowSize,
                    )

        self.seqNum += 1
        if self.seqNum > RxPacket.maxSeqNum():
            self.seqNum = 0

        resetsLeft = self.resetLimit()

        isFinAcked = False

        while resetsLeft and (not isFinAcked):
            self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                data, address = self.recvfrom(self.recvWindowSize)
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
                                srcPort = self.srcRxPPort,
                                desPort = self.desRxPPort,
                                seqNum = self.seqNum,
                                ackNum = self.ackNum,
                                flagList = fin_flags,
                                winSize = self.recvWindowSize,
                                )

                    self.sendto(finPacket.toByteArray(), (self.desAddr, self.desUDPPort))

        self.socket.close()
        self = RxSocket(self.srcRxPPort, self.debug)
        self.state = 'CLOSED'


    def __sendInit(self):

        #create packet
        self.log("Creating init packet......\n")

        try:
            self.log("Setting flags...\n")
            flags = (True, False, False, False, False, False)
        except Exception as e:
            self.log("Exception: " + str(e))
            sys.exit(0)
        self.log("Flags created...\n")

        try:
            initPacket = RxPacket.getInit(
                        srcPort = self.srcRxPPort,
                        desPort = self.desRxPPort,
                        seqNum = self.seqNum,
                        ackNum = self.ackNum,
                        winSize = self.recvWindowSize,
                        )
        except Exception as e:
            self.log("Exception: " + str(e))
            sys.exit(0)

        #increment seq num
        self.log("Incrementing sequence number......\n")
        self.seqNum = self.seqNum + 1 #increment by number of bytes (20 byte header only)
        if self.seqNum > RxPacket.maxSeqNum():
            self.seqNum = 0

        #transfer packet
        resetsLeft = self.resetLimit
        self.log("entering send loop for INIT packet......\n")
        while resetsLeft:
            self.log("Sending init......\n")
            self.sendto(initPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                self.log("waiting for ack......\n")
                data, address = bytearray(self.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data))

                if not packet:
                    self.log("Checksum failed......\n")
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else:
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    self.log("init has been acked......\n")
                    break
                else:
                    self.log("Wrong packet recieved, restarting init loop......\n")
                    resetsLeft -= 1

        if not resetsLeft:
            self.log("socket timeout......\n")
            raise Exception('socket timeout')

        return packet

    def __sendCnct(self):

        #create packet
        self.log("Creating cnct packet......\n")
        flags = (False, True, False, False, False, False)
        cnctPacket = RxPacket.getCnct(
                    srcPort = self.srcRxPPort,
                    desPort = self.desRxPPort,
                    seqNum = self.seqNum,
                    winSize = self.recvWindowSize,
                    )

        #increment seq num
        self.seqNum = self.seqNum + 1 #increment by number of bytes (20 byte header only)
        if self.seqNum > RxPacket.maxSeqNum():
            self.seqNum = 0


        #transfer packet
        resetsLeft = self.resetLimit
        self.log("entering send loop for INIT packet......\n")
        while resetsLeft:
            self.log("Sending init......\n")
            self.sendto(cnctPacket.toByteArray(), (self.desAddr, self.desUDPPort))

            try:
                self.log("waiting for ack......\n")
                data, address = bytearray(self.recvfrom(self.rcvWindowSize))
                packet = self.__reconstructPacket(data = bytearray(data))

                if not packet:
                    self.log("Checksum failed......\n")
                    resetsLeft -= 1
                    continue
            except socket.timeout:
                resetsLeft -= 1
            else:
                if packet.isAck() and packet.header['ackNum'] == self.seqNum:
                    self.log("init has been acked......\n")
                    break
                else:
                    self.log("Wrong packet recieved, restarting init loop......\n")
                    resetsLeft -= 1

        if not resetsLeft:
            self.log("socket timeout......\n")
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
