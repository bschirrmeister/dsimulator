# This is the main class. Where everything starts
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from constants import *
from statechart import State, simMessage
from network import Network

import simuProtocol_pb2
import binascii
import time
import Queue
import select
import SocketServer

#import layers / modules
import cmts

from api import *

class CMState(State):
    def signal(self, message):
        message.mac = self.context.mac
        # print "LOG::CMState signal message.mac=%s messge.name=%s"  % (message.mac,message.name) 
        # print "LOG::CMState context=",self.context,"parent=",self.parent

        super(CMState, self).signal(message, signalQueue)

class RunningDevices(State):
    ''' This class holds the whole world of running devices (CPEs,cablemodems,CMTS, etc.).
        Here, is where every message is delivered to the appropiate devie '''

    def __init__(self, queueSignal=None):
        super(RunningDevices, self).__init__( qSignal=queueSignal )
        # dictionary with running CMs by ip { (IPCM,object) }
        self.IPcms = {}
        # dictionary with running cmts by ip { (IPCMTS,object) }
        self.IPcmts = {}
        # dictionary with running cmts
        self.cmts = {}
        # dictionary with running cms 
        self.cms = {}
        # dictionary with running cpes
        self.cpes = {}
        # dictionary with all running on the simulator
        self.runningDevices = {}

        self.name = "DeviceRunner"

    def run_cmts(self, cmts):
        if (cmts.ip == "0.0.0.0"):
            return False

        self.cmts[cmts.mac] = cmts
        self.IPcmts[cmts.ip] = self.runningDevices[cmts.ip] = cmts
        self.context = cmts 

        # cmts.ipDevices = self.ipDevices
        self.spawn( cmts , name=cmts.name )
        return True

    def run_cm(self, cm):
        cm.emulator = self

        if cm.mac in self.cms:
            return False 

        self.cms[cm.mac] = cm
        self.context = cm
        self.spawn( cm , name="CableModem")
        return True

    def run_cpe(self, cpe):
        cpe.emulator = self
        if cpe.mac in self.cpes:
            return False 

        self.cpes[cpe.mac] = cpe
        self.context = cpe
        self.spawn( cpe , name="CPE")
        return True

    def dispatch_message(self, message):
        device = None
        if (message.payload is not None) and (message.payload.haslayer('ARP')) and (message.payload.op == WHO_HAS):
            if self.runningDevices.has_key(message.payload.pdst):
                device = self.runningDevices[message.payload.pdst]
        else:
            device = self.cms.get(message.mac, None)

        #if (message.payload) and message.payload.haslayer('ARP')==False: print "LOG:Simulator::message received :",message.payload.show()
        if not device :
            device = self.cmts.get(message.mac, None)
            if not device :
                device = self.cpes.get(message.mac, None)

        if device :
            device.dispatch_message(message)
        else:
           SimulatorLogger.debug("There is no device to deliver message for mac %s", message.mac)

class Simulator(SocketServer.BaseRequestHandler):
    ''' Here is where everything starts '''

    def __init__(self):
        import cmdslistener
        # Queue for signal events.....
        self.queue = Queue.Queue()
        self.machine = RunningDevices( queueSignal=self.queue )
        self.simulatorStatus = RUNNING
        self.listener = cmdslistener.CmdsListener(5, 10003, self)
        
        self.signalCounter = 0

    def signal(self, message):
        signalQueue.put_nowait(message)

    def run(self):
        # Launch a thread for client commands processing
        self.listener.start()
        # Launch a thread for event timer
        self.startSimulator()

    def startSimulator(self):
        SimulatorLogger.info("#CMs to boot:%d",len(self.machine.cms))

        self.doLoop = True

        while self.doLoop:
            # retrieve signals from simulator signal queue
            message = self.get_new_message()

            #look for scheduled events...
            now = time.time()
            #leventTimers=sorted(eventTimers, key=lambda item: now - item.lTimer)
            eventTimers.sort(key=lambda item: now - item.lTimer, reverse=True)

            # remove all timer events to execute
            while (len(eventTimers)>0) and ((eventTimers[-1].lTimer - now) < 0):
                # remove timer from list
                tItem = eventTimers.pop()
                print "adding ",tItem.msg,"event for ",tItem.mac,tItem.msg
                signalQueue.put_nowait( simMessage(name=tItem.msg, mac=tItem.mac, payload=None) )

            if self.simulatorStatus:
                if message is not None:
                    if message.name == 'exit':
                        SimulatorLogger.info("Message received=EXIT. Leaving....")
                        self.doLoop = False
                    else:
                        SimulatorLogger.debug("Simulator new message::msg.mac=%s msg.name=%s" ,message.mac,message.name)
                        self.machine.dispatch_message(message)

        provisioned = 0  
        for mac,device in self.machine.cms.iteritems():
            if (device.ip != '0.0.0.0'):
                SimulatorLogger.debug("%s.....%s ProvTime=%d",mac,device.ip, device.cmTimers['dhcp_ack'] - device.cmTimers['dhcp_discover'])
                #print "\n",mac,"......",device.ip, " ProvTime=", device.cmTimers['dhcp_ack'] - device.cmTimers['dhcp_discover'],
                #if device.cmTimers.has_key('tftp_end') and device.cmTimers.has_key('tftp_start'):
                #    print " TFTP Time=",device.cmTimers['tftp_end'] - device.cmTimers['tftp_start'],
                provisioned+=1
            else:
                SimulatorLogger.debug("%s.....%s",mac,device.ip)

        SimulatorLogger.debug("Signals procesed in queue:%d",self.signalCounter)
        SimulatorLogger.info("#CM provisioned = %d\nSimulator Stats...",provisioned)
        for k,v in simulatorStats.getdata().iteritems():
            SimulatorLogger.info("%s.....%d",k,v)

    def get_new_message(self):
        message = None
        message = signalQueue.get()
        signalQueue.task_done()
        self.signalCounter+=1
        return message

    def add_cpe(self, cpe):
        return self.machine.run_cpe(cpe)

    def add_cm(self, cm):
        return self.machine.run_cm(cm)

    def add_cmts(self, cmts):
        return self.machine.run_cmts(cmts)


if __name__ == "__main__":
    # scapy basic configuration...
    bind_layers(UDP,BOOTP,sport=BOOTPS)
    conf.verb = 0 

    startTime = time.time()
    print "Simulation Start Time : ", time.ctime()
    simulator = Simulator()
    network = Network(simQueue=signalQueue)
    network.launch()
    
    
    #timerEvent.run()
    simulator.run()

    simuTime = time.time() - startTime
    print "Time Elapsed while Simulation :%.3f " % (simuTime)
    print "Stopping network...."
    network.stop()











    sys.exit(0)
