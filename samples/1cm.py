# Simulator Sample
# boot up 1 CM. Request to Simulator CMs provissioned with IPs, then stop.

# Here you can learn how to setup virtualCMTS -- CMD_SIMULATOR_ADDCMTS,CMD_SIMULATOR_SHOWCMTS
# Add CableModems to simulator --  CMD_SIMULATOR_ADDCM 
# retrieve CableModems status  --  CMD_SIMULATOR_SHOWCMS
# Send commands to Simulator via CMD_SIMULATOR_SENDMSG

# enjoy it ! 
# Matias Torchinsky (matt) - tmatias@gmail.com

from api import *
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


if __name__ == "__main__":
    totalCM = 1
    cmList = []

	# Setup the birdge with the ip where the simulator is running...
    simulator = SimulatorBridge('localhost',10003)
    print "Client connected....."

    try:
		# read clienttools.setupCMTS function signature to understand every parameter
        cmtsMac = clienttools.setupCMTS('31.0.0.1','00:16:36:dd:fa:00', 'UBR 1000', '192.168.204.149', '00:0c:29:f4:c1:fa',simulator_ref=simulator) 
        # generates a list of totalCM len, with uniques mac address. i
        cmList = populateList(totalCM,cmtsMac)
    except:
        stopSimulator(simulator, "Could not setup CMTSs. Aborting")

	# Every CM on cmList, will be assigned ( "connected" ), to CMTS with macaddress cmtsMac
    cmd = simuProtocol_pb2.clientCommand()
    cmd.id = CMD_SIMULATOR_ADDCM
    for device in cmList:
        pair = cmd.devices.add()
        pair.cmMac = device[0]
        pair.cmtsMac = device[1]

    # send them all to simulator....
    ans = simulator.sendCommand( cmd )
    if (ans.id == ANS_ERR): stopSimulatior(simulator, ans.msg )

    # request for a list of CM registered on the Simulator
    cmd.id = CMD_SIMULATOR_SHOWCMS
    ans = simulator.sendCommand( cmd )
    print "CMs registered for booting :",len(ans.macCms)

    # Start simulation....
    cmd.id = CMD_SIMULATOR_START
    ans = simulator.sendCommand( cmd )
    print "Simulator started......."

	# At this time, we have the simulator running, the virtual CMTS and virtual cablemodems 
	# exists on the simulator , but the devices are powered off. 

    startTime = time.time()

	# Lets power on evry device and fire up a dhcp discover
    msgscmd = simuProtocol_pb2.clientCommand()
    msgscmd.id = CMD_SIMULATOR_SENDMSG
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

    cmsWithIP = clienttools.waitforips(simulator, totalCM, CMD_SIMULATOR_GETAMOUNTCMS_WITH_IP)

    print "Simulation time :%.3fs" % (time.time() - startTime)
    print "Booted CM=%d. CM with IP assigned=%d" % (totalCM, cmsWithIP)
    k = raw_input("Press any key to stop simulation:")
    print "Simulator stoped......."

    cmd.id = CMD_SIMULATOR_EXIT

    simulator.sendCommand( cmd )
