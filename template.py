# This is a program to simulate the transmission of packets without using any form of congestion control (template)
# Used for ELEC4848 FYP
# author: Law Lok Hin Andrew (3035571424) 

# buffer used in the switch
class Buffer:
    def __init__(self, max):
        self.max = max # max size of the buffer
        self.element = [] # the queue of the buffer
        self.size = 0 # the current size of the buffer
        
    def isEmpty(self):
        if self.size == 0:
            return True
        else:
            return False
    
    def isFull(self):
        if self.size == self.max:
            return True
        else:
            return False

    def getSize(self):
        return self.size
    
    def push(self, newElement):
        if not self.isFull():
            self.element.append(newElement)
            self.size += 1
    
    def pop(self):
        if not self.isEmpty():
            returnElement = self.element[0]
            self.element = self.element[1:]
            self.size -= 1
            return returnElement

# receiver to receive the packets sent by senders
class Receiver:
    def __init__(self, numSender, numPacket):
        self.numSender = numSender # the number of senders in the system
        self.numPacket = numPacket # the number of packets expected from each senders
        self.time = 0 # global time for data analysis
        self.overhead = 0 # counting the num of ACK sent
        self.ackCounter = {} # counting the packets ACKed
        for i in range(numSender):
            self.ackCounter[i] = 0
    
    def checkFinish(self): # check if all transmission are finished
        for i in range(self.numSender):
            if self.ackCounter[i] < self.numPacket:
                return False
        else:
            return True
        
    def timePass(self): # update the timers
        self.time += 1
    
    def getOverhead(self): # get the overhead count
        return self.overhead

    """
    packets received : {"sender": self.id, "sentTime": self.time, "packetNum": packetNum}
    """

    def handlePacket(self, packet): # will return the correct ACK when receive packet
        if packet != {}:
            msg = "Sender: " + str(packet["sender"]) + "; "
            msg += "Packet: " + str(packet["packetNum"]) + "; "
            msg += "Send Time: " + str(packet["sentTime"]) + "; "
            msg += "Receiver Time: " + str(self.time) + ";"
            msg += "Current Rate: " + str(packet["rate"]) + "; "
            print(msg) # print out received packets
            id = packet["sender"]
            packetNum = packet["packetNum"]
            if packetNum == self.ackCounter[id]:
                self.ackCounter[id] += 1
                ack = (id, packetNum)
                self.overhead += 1
            return ack  

# senders to send packets to the receiver 
class Sender:
    def __init__(self, id, num, window, rate):
        self.id = id # id of the sender
        self.num = num # num of packets to send
        self.window = window # time to wait before timeout
        self.rate = rate # rate for rate regulator (if any)
        self.sent = 0 # num of packets sent
        self.ack = 0 # num of packets ACKed
        self.time = 0 # num of cycle passed since beginning
        self.waitTimer = {} # timer for the oldest not ACKed packet
        for i in range(num):
            self.waitTimer[i] = -1 # -1 means the timer is not active
    
    def ackPacket(self, ptr): # ACK the packet
        if ptr == self.ack:
            self.ack += 1
            self.waitTimer[ptr] = -2 # -2 means timer stopped
    
    def timePass(self): # updating timers for every cycle pass
        self.time += 1
        for i in range(self.num):
            if self.waitTimer[i] >= 0:
                self.waitTimer[i] += 1
    
    def checkTimeout(self): # checking any packets sent timeout
        for i in range(self.num):
            if self.waitTimer[i] >= self.window:
                return i
            else:
                return -1
    
    def setRate(self, newRate): # changing the rate
        self.rate = newRate

    """
    packets sent : {"sender": self.id, "sentTime": self.time, "packetNum": packetNum}
    
    """
    def sendPacket(self):
        if self.ack < self.num: # transmission not finished
            if self.time % self.rate == 0: # ready according to rate regulator
                timeout = self.checkTimeout()
                if self.sent < self.num: # not all packets sent at least once
                    if timeout == -1: # no timeout
                        packet = {}
                        packet["sender"] = self.id
                        packet["sentTime"] = self.time
                        packet["packetNum"] = self.sent
                        packet["rate"] = self.rate
                        self.sent += 1
                    else: # timeout
                        packet = {}
                        packet["sender"] = self.id
                        packet["sentTime"] = self.time
                        packet["packetNum"] = timeout
                        packet["rate"] = self.rate
                        self.waitTimer[timeout] = 0 # restart timer
                else: # all packets sent at least once
                    if timeout == -1:
                        packet = {} # wait for timeout
                    else:
                        packet = {}
                        packet["sender"] = self.id
                        packet["sentTime"] = self.time
                        packet["packetNum"] = timeout
                        packet["rate"] = self.rate
                        self.waitTimer[timeout] = 0 # restart timer
            else: # not ready to sent according to rate regulator
                packet = {}
        else: # transmission finished
            packet = {}
        return packet    
        
# switch to relay packets sent from senders to the receiver
class Switch:
    def __init__(self, max, rate):
        self.buffer = Buffer(max) # the buffer of the switch
        self.rate = rate # rate regulator for simulation
        self.time = 0 # global time

    def timePass(self):
        self.time += 1

    def bufferSize(self): # return current size of buffer
        return self.buffer.getSize()
        
    def receive(self, newElement):
        if newElement != {}:
            self.buffer.push(newElement)
        
    def send(self):
        if self.time % self.rate == 0: # ready to relay according to rate regulator
            if self.buffer.isEmpty(): # nothing to relay
                return {}
            else: # something to relay
                return self.buffer.pop()
        else: # not ready to relay
            return {}
            
"""  
main program
"""

# Constants, can be changed if neccessary
BUFFER_MAX = 21 # min of 21 prevent deadlock
NUM_SENDER = 2
NUM_PACKET = 20
WINDOW = 50
SENDER_RATE = 10 # default rate of senders
SWITCH_RATE = 10 # default rate of switch

# initialization
switch = Switch(BUFFER_MAX, SWITCH_RATE)
receiver = Receiver(NUM_SENDER, NUM_PACKET)
sender = {}
for i in range(NUM_SENDER):
    sender[i] = Sender(i, NUM_PACKET, WINDOW, SENDER_RATE)
time = 0

# simulation
while not receiver.checkFinish():
    # switch relay packets in the buffer
    packet = switch.send()
    if packet != {}:
        ack = receiver.handlePacket(packet)
        sender[ack[0]].ackPacket(ack[1])
    # switch receive packets
    for i in range(NUM_SENDER):
        switch.receive(sender[i].sendPacket())
    # update time
    for i in range(NUM_SENDER):
        sender[i].timePass()
    receiver.timePass()
    switch.timePass()
# return overhead count
print("Overhead: ", receiver.getOverhead())