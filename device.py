# Network device abstraction
# Developed by Matias Torchinsky ( tmatias@gmail.com )

class Device(object):
    ip = "0.0.0.0"
    mac = None
    nexthop = None
    deviceKind = ''
    deviceDescr = ''
