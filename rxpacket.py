class RxPacket:
    
    # This class will be used to store helper functions for the RxP packet design.
    # The class itself is not meant ot be instantiated.

    # Returns a simple INIT packet.
    def getInit(srcPort, desPort, seqNum, ackNum):

    # Returns a simple CNCT packet.
    def getCnct(srcPort, desPort, seqNum, ackNum):


    # Return a byte array of packets to use when sending via UDP.
    # flagList should be a 4-length array of booleans corresponding to
    #  whether INIT, CNCT, ACK, and FIN are set.
    # winSize is the size of the window.
    # Data should be a byte array of data.
    def getPacket(srcPort, desPort, seqNum, ackNum, flagList, winSize = None, data = None):
