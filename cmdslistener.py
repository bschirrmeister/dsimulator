# This class is responsable for listening commands from clients 
# and do some processing with commands
# Developed by Matias Torchinsky ( tmatias@gmail.com )

from constants import *
import simuProtocol_pb2

import socket
import select
import threading

from api import *
from simulator import *
from cpe import CPE
#from cpe_buggy import CPE
from cablemodem import CM

class CmdsListener(threading.Thread):
    def __init__(self, maxclients=5, lport=10000, simulator = None):
        # Set up the server:
        self.server = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind (( '', lport))
        self.server.listen(maxclients)
        threading.Thread.__init__(self)
        self.simulator = simulator
       
    def processRequest( self, clientsock ):
        # 1st Receive fixed packet length 
        msg = ''
        while len(msg) < 4:
            chunk = clientsock.recv(4-len(msg))
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk

        res = struct.unpack('<i',msg)
        SimulatorLogger.debug("Simulator will receive %d bytes from client", res[0])

        # read data from network
        cmd = simuProtocol_pb2.clientCommand()
        cmd.id = simuProtocol_pb2.cmdID.CMD_NOCMD
 
        networkData = ''
        while len(networkData) < res[0]:
            rawData = clientsock.recv(res[0] - len(networkData) )
            if rawData=='':
                raise RuntimeError, "socket connection broken"
            networkData+=rawData

        cmd.ParseFromString(networkData)

        simAnswer = simuProtocol_pb2.simulatorAnswer()

        if cmd.id == CMD_SIMULATOR_START:
            SimulatorLogger.info("SIMULATOR_START cmd received...")
            self.simulator.simulatorStatus = RUNNING
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_FLUSHCMS:
            SimulatorLogger.info("SIMULATOR_FLUSHCMS cmd received...")
            self.simulator.machine.cms = {}
            self.simulator.machine.IPcms = {}
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_FLUSHCMTS:
            SimulatorLogger.info("SIMULATOR_FLUSHCMTS cmd received...")
            self.simulator.machine.IPcmts = {}
            self.simulator.machine.cmts = {}
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_STOP:
            SimulatorLogger.info("SIMULATOR_STOP cmd received...")
            self.simulator.simulatorStatus = STOPPED
            self.simulator.machine.cms = {}
            self.simulator.machine.IPcms = {}
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_EXIT:
            SimulatorLogger.info("SIMULATOR_EXIT cmd received...")
            self.simulator.simulatorStatus = STOPPED
            self.simulator.doLoop=False
            self.simulator.signal( Message('exit',mac='00:00:00:00:00:00') )
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_GETCMIP:
            """ return for a given macaddres (specified in cmMac), it's IP in ipCM"""    
            SimulatorLogger.info("SIMULATOR_GETCMIP cmd received...")
            item = cmd.devices._values[0]
            if ( self.simulator.machine.cms.has_key(item.cmMac) ):
                dev =  self.simulator.machine.cms[ item.cmMac ]
                simAnswer.ipCM = dev.ip
                SimulatorLogger.info("SIMULATOR_GETCMIP IP assigned=%s",simAnswer.ipCM)
                simAnswer.id = ANS_OK
            else:
                SimulatorLogger.error("SIMULATOR_GETCMIP did not find device %s",item.cmMac)
                simAnswer.id = ANS_ERR
            #for index in cmd.devices._values:
            #    SimulatorLogger.debug("Retrieving IP(%s)", index.cmMac)
        elif cmd.id == CMD_SIMULATOR_SHOWCMS:
            """ return a list of macaddres registered into simulator """
            SimulatorLogger.info("SIMULATOR_SHOWCMS cmd received...")
            for mac in self.simulator.machine.cms.iterkeys():
                simAnswer.macCms.append(mac)
            simAnswer.id = ANS_SHOWCMS
        elif cmd.id == CMD_SIMULATOR_SHOWCMS_DETAILED:
            SimulatorLogger.debug("SIMULATOR_SHOWCMS_DETAILED cmd received...")
            for mac,dev in self.simulator.machine.cms.iteritems():
                item = simAnswer.cablemodems.add()
                item.cmMac = mac
                item.cmtsMac = ''
                item.ip = dev.ip
                if dev.cmTimers.has_key('dhcp_discover'): item.timer_dhcp_discover = dev.cmTimers['dhcp_discover']
                if dev.cmTimers.has_key('dhcp_offer'): item.timer_dhcp_offer    = dev.cmTimers['dhcp_offer']
                if dev.cmTimers.has_key('dhcp_request'): item.timer_dhcp_request  = dev.cmTimers['dhcp_request']
                if dev.cmTimers.has_key('dhcp_ack'): item.timer_dhcp_ack      = dev.cmTimers['dhcp_ack']
            simAnswer.id = ANS_SHOWCMS_DETAILED
        elif cmd.id == CMD_SIMULATOR_GETAMOUNTCMS_WITH_IP:
            SimulatorLogger.debug("SIMULATOR_GETAMOUNTCMS_WITH_IP cmd received...")
            cmsWithIP = 0
            for mac,dev in self.simulator.machine.cms.iteritems():
                if (dev.ip != "0.0.0.0"): cmsWithIP+=1

            simAnswer.ipCM = str(cmsWithIP)
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_GETAMOUNTCMS:
            SimulatorLogger.info("SIMULATOR_GETAMOUNTCMS cmd received...")
            simAnswer.ipCM = str(len(self.simulator.machine.cms))
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_SENDMSG:
            SimulatorLogger.debug("SIMULATOR_SENDMSG cmd received...")
            for index in cmd.devices._values:
                SimulatorLogger.debug("%s :: signal=%s", index.cmMac,index.msg)
                self.simulator.signal( Message(index.msg,mac=index.cmMac) )
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_GETSTATUS_TFTP:
            cmCounter = 0
            for mac,dev in self.simulator.machine.cms.iteritems():
                if (dev.tftp.bootfileSize > 0):
                    cmCounter+=1

            self.answer.msg = cmCounter
            self.answer.setCmdId(ANS_GETSTATUS_TFTP)
            # print "SHOWCMTS ANS =::",self.answer.answer
        elif cmd.id == CMD_SIMULATOR_GETSTATUS:
            cmCounter = 0     
            for mac,dev in self.simulator.machine.cms.iteritems():
                if (dev.ip != "0.0.0.0"):
                    cmCounter+=1
                
            self.answer.msg = cmCounter
            self.answer.setCmdId(ANS_GETSTATUS)
            # print "SHOWCMTS ANS =::",self.answer.answer
        elif cmd.id == CMD_SIMULATOR_SHOWCMTS:
            SimulatorLogger.info("SIMULATOR_SHOWCMTS cmd received...")
            for mac in self.simulator.machine.cmts.iterkeys():
                simAnswer.macCmts.append(mac)

            simAnswer.id = ANS_SHOWCMTS

        elif cmd.id == CMD_SIMULATOR_ADDCMTS:
            for index in cmd.CMTSDevices._values:
                newcmts = cmts.CMTS(CMTSName=index.cmtsName,macaddress=index.cmtsMac,ip=index.cmtsIP)
                cmtsOperation = self.simulator.add_cmts( newcmts )
                SimulatorLogger.info("SIMULATOR_ADDCMTS cmd received (%s:%s)=%s",index.cmtsMac,index.cmtsIP,cmtsOperation)
                if ( cmtsOperation and index.helperAddressIP ):
                    # turn on CMTS ( by default CMTS will be on )
                    self.simulator.signal( Message("power_on",mac=index.cmtsMac) )
                    SimulatorLogger.info("SIMULATOR_ADDCMTS setting Helper Address Parameters (%s:%s)",index.helperAddressIP,index.helperAddressMAC)
                    opResult = newcmts.setDhcpServer(index.helperAddressIP,index.helperAddressMAC)
                else:
                    opResult = ANS_ERR
                    SimulatorLogger.error("Invalid CM Mac(%s). CPE %s could not be registered",index.cmMac,index.cmMac)
                
            simAnswer.id = opResult
        elif cmd.id == CMD_SIMULATOR_ADDCPE:
            for index in cmd.devices._values:
                if self.simulator.machine.cms.has_key(index.cmMac): # if the CM associated to CPE exists 
                    cm_cpe = self.simulator.machine.cms[ index.cmMac ]
                    # CPE mac travels on cmtsMac field
                    opResult = self.simulator.add_cpe( CPE(index.cmtsMac, cm=cm_cpe) )
                else:
                    SimulatorLogger.error("Invalid CM Mac(%s). CPE %s could not be registered",index.cmMac,index.cmtsMac)

            simAnswer.id = ANS_ADDCPE
        elif cmd.id == CMD_SIMULATOR_GETAMOUNTCPES_WITH_IP:
            SimulatorLogger.debug("SIMULATOR_GETAMOUNTCPES_WITH_IP cmd received...")
            cmsWithIP = 0
            for mac,dev in self.simulator.machine.cpes.iteritems():
                if (dev.ip != "0.0.0.0"): cmsWithIP+=1

            simAnswer.ipCM = str(cmsWithIP)
            simAnswer.id = ANS_OK
        elif cmd.id == CMD_SIMULATOR_ADDCM:
            SimulatorLogger.info("Cmd received:ADDCM")

            for index in cmd.devices._values:
                if self.simulator.machine.cmts.has_key(index.cmtsMac):
                    localcmts = self.simulator.machine.cmts[ index.cmtsMac ]
                    opResult = self.simulator.add_cm( CM( index.cmMac, cmts=localcmts) )
                    #self.answer.answer.append( (index.cmMac,opResult) )
                else:
                    pass
                    #self.answer.answer.append( (data.maclist[index][0], False) )
                    #self.answer.msg="Did not find CMTS for association with CM"
                    #self.answer.setCmdId(ANS_ERR)

            simAnswer.id = ANS_ADDCM

        else:
            SimulatorLogger.error("Unknown cmd received (%d)",data.cmdid)

        #clientsock.sendall( simAnswer.SerializeToString() )

        answerSize = len(simAnswer.SerializeToString())
        res = struct.pack('<i', answerSize)
        #SimulatorLogger.debug("client must received %d bytes", answerSize)
        clientsock.send(res)

        totalsent = 0
        data = simAnswer.SerializeToString()
        while totalsent < answerSize:
            sent = clientsock.send(data[totalsent:])
            if sent == 0:
                raise RuntimeError, "socket connection broken"
            totalsent = totalsent + sent

    def run ( self ):
        SimulatorLogger.info('waiting for connections....')
        while True:
            self.answer = SimCmd()
            inputready,outputready,exceptready = select.select([self.server],[],[])

            for data in inputready:
                # handle the server socket 
                clientsock, addr = self.server.accept()
                # input.append(clientsock)
                self.processRequest( clientsock )
