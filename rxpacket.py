'''
class: RxPacket

Stores all necessary data and functions to deal with packets in an object oriented manor

fields:
    header: dictionary storing all header values
    data: holds the data sent in this packet
'''
class RxPacket:

    # based on bit count for each value
    MAX_SEQUENCE_NUM = math.pow(2, 32) - 1
    MAX_ACK_NUM = math.pow(2, 32) - 1
    MAX_WINDOW_SIZE = math.pow(2, 16) - 1
    HEADER_LENGTH = 20 # number of bytes in header
    
    HEADER_FIELDS = ( 
                    ('srcPort', uint16, 2), 
                    ('desPort', uint16, 2), 
                    ('seqNum', uint32, 4), 
                    ('ackNum', uint32, 4), 
                    ('flags', uint32, 4), 
                    ('winSize', uint16, 2), 
                    ('checksum', uint16, 2) 
                    )
    
    # static methods
    
    # Returns a simple INIT packet.
    def getInit(srcPort, desPort, seqNum, ackNum, winSize):
        p = RxPacket(srcPort, desPort, seqNum, ackNum, (True, False, False, False), winSize)
        return p

    # Returns a simple CNCT packet.
    def getCnct(srcPort, desPort, seqNum, ackNum):
        p = RxPacket(srcPort, desPort, seqNum, ackNum, (False, True, False, False), winSize)
        return p
        
    # returns an RxPacket given a byteArray as an input        
    def fromByteArray(byteArray):
        p = RxPacket()
        p.__unpickle(byteArray)
    # end static methods
    
    # constructor
    def __init__(self, srcPort = 0, desPort = 0, seqNum = 0, ackNum = 0, flagList = None, winSize = MAX_WINDOW_SIZE, data = bytearray()):
        
        if srcPort:
            self.header['srcPort'] = srcPort
        if desPort:
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
        
        if winSize > MAX_WINDOW_SIZE:
            self.header['winSize'] = MAX_WINDOW_SIZE
        else:
            self.header['winSize'] = winSize
                    
        self.data = data
        
        self.header['checksum'] = self.__computeChecksum()
    
    # instance methods
    
    # checks if the internet checksum provided is equal to what is 
    # calculated on this side
    def isValid(self):
        givenChecksum = self.header['checksum']
        calculatedChecksum = self.__computeChecksum()
        return givenChecksum == calculatedChecksum
    
    # checks if it is an init packet
    def isInit(self):
        return header['flags'][0]
    
    def isCnct(self):
        return header['flags'][1]
    
    def isAck(self):
        return header['flags'][2]
    
    def isFin(self):
        return header['flags'][3]
        
    # Return a byte array of packets to use when sending via UDP.
    # flagList should be a 4-length array of booleans corresponding to
    # whether INIT, CNCT, ACK, and FIN are set.
    # winSize is the size of the window.
    # Data should be a byte array of data.
    def toByteArray(self):
        packet = bytearray()
        packet.extend(self.__pickleHeader())
        packet.extend(self.data)
        return packet
        
    #end instance methods
    
    # http://stackoverflow.com/a/1769267
    def __computeChecksum(self):
        self.header['checksum'] = 0
        packet = str(self.getByteArray())
        
        sum = 0
        for i in range(0, len(packet), 2):
            
            #16 bit carry-around addition
            value = ord(packet[i]) + (ord(packet[i + 1]) << 8)
            temp = sum + value
            sum = (temp & 0xffff) + (temp >> 16)
            
        return ~sum & 0xffff #16-bit one's complement
    
    #adds byteArray to object
    def __unpickle(self, byteArray):
        if byteArray:
            headerBytes = byteArray[0 : HEADER_LENGTH]
            self.__unpickleHeader(headerBytes)
            
            dataBytes = byteArray[HEADER_LENGTH : ]
            self.data = dataBytes
            
    def __unpickleHeader(self, headerBytes):
        base = 0
        
        #for each header field, get values
        for (fieldName, dataType, size) in HEADER_FIELDS:
            # Get the bytes from byteArray, convert to int
            bytes = headerBytes[base : base + size]
            value = dataType.from_buffer(bytes).value
            
            #add specific field, done differently for flags
            if (fieldName == 'flags'):
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
        return (isInit, isCnct, isAck, isFin)
        
    #converts the header to a length 20 bytearray
    def __pickleHeader(self):
        byteArray = bytearray()
        
        for (fieldName, dataType, size) in HEADER_FIELDS:
            value = self.header[fieldName]
            
            if (fieldName != 'flags'):
                byteArray.extend(bytearray(dataType(value)))
            else:
                byteArray.extend(self.__pickleFlags())
        
        return byteArray
    
    #converts a flag list to a length 4 bytearray
    def __pickleFlags(self):
        value = 0
        flags = self.header['flags']
        if flags[0] == True:
            value = value | 0x1
        if flags[1] == True:
            value = value | (0x1 << 1)
        if flags[2] == True:
            value = value | (0x1 << 2)
        if flags[3] == True:
            value = value | (0x1 << 3)
        return bytearray(uint32(value))
        
    #end instance methods
        
        
        
        
