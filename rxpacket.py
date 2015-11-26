'''
class: RxPacket

Stores all necessary data and functions to deal with packets in an object oriented manor

fields:
    header: dictionary storing all header values
    data: holds the data sent in this packet
'''
import ctypes
import sys
import socket
import math
import struct
import random
from functools import reduce

DEBUG = False

def log(message):
    if DEBUG:
        print message

class RxPacket:

    uint16 = ctypes.c_uint16
    uint32 = ctypes.c_uint32

    # Global decs
    global MAX_SEQUENCE_NUM
    global MAX_ACK_NUM
    global MAX_WINDOW_SIZE
    global HEADER_LENGTH
    global DATA_LEN
    global HEADER_FIELDS


    # based on bit count for each value
    MAX_SEQUENCE_NUM = int(math.pow(2, 32) - 1)
    MAX_ACK_NUM = int(math.pow(2, 32) - 1)
    MAX_WINDOW_SIZE = int(math.pow(2, 16) - 1)
    HEADER_LENGTH = 20 # number of bytes in header
    DATA_LEN = 1004

    HEADER_FIELDS = (
                    ('srcPort', uint16, 2),
                    ('desPort', uint16, 2),
                    ('seqNum', uint32, 4),
                    ('ackNum', uint32, 4),
                    ('flagList', uint32, 4),
                    ('winSize', uint16, 2),
                    ('checksum', uint16, 2)
                    )

    # static methods
    @staticmethod
    def maxSeqNum():
        log("Returning max sequence number...\n")
        return MAX_SEQUENCE_NUM

    @staticmethod
    def maxAckNum():
        log("Returning max ack number...\n")
        return MAX_ACK_NUM

    @staticmethod
    def maxWinSize():
        log("Returning max window size...\n")
        return MAX_WINDOW_SIZE

    @staticmethod
    def getHeaderLeangth():
        log("Returning header length...\n")
        return HEADER_LENGTH

    @staticmethod
    def getDataLength():
        log("Returning data length...\n")
        return DATA_LEN

    # Returns a simple INIT packet.
    @staticmethod
    def getInit(srcPort, desPort, seqNum, ackNum, winSize):
        log("Returning an INIT packet...\n")
        return RxPacket(srcPort, desPort, seqNum, ackNum, (True, False, False, False, False, False), winSize)

    # Returns a simple CNCT packet.
    @staticmethod
    def getCnct(srcPort, desPort, seqNum, ackNum, winSize):
        log("Returning a CNCT packet...\n")
        return RxPacket(srcPort, desPort, seqNum, ackNum, (False, True, False, False, False, False), winSize)


    # returns an RxPacket given a byteArray as an input
    @staticmethod
    def fromByteArray(byteArray):
        log("Creating an empty RXPacket in fromByteArray...\n")
        p = RxPacket()
        log("Unpicking byteArray to packet...\n")
        p.__unpickle(byteArray)
        log("Returning unpickled packet..." + str(p.header) + "\n")
        return p
    # end static methods

    # constructor
    def __init__(self, srcPort = 0, desPort = 0, seqNum = 0, ackNum = 0, flagList = None, winSize = MAX_WINDOW_SIZE, data = None):
        self.header = {}

        self.header['srcPort'] = srcPort
        self.header['desPort'] = desPort

        if seqNum > MAX_SEQUENCE_NUM:
            self.header['seqNum'] = seqNum - MAX_SEQUENCE_NUM #Restart the sequence numbers??
        else:
            self.header['seqNum'] = seqNum

        if ackNum > MAX_ACK_NUM:
            self.header['ackNum'] = ackNum - MAX_ACK_NUM
        else:
            self.header['ackNum'] = ackNum

        if flagList:
            self.header['flagList'] = flagList
        else:
            self.header['flagList'] = (False, False, False, False, False, False)

        if winSize > MAX_WINDOW_SIZE:
            self.header['winSize'] = MAX_WINDOW_SIZE
        else:
            self.header['winSize'] = winSize

        if data:
            self.data = bytearray(data)
        else:
            self.data = None

        log("Computing checksum...\n")
        self.header['checksum'] = 0

        log("Converting packet to byteArray...\n")
        packet = str(self.toByteArray())
        log("Packet converted to byteArray...\n")

        asum = 0
        for i in range(0, len(packet), 2):

            #16 bit carry-around addition
            if i + 1 == len(packet):
                value = ord(packet[i])
            else:
                value = ord(packet[i]) + (ord(packet[i + 1]) << 8)
            temp = asum + value
            asum = (temp & 0xffff) + (temp >> 16)

        log("Done computing checksum....\n")
        self.header['checksum'] = int(~asum & 0xffff)
        log("Header is : " + str(self.header) + ".....\n")

    # instance methods

    # checks if the internet checksum provided is equal to what is
    # calculated on this side
    def isValid(self):
        log("isValid entered...\n")
        givenChecksum = self.header['checksum']
        log("given checksum is: " + str(givenChecksum) + "...\n")
        calculatedChecksum = self.__computeChecksum()
        return givenChecksum == calculatedChecksum

    # checks if it is an init packet
    def isInit(self):
        return self.header['flagList'][0]

    def isCnct(self):
        return self.header['flagList'][1]

    def isAck(self):
        return self.header['flagList'][2]

    def isFin(self):
        return self.header['flagList'][3]

    def isEndOfMessage(self):
        return self.header['flagList'][5]

    # Return a byte array of packets to use when sending via UDP.
    # flagList should be a 4-length array of booleans corresponding to
    # whether INIT, CNCT, ACK, and FIN are set.
    # winSize is the size of the window.
    # Data should be a byte array of data.
    def toByteArray(self):
        packet = bytearray()
        log("Pickling header.....\n")
        packet.extend(self.__pickleHeader())
        log("Done pickling header.....\n")
        if self.data:
            log("adding data.....\n")
            packet.extend(self.data)
            log("done adding data.....\n")
        return packet

    #end instance methods

    # http://stackoverflow.com/a/1769267
    def __computeChecksum(self):
        log("Computing checksum...\n")
        self.header['checksum'] = 0

        log("Converting packet to byteArray...\n")
        packet = str(self.toByteArray())
        log("Packet converted to byteArray...\n")

        asum = 0
        for i in range(0, len(packet), 2):

            #16 bit carry-around addition
            if i + 1 == len(packet):
                value = ord(packet[i])
            else:
                value = ord(packet[i]) + (ord(packet[i + 1]) << 8)
            temp = asum + value
            asum = (temp & 0xffff) + (temp >> 16)

        log("Done computing checksum....\n")
        return int(~asum & 0xffff)
        log("ComputeChecksum: Header is : " + str(self.header) + ".....\n")

    #adds byteArray to object
    def __unpickle(self, byteArray):
        if byteArray:
            headerBytes = byteArray[0 : HEADER_LENGTH]
            self.__unpickleHeader(headerBytes)

            if (len(byteArray) != HEADER_LENGTH):
                dataBytes = byteArray[HEADER_LENGTH : ]
            else:
                dataBytes = None
            self.data = dataBytes

    def __unpickleHeader(self, headerBytes):
        base = 0

        #for each header field, get values
        for (fieldName, dataType, size) in HEADER_FIELDS:
            # Get the bytes from byteArray, convert to int
            bytes = headerBytes[base : base + size]
            value = dataType.from_buffer(bytes).value

            #add specific field, done differently for flags
            if (fieldName == 'flagList'):
                value = self.__unpickleFlags(value)

            #add value to header
            self.header[fieldName] = value

            # increment base
            base = base + size

    def __unpickleFlags(self, value):
        # checks if each individual bit is present
        isInit = ((value & 0x1) == 1)
        isCnct = (((value & 0x2) >> 1) == 1)
        isAck = (((value & 0x4) >> 2) == 1)
        isFin = (((value & 0x8) >> 3) == 1)
        isNM = (((value & 0x16) >> 4) == 1)
        isEOM = (((value & 0x32) >> 5) == 1)
        return (isInit, isCnct, isAck, isFin, isNM, isEOM)

    #converts the header to a length 20 bytearray
    def __pickleHeader(self):
        byteArray = bytearray()

        for (fieldName, dataType, size) in HEADER_FIELDS:
            log("Pickling header field " + fieldName + "....\n")
            value = self.header[fieldName]

            if (fieldName != 'flagList'):
                log("Pickling non-flags...\n")
                byteArray.extend(bytearray(dataType(value)))
                log("Pickling successfull...\n")
            else:
                log("Pickling flags...\n")
                byteArray.extend(self.__pickleFlags(dataType))
                log("Flags pickled successfully...\n")

        return byteArray

    #converts a flag list to a length 4 bytearray
    def __pickleFlags(self, dataType):
        log("Entered pickle flags method...\n")
        value = 0
        flags = self.header['flagList']

        log("Current flags: " + str(flags))
        if flags[0] == True:
            value = value | 0x1
        if flags[1] == True:
            value = value | (0x1 << 1)
        if flags[2] == True:
            value = value | (0x1 << 2)
        if flags[3] == True:
            value = value | (0x1 << 3)
        if flags[4] == True:
            value = value | (0x1 << 4)
        if flags[5] == True:
            value = value | (0x1 << 5)
        return bytearray(dataType(value))

    #end instance methods
