# This is a program to simulate the transmission of packets using FECN
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
        #print("0: ", self.ackCounter[0], " 1: ", self.ackCounter[1])
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
    output: "sender;packet;sendTime;ReceiveTime;rate"
    """

    def handlePacket(self, packet): # will return the correct ACK when receive packet
        if packet != {}:
            msg = str(packet["sender"]) + ";"
            msg += str(packet["packetNum"]) + ";"
            msg += str(packet["sentTime"]) + ";"
            msg += str(self.time) + ";"
            msg += str(packet["rate"])
            print(msg) # print out received packets
            id = packet["sender"]
            packetNum = packet["packetNum"]
            rd = packet["rd"] # FECN
            ack = (id, packetNum, rd) #FECN
            if packetNum == self.ackCounter[id]:
                self.ackCounter[id] += 1
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
                        packet["rd"] = -1 # for FECN
                        self.sent += 1
                    else: # timeout
                        packet = {}
                        packet["sender"] = self.id
                        packet["sentTime"] = self.time
                        packet["packetNum"] = timeout
                        packet["rate"] = self.rate
                        packet["rd"] = -1 # for FECN
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
                        packet["rd"] = -1 # for FECN
                        self.waitTimer[timeout] = 0 # restart timer
            else: # not ready to sent according to rate regulator
                packet = {}
        else: # transmission finished
            packet = {}
        return packet    

    # for FECN
    def handleRDTag(self, rd): # adjust the rate according to RD tag
        #print(rd)
        if rd > 0:
            self.rate = rd
        #print("current rate: ", self.rate)

# switch to relay packets sent from senders to the receiver
class Switch:
    def __init__(self, max, rate, tInterval):
        self.buffer = Buffer(max) # the buffer of the switch
        self.rate = rate # rate regulator for simulation
        self.time = 0 # global time
        # added for FECN
        self.advertisedRate = rate * NUM_SENDER # r0 = C / N0
        self.tInterval = tInterval
        self.qEq = round(max * 0.25) # equilibrium queue size

    def timePass(self):
        self.time += 1

    def bufferSize(self): # return current size of buffer
        return self.buffer.getSize()
        
    def receive(self, newElement):
        if newElement != {}:
            #print(self.bufferSize())
            newElement["rd"] = max(newElement["rd"], self.advertisedRate)
            self.buffer.push(newElement)
        
    def send(self):
        if self.time % self.rate == 0: # ready to relay according to rate regulator
            if self.buffer.isEmpty(): # nothing to relay
                return {}
            else: # something to relay
                return self.buffer.pop()
        else: # not ready to relay
            return {}

    # added for FECN
    def updateAdvertisedRate(self, arrivalRate):
        if self.time % self.tInterval == 0: # time for advertised rate update
            #fq = self.queueControlFunction()
            effectiveLoadFactor = self.rate / arrivalRate
            #print(self.advertisedRate * effectiveLoadFactor)
            self.advertisedRate = round(self.advertisedRate * effectiveLoadFactor)
            #print(arrivalRate)
            #print(effectiveLoadFactor)
            #print("ARate: ", self.advertisedRate)
            
    """
    def queueControlFunction(self): # linear function
        size = self.buffer.getSize()
        #print(size)
        return 1 - 0.333 * (size - self.qEq) / self.qEq
    """

"""  
main program
"""

# Constants, can be changed if neccessary
BUFFER_MAX = 21
NUM_SENDER = 2
NUM_PACKET = 200
WINDOW = 50
SENDER_RATE = 10 # default rate of senders
SWITCH_RATE = 10 # default rate of switch
# added for FECN
T_INTERVAL = 200

# initialization
switch = Switch(BUFFER_MAX, SWITCH_RATE, T_INTERVAL)
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
        #print("return RD: ", ack[2])
        sender[ack[0]].handleRDTag(ack[2]) # FECN
    # switch receive packets
    for i in range(NUM_SENDER):
        switch.receive(sender[i].sendPacket())
    # update the advertised rate of switch
    #print(sender[1].rate)
    denom = 1
    numer = 0
    for i in range(NUM_SENDER):
        denom *= sender[i].rate
    for i in range(NUM_SENDER):
        tmp = 1
        for j in range(NUM_SENDER):
            if j != i:
                tmp *= sender[j].rate
        numer += tmp
    arrivalRate = denom / numer # skewed
    switch.updateAdvertisedRate(arrivalRate)
    # update time
    for i in range(NUM_SENDER):
        sender[i].timePass()
    receiver.timePass()
    switch.timePass()
# return overhead count
print("ACK sent: ", receiver.getOverhead())