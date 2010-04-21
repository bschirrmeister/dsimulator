# Simulator Sample
# Measures time in seconds for a given CM to get an IP.

# Here you can learn how to setup virtualCMTS -- CMD_SIMULATOR_ADDCMTS | CMD_SIMULATOR_SHOWCMTS
# Add CableModems for simulatior --  CMD_SIMULATOR_ADDCM 
# retrieve CableModems status -- CMD_SIMULATOR_SHOWCMS
# Send commands to SImulator via CMD_SIMULATOR_SENDMSG

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
    sys.exit(0)

def turnOnDevices(cmList, simulator):
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

if __name__ == "__main__":
    totalCM = 10
    cmList = []

	# Setup the birdge with the ip where the simulator is running...
    simulator = SimulatorBridge('192.168.204.149',10003)
    print "Client connected....."

    try:
		# read clienttools.setupCMTS function signature to understand every parameter
        cmtsMac = clienttools.setupCMTS('31.0.0.1','00:16:36:dd:fa:00', 'UBR 1000', '192.168.204.149', '00:0c:29:f4:c1:fa',simulator_ref=simulator) 
    except:
        stopSimulator(simulator, "Could not setup CMTS. Aborting")

    # generates a list of totalCM len, with uniques mac address
    cmList = populateList(totalCM,cmtsMac)
        
    cmd = simuProtocol_pb2.clientCommand()
    cmd.id = CMD_SIMULATOR_ADDCM
    for device in cmList:
        pair = cmd.devices.add()
        pair.cmMac = device[0]
        pair.cmtsMac = device[1]

    # send them all to simulator....
    ans = simulator.sendCommand( cmd )
    if (ans.id == ANS_ERR): stopSimulatior(simulator, ans.msg )

    # Start simulation....
    cmd.id = CMD_SIMULATOR_START
    ans = simulator.sendCommand( cmd )
    print "Simulator started......."

    # When we really starts simulation process
    startTime = time.time()

	# Lets power on evry device and fire up a dhcp discover
    turnOnDevices(cmList, simulator)

    cmsWithIP = clienttools.waitforips(simulator, totalCM, CMD_SIMULATOR_GETAMOUNTCMS_WITH_IP)
    print "Finishing Simulation. Elapsed time :%.3fs" % (time.time() - startTime)

    cmd.id = CMD_SIMULATOR_SHOWCMS_DETAILED
    ans = simulator.sendCommand( cmd )

    # now iterate over all CMs and print timers
    for cm in ans.cablemodems._values:
        if (cm.ip != "0.0.0.0"):
            print "%s::%s ackTime - discoverTime =%.3fs" % (cm.cmMac,cm.ip,cm.timer_dhcp_ack - cm.timer_dhcp_discover)

    print "Booted CM=%d. CM with IP assigned=%d" % (totalCM, cmsWithIP)
    print "Simulator stoped......."

    cmd.id = CMD_SIMULATOR_EXIT
    ans = simulator.sendCommand( cmd )
