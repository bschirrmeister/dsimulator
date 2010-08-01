# Simulator Sample
# boot up 1 CM. Request to Simulator CMs provissioned with IPs, then stop.

# Here you can learn how to setup virtualCMTS -- CMD_SIMULATOR_ADDCMTS,CMD_SIMULATOR_SHOWCMTS
# Add CableModems to simulator --  CMD_SIMULATOR_ADDCM 
# retrieve CableModems status  --  CMD_SIMULATOR_SHOWCMS
# Send commands to Simulator via CMD_SIMULATOR_SENDMSG

# enjoy it ! 
# Matias Torchinsky (matt) - tmatias@gmail.com

import api
import time
import clienttools
import simuProtocol_pb2

def stopSimulator( simualtor, msg=None):
    """ stop simulator : Stop simulator and quits."""
    
    if ( msg ): print "Error reported:",msg

    cmd = simuProtocol_pb2.clientCommand()
    cmd.id = api.CMD_SIMULATOR_STOP
    ans = simulator.sendCommand( cmd )
    print "Simulator stoped......."


if __name__ == "__main__":
    totalCM = 1
    totalCPEs = 1
    cmList = []

    simulator = api.SimulatorBridge('localhost',10003)
    print "Client connected....."

    try:
        #cmtsMac = clienttools.setupCMTS('31.0.0.1','00:16:36:dd:fa:00', 'UBR 1000', '192.168.5.139', '00:0c:29:f4:c1:fa',simulator_ref=simulator) 
        #cmtsMac = clienttools.setupCMTS('31.0.0.1','00:16:36:dd:fa:00', 'UBR 1000', '192.168.204.153', '00:0c:29:fb:fa:46',simulator_ref=simulator) 
        cmtsMac = clienttools.setupCMTS('31.0.0.1','00:16:36:dd:fa:00', 'UBR 1000', '192.168.204.149', '00:0c:29:f4:c1:fa',simulator_ref=simulator) 
        # generates a list of #totalCM, with uniques mac address. Every CM on this list
        # will be assigned ( "connected" ), to CMTS specified on cmtsMac
        cmList = api.populateList(totalCM, cmtsMac)
    except:
        stopSimulator(simulator, "Could not setup CMTSs. Aborting")

    # Add a CM to simulator
    cmd = simuProtocol_pb2.clientCommand()
    cmd.id = api.CMD_SIMULATOR_ADDCM
    pair = cmd.devices.add()
    pair.cmMac = cmList[0][0]
    pair.cmtsMac = cmList[0][1]
    # send them to simulator....
    ans = simulator.sendCommand( cmd )
    if (ans.id == api.ANS_ERR): stopSimulatior(simulator, ans.msg )

    # now, add a CPE to simulator
    cmd.id = api.CMD_SIMULATOR_ADDCPE
    # we already have the CM mac on pair.cmMac, so need to add CPE Mac
    # for this, we use cmtsMac reg. 
    pair.cmtsMac = 'cc:cc:cc:cc:01:01' 
    # send them to simulator....
    ans = simulator.sendCommand( cmd )
    if (ans.id == api.ANS_ERR): stopSimulatior(simulator, ans.msg )

    # Start simulation....
    cmd.id = api.CMD_SIMULATOR_START
    ans = simulator.sendCommand( cmd )
    print "Simulator started......."

    startTime = time.time()

    msgscmd = simuProtocol_pb2.clientCommand()
    msgscmd.id = api.CMD_SIMULATOR_SENDMSG
    for cm in cmList:
        pair = msgscmd.devices.add()
        pair.cmMac = cm[0]
        pair.cmtsMac = ''
        pair.msg = 'power_on'
        pair = msgscmd.devices.add()
        pair.cmMac = cm[0]
        pair.cmtsMac = ''
        pair.msg = 'dhcp_discover'

    ans = simulator.sendCommand( msgscmd )

    cmsWithIP = clienttools.waitforips(simulator, totalCM, api.CMD_SIMULATOR_GETAMOUNTCMS_WITH_IP)

    # now, turn on the CPE
    msgscmd = simuProtocol_pb2.clientCommand()
    msgscmd.id = api.CMD_SIMULATOR_SENDMSG
    pair = msgscmd.devices.add()
    pair.cmMac = 'cc:cc:cc:cc:01:01' 
    pair.cmtsMac = ''
    pair.msg = 'power_on'
    pair = msgscmd.devices.add()
    pair.cmMac = 'cc:cc:cc:cc:01:01' 
    pair.cmtsMac = ''
    pair.msg = 'dhcp_discover'
    # send them to simulator....
    ans = simulator.sendCommand( msgscmd )
    if (ans.id == api.ANS_ERR): stopSimulatior(simulator, ans.msg )

    cpesWithIP = clienttools.waitforips(simulator, totalCPEs, api.CMD_SIMULATOR_GETAMOUNTCPES_WITH_IP)

    print "Simulation time :%.3fs" % (time.time() - startTime)
    print "Booted CM=%d. Devices with IP assigned=%d" % (totalCM, cmsWithIP+cpesWithIP)
    k = raw_input("Press any key to stop simulation:")
    print "Simulator stoped......."


    try:
        cmd.id = api.CMD_SIMULATOR_EXIT
        simulator.sendCommand( cmd )
    except:
        pass
