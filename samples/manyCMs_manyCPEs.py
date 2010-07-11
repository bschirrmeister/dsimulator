# Simulator Sample
# boot up some CMs, later boot up some CPEs ( PCs ). 
# Request to Simulator CMs provissioned with IP, then stop.
# Just edit the amount of virtual devices ( CMs ) to simulate setting the variable totalCM

# Here you can learn how to setup virtualCMTS -- CMD_SIMULATOR_ADDCMTS | CMD_SIMULATOR_SHOWCMTS
# Add CableModems for simulator --  CMD_SIMULATOR_ADDCM 
# Add CPEs for simulator --  CMD_SIMULATOR_ADDCPE
# retrieve CableModems status -- CMD_SIMULATOR_SHOWCMS
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
    cmd.id = CMD_SIMULATOR_STOP
    ans = simulator.sendCommand( cmd )
    print "Simulator stoped......."

    sys.exit(0)


if __name__ == "__main__":
    totalCM = totalCPE = 2
    cpeMacList = cmList = []

	# Setup the birdge with the ip where the simulator is running...
    simulator = api.SimulatorBridge('localhost',10003)
    print "Client connected....."

    try:
		# read clienttools.setupCMTS function signature to understand every parameter
        virtualCMTSMac = clienttools.setupCMTS('31.0.0.1','00:16:36:dd:fa:00', 'UBR 1000', '192.168.204.149', '00:0c:29:f4:c1:fa',simulator_ref=simulator) 
    except:
        stopSimulator(simulator, "Could not setup CMTS. Aborting")

    # generates a list of totalCM len, with uniques mac address and associate them to cmtsMac
    cmList = api.populateList( totalCM,virtualCMTSMac )

	# Every CM on cmList, will be assigned ("connected"), to CMTS with macaddress cmtsMac
    cmd = simuProtocol_pb2.clientCommand()
    cmd.id = api.CMD_SIMULATOR_ADDCM
    for device in cmList:
        pair = cmd.devices.add()
        pair.cmMac = device[0]
        pair.cmtsMac = device[1]

    # send them all to simulator....
    ans = simulator.sendCommand( cmd )
    if (ans.id == api.ANS_ERR): stopSimulatior(simulator, ans.msg )

    # now, add the CPEs to simulator
    cmd = simuProtocol_pb2.clientCommand()
    cmd.id = api.CMD_SIMULATOR_ADDCPE
    # we already have the CM mac on pair.cmMac, so need to add CPE Mac
    # for this, we use cmtsMac reg. 
    for device in cmList:
        pair = cmd.devices.add()
        pair.cmMac = device[0]
        pair.cmtsMac = 'cc:cc:cc'+ api.genmacaddress(3)    # should check for duplicates... 
        cpeMacList.append(pair.cmtsMac)

    # send them to simulator....
    ans = simulator.sendCommand( cmd )
    if (ans.id == api.ANS_ERR): stopSimulatior(simulator, ans.msg )

    # Start simulation....
    cmd.id = api.CMD_SIMULATOR_START
    ans = simulator.sendCommand( cmd )
    print "Simulator started......."

	# At this time, we have the simulator running, the virtual devices ( CMTS, cablemodems , CPEs)
	# exists on the simulator , but the devices are powered off. 

    startTime = time.time()

	# Lets power on every device and fire up a dhcp discover
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

    # power on all the CMs
    ans = simulator.sendCommand( msgscmd ) 

    # wait till totalCM ips a
    cmsWithIP = clienttools.waitforips(simulator, totalCM, api.CMD_SIMULATOR_GETAMOUNTCMS_WITH_IP, delayBetweenLoops=.2)

	# Lets power on every CPE and fire up a dhcp discover
    msgscmd = simuProtocol_pb2.clientCommand()
    msgscmd.id = api.CMD_SIMULATOR_SENDMSG
    for pc in cpeMacList:
        pair = msgscmd.devices.add()
        pair.cmMac = pc
        pair.cmtsMac = ''
        pair.msg = 'power_on'
        pair = msgscmd.devices.add()
        pair.cmMac = pc
        pair.cmtsMac = ''
        pair.msg = 'dhcp_discover'

    # power on all the CMs
    ans = simulator.sendCommand( msgscmd ) 

    k = raw_input("Press any key to stop simulation:")
    #print "Simulator stoped......."
    cmd.id = api.CMD_SIMULATOR_EXIT
    simulator.sendCommand( cmd )

    print "Simulation time :%.3fs" % (time.time() - startTime)
    print "Booted CM=%d. CM with IP assigned=%d" % (totalCM, cmsWithIP)
