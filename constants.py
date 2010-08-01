# Here you will find constants and common settings like logging levels, 
# Developed by Matias Torchinsky ( tmatias@gmail.com )

import logging
import collections
import Queue
from scapy.all import *
# simulator stats module
import stats

# list for timer events.....
eventTimers = []

signalQueue = Queue.Queue()
simulatorStats = stats.SimulatorStats()


# define logger sections
logging.basicConfig()

CmtsLogger = logging.getLogger("CMTS")
CmtsLogger.setLevel(logging.INFO)
statechartLogger = logging.getLogger("STATECHART")
statechartLogger.setLevel(logging.INFO)
arpLogger = logging.getLogger("ARP")
arpLogger.setLevel(logging.INFO)
icmpLogger = logging.getLogger("ICMP")
icmpLogger.setLevel(logging.INFO)
dhcpLogger = logging.getLogger("DHCP")
dhcpLogger.setLevel(logging.INFO)
networkLogger = logging.getLogger("NETWORK")
networkLogger.setLevel(logging.INFO)
sniffLogger = logging.getLogger("SNIFFER")
sniffLogger.setLevel(logging.INFO)
SimulatorLogger = logging.getLogger("SIMULATOR")
SimulatorLogger.setLevel(logging.INFO)
tftpLogger = logging.getLogger("TFTP")
tftpLogger.setLevel(logging.INFO)

# Simulator states
STOPPED=0
RUNNING=10

# ICMP CONSTANTS
ECHO_REQUEST=8
ECHO_REPLY=0

# DHCP CONSTANTS
INIT_BOOT=20
DISCOVER=30
OFFER=40
REQUEST=50
ACK=60
BOOTPS=67
BOOTPC=68

# TFTP CONSTANT
TFTP_PORT = 69

#ARP CONSTANTS
WHO_HAS=1
IS_AT=2

ETH_GATEWAY = ''

#Event Timers IDs
TE_DHCP_RENEW = 100
