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
    print "X: port number to which FxA client's UDP socket should bind (even)"
    print "to. Should be one less than the server's port number.\n"
    print "A: the IP address of NetEmu\n"
    print "P: the UDP port number of NetEMU\n"
    print "Example:\n"
    print "FxA-Client.py 5001 127.0.0.1 5002"
    sys.exit(1)

# Validate commands given while running the program.
def validCommand(command):
    theFirstWord = command.split(' ', 1)[0]
    if theFirstWord in ['connect', 'disconnect']:
        return True
    elif theFirstWord in ['get', 'post', 'window']:
        if len(command.split(' ', 1)) == 2:
            return True
    return False

# Connect to the FXA server.
def connect():
    # Globals
    global state

    if state != 'NotConnected':
        log("Socket state is not 'NotConneted'. Closing for good practice.\n")
        sock.close()

    try:
        log("Attempting to connect to server at IP:" + destIP + " and Port:" + str(serverRxPPort) + "...\n")
        sock.connect((destIP, serverRxPPort))
        state = "Connected"
    except Exception as e:
        log("Exception: " + str(e) + "...\n")
        print "Could not connect to the server. Something's wrong.\n"
    else:
        state = 'Connected'
        print "Connected to server.\n"

def get(filename):
    # Send request for file.
    # Get response from server.
    getRequest = "GET " + filename

    log("Sending GET request for file " + filename + "...\n")
    send_msg(sock, getRequest)

    log("Awaiting for server response...\n")
    received = recv_msg(sock)


    # We got a message back, yay!
    if received != None:
        log("Received message from server. Decoding...\n")
        # Check for error message
        if received.decode('UTF-8').split(' ', 1)[0] == 'ERROR':
            log("Server returned error...\n")
            print received.decode('UTF-8')
        # Write file.
        else:
            log("Server returned file...\n")
            f = open(filename, 'wb')
            log("Writing file " + filename + "...\n")
            f.write(received)
            f.close()
            print "File written!\n"
    elif received == None:
        print "Received an empty message. Something's wrong."


def put(filename):
    # Puts file to server.
    sendRequest = "PUT " + filename

    send_msg(sock, sendRequest)

    response = recv_msg(sock)

    # Server is ready to receive file.
    if response.decode("UTF-8") == 'READY':
        # Read file into bytearray
        with open(filename, "rb") as theFile:
            f = theFile.read()
            fileBytes = bytearray(f)

        # Finally, send the message.
        send_msg(sock, fileBytes)

        # Make sure server got it.
        msg = recv_msg(sock)

        if msg.decode("UTF-8") == "OKAY":
            print "File transferred!"
        else:
            print "ERROR: " + msg.decode("UTF-8")
    else:
        print "Server cannot receive file. Reason: " + response.decode("UTF-8")

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

def disconnect():
    if sock is None:
        print "You haven't connected to anything yet!\n"
    else:
        if state == 'NotConnected':
            print "Socket is already disconnected.\n"
        elif state == 'Connected':
            sock.close()
            state = 'NotConnected'

# Main function.
def runClient():
    # Get the command from the user.
    command = raw_input('\n\nPlease enter a command:\n')

    # Validate command.
    if validCommand(command):
        log("Command validated...\n")
        # Get actual command.
        actualCommand = command.split(' ', 1)[0]

        # Call command handler.
        if actualCommand == 'connect':
            log("Calling connect...\n")
            connect()
        elif actualCommand == 'get':
            log("Calling get...\n")
            get(command.split(' ', 1)[1])
        elif actualCommand == 'put':
            log("Calling put...\n")
            put(command.split(' ', 1)[1])
        elif actualCommand == 'window':
            log("Calling window...\n")
            window(command.split(' ', 1)[1])
        elif actualCommand == 'disconnect':
            log("CAlling disconnect...\n")
            disconnect()

    # Not a valid command.
    else:
        print "That command is not recognized. Valid commands are: \n"
        print "connect, get [filename], post [filename], window [receiverWinSize], disconnect\n"


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
    log("Binding socket to 127.0.0.1 at port " + str(clientRxPPort) + "...\n")
    sock.bind(("127.0.0.1", clientRxPPort))
except:
    print "ERROR: Could not bind to port " + str(clientRxPPort) + " on localhost.\n"
    sys.exit(1)

log("Entering run loop for first time...\n")
while True:
    runClient()

# ------------END PROGRAM RUN LOOP-------------------- #
