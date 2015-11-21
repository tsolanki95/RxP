class RxPacket:

    #based on bit count for each value
    MAX_SEQUENCE_NUM = math.pow(2, 32) - 1
    MAX_ACK_NUM = math.pow(2, 32) - 1
    MAX_WINDOW_SIZE = math.pow(2, 16) - 1
    HEADER_LENGTH = 20 #number of bytes in header
    
    HEADER_FIELDS = ( ('srcPort', uint16, 2), ('desPort', uint16, 2), ('seqNum', uint32, 4), ('ackNum', uint32, 4), ('flags', uint32, 4), ('winSize', uint16, 2), ('checksum', uint16, 2)
    
    # This class will be used to store helper functions for the RxP packet design.
    
    def __init__(self, byteArray = None, srcPort = 0, desPort = 0, seqNum = 0, ackNum = 0, flagList = None, winSize = MAX_WINDOW_SIZE, data = bytearray()):
        if byteArray == None: #if no byte array
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
            
            computechecksum()
            
        else:
            unpickle(byteArray)

    # Returns a simple INIT packet.
    def getInit(srcPort, desPort, seqNum, ackNum):

    # Returns a simple CNCT packet.
    def getCnct(srcPort, desPort, seqNum, ackNum):
    
    def isValid(self, checksum):
    
    def isInit(self):
    
    def isCnct(self):
    
    def isAck(self):
    
    def isFin(self):
    
    #converts byte array to object
    def unpickle(self, byteArray):
        if byteArray:
            headerBytes = byteArray[0 : HEADER_LENGTH]
            unpickleHeader(headerBytes)
            
            dataBytes = byteArray[HEADER_LENGTH : ]
            self.data = dataBytes
            
    def unpickleHeader(self, headerBytes):
        base = 0
        
        #for each header field, get values
        for (fieldName, dataType, size) in HEADER_FIELDS:
            # Get the bytes from byteArray, convert to int
            bytes = headerBytes[base : base + size]
            value = dataType.from_buffer(bytes).value
            
            #add specific field, done differently for flags
            if (fieldName != 'flags'):
                self.header[fieldName] = value
            else:
                unpickleFlags(value)
            
            #increment base
            base = base + size
        
        
            

    # Return a byte array of packets to use when sending via UDP.
    # flagList should be a 4-length array of booleans corresponding to
    #  whether INIT, CNCT, ACK, and FIN are set.
    # winSize is the size of the window.
    # Data should be a byte array of data.
    def getByteArray(self):
        packet = bytearray()
        packet.extend(pickleHeader())
        packet.extend(self.data)
        return packet
        
    def pickleHeader(self):
        byteArray = bytearray()
        
        for (fieldName, dataType, size) in HEADER_FIELDS:
            value = self.header[fieldName]
            
            if (fieldName != 'flags'):
                byteArray.extend(bytearray(dataType(value)))
            else:
                byteArray.extend(pickleFlags(value))
            
        
        return byteArray
        
        
        
        
