# VERY basic accounting class
# Developed by Matias Torchinsky ( tmatias@gmail.com )


class SimulatorStats:
    def __init__(self):
        self.stats = {}
        self.stats['DHCP_DISCOVER'] = 0
        self.stats['DHCP_OFFER'] = 0
        self.stats['DHCP_REQUEST'] = 0
        self.stats['DHCP_ACK'] = 0
        self.stats['DHCP_RENEW'] = 0

    def reset(self):
        for element in self.stats.iteritems():
            self.stats[element] = 0

    def increment(self, key):
        if self.stats.has_key(key) == True:
            self.stats[key]+=1
            return self.stats[key]
        # wrong key
        return -1

    def getitem(self, key):
        if self.stats.has_key(key) == True:
            return self.stats[key]
        # if wrong key
        return -1

    def getdata(self):
        return self.stats
