# usefull functions for client implementations

# enjoy it. 
# Matias Torchinsky ( tmatias@gmail.com ) 

from api import *
import time
import simuProtocol_pb2

def setupCMTS(cmtsIP, cmtsMac, cmtsName, helperAddress, DHCPMac=None , simulator_ref = None):
    """ Setup the CMTS to be used during this simulation.

    cmtsIP          : The IP for yor CMTS ( be aware of routing issues). ( yeap, is virtual )
    cmtsMac         : the macaddress for your CMTS. ( also virtual )
	cmtsName		: name of your virtual CMTS
    helperAddress   : Where the CMTS should resend the unicast packets.( DHCP Server IP )
    DHCPMac         : if DHCP server and simulator are on the same network do not need set anything (arp will do the magic).  In other case, need to set the MacAddres
    simulator_ref   : simulator reference.
    """
    # Get active CMTSs
    cmd = simuProtocol_pb2.clientCommand()
    # request for a lists of CMTS
    cmd.id = CMD_SIMULATOR_SHOWCMTS
    ans = simulator_ref.sendCommand( cmd )
    if ( len(ans.macCmts._values) > 0 ):
        # mean we have at least one active CMTS    
        print "Active CMTSs :",cmtsMac
        return ans.macCmts._values[0]
    else:
        print "No active CMTS. adding ...", cmtsMac,cmtsIP,cmtsName,helperAddress
        # building a command for adding a CMTS
        cmd.id = CMD_SIMULATOR_ADDCMTS
        item = cmd.CMTSDevices.add()
        item.cmtsMac = cmtsMac
        item.cmtsIP = cmtsIP
        item.cmtsName = cmtsName
        item.helperAddressIP = helperAddress
        item.helperAddressMAC = DHCPMac


        ans = simulator_ref.sendCommand( cmd )

        if ( ans.id != ANS_OK ):
            print 'Error addind CMTS'
            raise ValueError
        else:
            print 'CMTS Added succesfully'
            return cmtsMac


def waitforips(simulator, totalCMs, devicecounter, delayBetweenLoops=.1, loops=40):
    cmsWithIP = 0
    noChangeLoop = 0
    cmd = simuProtocol_pb2.clientCommand()
    cmd.id = devicecounter
    while True:
        ans = simulator.sendCommand( cmd )
        iIpCM = int(ans.ipCM)
        if (cmsWithIP < iIpCM):
            noChangeLoop = 0
            cmsWithIP = iIpCM
            print "devices with IP",ans.ipCM
        else:
            noChangeLoop+=1

        if ( iIpCM  == totalCMs) or (noChangeLoop > loops):
            break

        time.sleep(delayBetweenLoops)

    return cmsWithIP
