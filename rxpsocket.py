import socket
import rxpacket
import sys
import struct
from collections import deque
from rxpacket import RxPacket

DEBUG = False
SUPERDEBUG = False

def log(message):
    if DEBUG:
        print message

def superlog(message):
    if SUPERDEBUG:
        print message

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
        self.desUDPPort = int(UDPdesport)

    def UDPbind(self, UDPsrcport):
        self.log("Setting and binding source UDP port...\n")
        self.srcUDPPort = int(UDPsrcport)
        self.socket.bind((self.srcAddr, int(UDPsrcport)))

    def log(self, message):
        if self.debug:
            print message

    def gettimeout(self):
        return self.socket.gettimeout()

    def settimeout(self, val):
        return self.socket.settimeout(val)

    # Bind the socket to a specific local RxP port.
    # Set the object's port var.
    def bind(self, aPort):
        self.log("Attempting to bind to RxP port " + str(aPort))
        try:
            if aPort:
                self.srcRxPPort = int(aPort)
        except Exception as e:
            log("The socket could not be bound to " + aPort + ".")
            self.log(str(e))

    # Listen for incoming connectins, and accepts them.
    # Uses the RxP handshake as described in the RxP state diagram.
    # Once connection is established, sets up memory and window.
    def listen(self):
        if self.srcUDPPort is None:
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
                theBytes, address = self.recvfrom(self.recvWindowSize)
                self.log("Recvfrom called....\n")
                packet = self.__reconstructPacket(data = bytearray(theBytes))
                log("Packet has been reconstructed. We're in listen. Header: " + str(packet.header) + "\n")

                if packet is None:
                    waitLimit -= 1
                    continue

            except socket.timeout:
                waitLimit -= 1
                continue

            else:
                log("Checking to see if packet isInit, in listen...\n")
                if (packet.isInit()):
                    log("Packet is INIT; breaking out of while loop in listen...\n")
                    break
                else:
                    waitLimit -= 1


        if not waitLimit:
            log("Socket timed out!\n")
            raise Exception('socket timeout')


        self.ackNum = packet.header['seqNum'] + 1
        self.log("Setting destination RxPPort to " + str(packet.header['desPort']))
        self.desRxPPort = packet.header['desPort']
        self.desAddr = address[0]
        self.log("Setting destination UDP port to " + str(address[1]))
        self.desUDPPort = address[1]

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


                data, address = self.recvfrom(self.recvWindowSize)
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
        self.desRxPPort = int(port)

        try:
            self.log("Sending INIT packet....\n")
            # Create an Init packet and send it off to the host we wish to connect to.
            ack1 = self.__sendInit()

            # Create a Cnct packet and send it off to the other host
            self.log("Sending CNCT packet...\n")
            ack2 = self.__sendCnct()
            log("CNCT packet sent!\n")
        except Exception:
            self.log("Could not connect...\n")
            raise Exception("Could not connect")
        else:
            self.log("Connection established\n")
            self.state = 'ESTABLISHED'



    def send(self, msg):

        superlog("We're sending: " + str(len(msg)) + " bytes.\n")

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
        for i in range(0, len(msg), RxPacket.getDataLength()):
            if (i + RxPacket.getDataLength() > len(msg)):
                dataQueue.append(bytearray(msg[i : ]))
                log("In send dataQue loop, adding: " + bytearray(msg[i : ]).decode('UTF-8') )
            else:
                dataQueue.append(bytearray(msg[i : i + RxPacket.getDataLength()]))
                log("In send dataQue loop, adding: " + bytearray(msg[i : i + RxPacket.getDataLength()]).decode('UTF-8'))


        log("Constructing to data queue...\n")
        #construct packet queue from data queue

        #numPackQd = 0

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


            if packet.isAck():
                sys.exit(0)

            packetQueue.append(packet)
            #numPackQd += 1
            #print numPackQd

        log("Packet queue created...\n")

        log("Preparing to send packets...\n")

        numPackSent = 0


        resetsLeft = self.resetLimit
        while packetQueue and resetsLeft:
            #send packets in send window
            window = self.sendWindowSize
            while window and packetQueue:
                packetToSend = packetQueue.popleft()

                if (not isinstance(packetToSend, int)) and (not packetToSend.isAck()):
                    #log("Sending RxPPacket to IP: " + str(self.desAddr) + " and port + " + str(self.desUDPPort) + "...\n")
                    self.sendto(packetToSend.toByteArray(), (self.desAddr, self.desUDPPort))
                    numPackSent+=1
                    #log("RxPPacket sent!\n")
                    #log("RXP PACKET SIZE: " + str(len(packet.toByteArray())))
                    lastSeqNum = packetToSend.header['seqNum']

                    window -= 1
                    sentQueue.append(packet)

                else:
                    continue

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
                    while packet < 0 and sentQueue:
                        packetQueue.appendleft(sentQueue.pop())
                        packet += 1
                        continue
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

    def recv(self, maxLength):
        if self.srcRxPPort is None:
            self.log("Socket already closed")

        if self.state != 'ESTABLISHED':
            self.log("Socket already closed")

        message = bytes()
        log("INTIIAL INSTANTIATED MESSAGE: " + message.decode('UTF-8') + "\n")
        log("INTIAL MESSAGE LENGTH: " + str(len(message)))

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

                if packet.isAck():
                    resetsLeft -= 1
                    continue

                message += packet.data

                #log("Message so far is " + message.decode('UTF-8') + "\n")
                #log("Individual packet this time was " + packet.data.decode('UTF-8') + "\n")

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

                #superlog("Returning message of length: " + str(len(message)))
                #return message


        if not resetsLeft:
            raise Exception('Socket timeout')

        superlog("Returning message of length: " + str(len(message)))
        return message

    def sendto(self, data, address):
        #self.log("Sending packet to " + str(address) + " in sendto...\n")
        try:
            self.socket.sendto(data, address)
        except Exception as e:
            self.log("Exception when calling socket.sendto: " + str(e))
            sys.exit(0)

    def recvfrom(self, recvWindow):
        while True:
            try:
                log("Waiting to receive message...\n" )
                packet = self.socket.recvfrom(recvWindow)
                log("Message received from " + str(packet[1]) + "\n")
                break
            except socket.error as error:
                log("Socket error: " + str(error))
                if error.errno is 35:
                    continue
                else:
                    raise e

        log("Returning packet from recvfrom...\n")
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
        self.log("Entering send loop for INIT packet......\n")
        while resetsLeft:
            self.log("Sending init to IP: " + self.desAddr + " and Port:" + str(self.desUDPPort) +"...\n")

            try:
                self.sendto(initPacket.toByteArray(), (self.desAddr, self.desUDPPort))
            except Exception as e:
                self.log("Exception while calling sendto: " + str(e) + "\n")

            self.log("SENT INIT PACKET!\n")

            try:
                self.log("Waiting for ack......\n")
                data, address = self.recvfrom(self.recvWindowSize)
                log("Packet received successfully, calling reconstructPacket from _sendINIT...\n")
                packet = self.__reconstructPacket(data = bytearray(data))
                log("Packet successfully reconstructed inside _sendINIT...\n")

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
        self.log("Creating init packet......\n")

        try:
            self.log("Setting flags...\n")
            flags = (True, False, False, False, False, False)
        except Exception as e:
            self.log("Exception: " + str(e))
            sys.exit(0)
        self.log("Flags created...\n")

        try:
            cnctPacket = RxPacket.getCnct(
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
        self.log("Entering send loop for CNCT packet......\n")
        while resetsLeft:
            self.log("Sending init to IP: " + self.desAddr + " and Port:" + str(self.desUDPPort) +"...\n")

            try:
                self.sendto(cnctPacket.toByteArray(), (self.desAddr, self.desUDPPort))
            except Exception as e:
                self.log("Exception while calling sendto: " + str(e) + "\n")

            self.log("SENT INIT PACKET!\n")

            try:
                self.log("Waiting for ack......\n")
                data, address = self.recvfrom(self.recvWindowSize)
                log("Packet received successfully, calling reconstructPacket from _sendCNCT...\n")
                packet = self.__reconstructPacket(data = bytearray(data))
                log("Packet successfully reconstructed inside _sendCNCT...\n")

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
                    self.log("Wrong packet recieved, restarting cnct loop......\n")
                    resetsLeft -= 1

        if not resetsLeft:
            self.log("socket timeout......\n")
            raise Exception('socket timeout')

        return packet


    def __reconstructPacket(self, data, checkAckNum = False):

        log("Calling fromByteArray inside ReconstructPacket...\n")
        packet = RxPacket.fromByteArray(data)
        log("Packet created using fromByteArray inside ReconstructPacket...\n")

        log("Calling isValid() inside Reconstruct packet...\n")
        if not packet.isValid():
            log("Packet wasn't valid...\n")
            return None
        else:
            log("Packet was valid...\n")


        if checkAckNum:

			packetAckNum = packet.header['ackNum']

			ackMismatch = (int(packetAckNum) - checkAckNum - 1)

			if packetAckNum and ackMismatch:
				return ackMismatch

        log("About to return ReconstructedPacket...\n")
        log("The packet header for this Reconstruct packet is: " + str(packet.header) + "\n")
        if packet.data:
            log("The number of pytes for this Reconstructed packet is :" + str(len(packet.data)))
            log("PACKET DATA: " + packet.data.decode('UTF-8'))
        return packet
