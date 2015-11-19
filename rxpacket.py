class RxPacket:

    #based on bit count for each value
    MAX_SEQUENCE_NUM = math.pow(2, 32) - 1
    MAX_ACK_NUM = math.pow(2, 32) - 1
    MAX_WINDOW_SIZE = math.pow(2, 16) - 1
    
    # This class will be used to store helper functions for the RxP packet design.
    # The class itself is not meant ot be instantiated.
    
    def __init__(self, byteArray = None, srcPort = None, desPort = None, seqNum = 0, ackNum = 0, flagList = None, winSize = MAX_WINDOW_SIZE, data = ""):
        if byteArray == None: #if no byte array
            if srcPort:
                self.srcPort = srcPort
            if desPort:
                self.desPort = desPort
            
            if seqNum > MAX_SEQUENCE_NUM:
                self.seqNum = seqNum - MAX_SEQUENCE_NUM #Restart the sequence numbers??
            else:
                self.seqNum = seqNum
            
            if ackNum > MAX_ACK_NUM:
                self.ackNum = ackNum - MAX_ACK_NUM
            else:
                self.ackNum = ackNum
                
            if flagList:
                self.flagList = flagList
            
            if winSize > MAX_WINDOW_SIZE:
                self.winSize = MAX_WINDOW_SIZE
            else:
                self.winSize = winSize
                
            self.data = data

    # Returns a simple INIT packet.
    def getInit(srcPort, desPort, seqNum, ackNum):

    # Returns a simple CNCT packet.
    def getCnct(srcPort, desPort, seqNum, ackNum):


    # Return a byte array of packets to use when sending via UDP.
    # flagList should be a 4-length array of booleans corresponding to
    #  whether INIT, CNCT, ACK, and FIN are set.
    # winSize is the size of the window.
    # Data should be a byte array of data.
    def getByteArray():
