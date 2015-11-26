DEBUG = True

def log(message):
    if DEBUG:
        print message

#import rxpsocket
import rxpsocket
import sys
import struct
import socket

# Simple File Transfer Application
# This is the client.

# Validate arguments passed into the program.
def validateSysArgs():
    # Check number of arguments
    if len(sys.argv) != 4:
        log("Arguement list != 4, listing usage...\n")
        usage()

    # Check arguments.
    try:
        int(sys.argv[1])
        int(sys.argv[3])
        socket.inet_aton(sys.argv[2])
    except:
        log("Couldn't confirm that the argumenmts are in the correct format...\n")
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
    asocket.send(msg)

def recv_msg(asocket):
    return asocket.recv(100000000000)


'''
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
    log("Preparing to receive " + str(n) + " bytes...\n")

    # Helper function to recv n bytes or return None if EOF is hit
    data = ''
    recvCallsMade = 0;
    while len(data) < n:
        log("Length of received data is " + str(len(data)) + "\n")
        log("Length of total data is " + str(n) + "\n")


        # Only show progress if we're downloading a file bigger than 200 bytes.
        if n > 1000:
            # Show download progress.
            sys.stdout.write('\r')
            sys.stdout.write('>>>> Downloading file... ' + str(float(int(100 * (len(data) / float(n))))) + "% <<<<")
            sys.stdout.flush()
        packet = asocket.recv(n - len(data))
        log("In recvall, receieved " + str((n-len(data))) + "bytes...\n")
        if not packet:
            return None
        data += packet
        recvCallsMade += 1
    sys.stdout.write('\r')
    if n > 1000:
        sys.stdout.write('>>>> Downloading file... 100% <<<<')
    log("\n Calls to rcv() made: " + str(recvCallsMade) + "...\n")
    print str(len(data)) + " bytes successuflly received.\n"
    log("The data receieved in RECVALL is: " + data.decode('UTF-8'))
    return data
'''

def window(size):
    print "This functionality isn't implemented yet.\n"

def handleGet(filename):
    try:
        log("Attempting to open file " + filename + "...\n")
        log("The type of the filename is: " + str(type(filename)))
        with open(filename.decode('UTF-8'), "rb") as afile:
        # File is open. Send as bytestream.
            log("File opened - now attempting to read it in.\n")
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
    log("Sending READY message to client...\n")
    send_msg(sock, "READY")

    log("Ready message sent...\n")
    theFile = recv_msg(sock)

    log("Received file!\n")
    log("Sending OKAY message...\n")
    send_msg(sock, "OKAY")

    log("Writing file...\n")
    f = open(filename.decode('UTF-8'), 'wb')
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
        try:
            log("Attempting to listen...\n")
            try:
                sock.listen()
            except Exception as e:
                log("Exception: " + str(e))
                sys.exit(0)
            log("Setting state to connected.\n")
            state = "Connected"
        except Exception as e:
            log("Connection Failed: " + str(e))
            return

    # Once we're connected, wait for a GET or PUT request.
    log("Waiting for message from client...\n")
    message = recv_msg(sock)

    # We've got something from the recv call.

    # Client closed connection.
    if message is None:
        log("Client terminated connection.")
        state = 'NotConnected'
    else:
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
            log("Calling PUT handler for file " + filename + "...\n")
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

locUDPPort = sys.argv[1]
destUDPPort = sys.argv[3]
destIP = sys.argv[2]

log("Creating empty socket...\n")
sock = rxpsocket.RxPSocket(serverRxPPort)
sock.settimeout(250)
state = 'NotConnected'

# Bind to local RxP ip and port.
try:
    log("Binding server RXPport: " + str(serverRxPPort))
    sock.bind(serverRxPPort)
    log("Binding UDP src port: " + str(locUDPPort))
    sock.UDPbind(locUDPPort)
    log("Binding UDP des port: " + str(destUDPPort))
    sock.UDPdesSet(destUDPPort)
    log("UDP src and des ports set; RxP src port bound...\n")
except Exception as e:
    print "ERROR: Could not bind to port " + str(locUDPPort) + " on localhost.\n"
    log("Exception: " + str(e))
    sys.exit(1)

log("Entering run loop for first time...\n")
while True:
    runServer()

# ------------END PROGRAM RUN LOOP-------------------- #
