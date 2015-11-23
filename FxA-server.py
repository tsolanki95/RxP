DEBUG = True

def log(message):
    if DEBUG:
        print message

#import rxpsocket
import socket
import sys
import struct

# Simple File Transfer Application
# This is the client.

# Validate arguments passed into the program.
def validateSysArgs():
    # Check number of arguments
    if len(sys.argv) != 4:
        usage()

    # Check arguments.
    try:
        int(sys.argv[1])
        int(sys.argv[3])
        socket.inet_aton(sys.argv[2])
    except:
        usage()

# Simple function to print usage and exit.
def usage():
    print "FxA-Client Usage: \n"
    print "FxA-Client.py X A P\n"
    print "-----------------------------\n"
    print "X: port number to which FxA server's UDP socket should bind (odd)"
    print "to. Should be one less than the server's port number.\n"
    print "A: the IP address of NetEmu\n"
    print "P: the UDP port number of NetEMU\n"
    print "Example:\n"
    print "FxA-Server.py 5001 127.0.0.1 5002"
    sys.exit(1)

# Validate commands given while running the program.
def validCommand(command):
    theFirstWord = command.split(' ', 1)[0]
    if theFirstWord == 'window':
        return True
    elif theFirstWord == 'terminate':
        print "Exiting, thank you!"
        sys.exit(0)
    else:
        return False

def send_msg(asocket, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    asocket.send(msg)

def recv_msg(asocket):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(asocket, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(asocket, msglen)

def recvall(asocket, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
    while len(data) < n:
        packet = asocket.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def window(size):
    print "This functionality isn't implemented yet.\n"

def handleGet(filename):
    try:
        log("Attempting to open file " + filename + "...\n")
        with open(filename, "rb") as afile:
        # File is open. Send as bytestream.
            log("File opened - now attempting to read it in.")
            toSend = afile.read()
            bytesToSend = bytearray(toSend)
            log("File imported as byteArray...\n")
            log("Sending file to client...\n")
            send_msg(sock, bytesToSend)
            if DEBUG:
                print "Sent file!"
    except IOError as e:
        # File doe snot exist. Send error message.
        eMessage = "ERROR : File does not exist."
        log("Exception: " + str(e) + "...\n")
        log("Sending error message to cleint...\n")
        send_msg(sock, eMessage)

def handlePut(filename):
    # Send ready message.
    rMessage = "READY"
    send_msg("READY")

    theFile = recv_msg(sock)
    f = open(filename, 'wb')
    f.write(theFile)
    f.close()
    print "File written!\n"

# Main function.
def runServer():
    log("-------TOP OF RUN LOOP------------------")

    # Globals
    global sock
    global state

    # Listen and accept incoming connections, if we're not already connected.
    # Blocks until we're connected.

    #if not sock.connected():

    # If socket isn't listening, listen!
    log("State is currently " + state + "...\n")
    if not (state == "Listening" or state == "Connected"):
        log("Attempting to listen...\n")
        sock.listen(1)
        log("Setting state to listening.\n")
        state = "Listening"

    # Only accept new connections if we aren't connected
    if not state == "Connected":
        log("Now accepting incoming connections...\n")
        sock, addr = sock.accept()
        state = "Connected"
        log("Connected with client at " + str(addr) + "...\n")

    # Once we're connected, wait for a GET or PUT request.
    log("Waiting for message from client...\n")
    message = recv_msg(sock)
    log("Message received!...\n")
    command = message.split(' ', 1)[0]
    filename = message.split(' ', 1)[1]
    log("Message command: " + command + "...\n")
    log("Message filename: " +  filename + "...\n")

    # If get, send to handler.
    if command == 'GET':
        log("Calling GET handler for file " + filename + "...\n")
        handleGet(filename)

    # IF put, send to handler.
    elif command == 'PUT':
        log("Calling PUT handler for file " + filanemae + "...\n")
        handlePut(filename)

    # Invalid command! Send error.
    else:
        log("Invalid command received...\n")
        print "Command that was not GET or PUT received. Exiting."
        sys.exit(1)

# ------------PROGRAM RUN LOOP-------------------- #
print("\n")

# First, make sure parameters are correctly used.
log("Validating arguments...\n")
validateSysArgs()

# Global RXP FTP ports.
clientRxPPort = 6001
serverRxPPort = 6002

locPort = sys.argv[1]
destPort = sys.argv[3]
destIP = sys.argv[2]
#sock = rxpsocket()
log("Creating empty socket...\n")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
state = 'NotConnected'

# Bind to local ip and port.
try:
    log("Binding socket to 127.0.0.1 at port " + str(serverRxPPort) + "...\n")
    sock.bind(("127.0.0.1", serverRxPPort))
except:
    print "ERROR: Could not bind to port " + str(serverRxPPort) + " on localhost.\n"
    sys.exit(1)

log("Entering run loop for first time...\n")
while True:
    runServer()

# ------------END PROGRAM RUN LOOP-------------------- #