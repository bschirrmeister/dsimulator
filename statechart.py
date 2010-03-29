import sys
import random
from constants import *

class State(object):
    def __init__(self, ctx=None, parent=None, qSignal=None ):
        self.sub_states = []
        self.parent = parent
        self.qSignal = qSignal
        self.context = ctx
        self.names = {}

    def spawn(self, state, name=None):
        self.sub_states.append((name, state))
        self.names[name]=state
        state.context = self.context
        state.parent = self
			
    def __getitem__(self, key):
        print self.names
        return self.names[key]

    def dispatch_message(self, message):
        self.op = False
        handler = getattr(self, "on_"+message.name, None)

        # XXX just debuging... should be removed
        if handler is None:
            statechartLogger.debug("LOG %s cant handle message %s (id=%d)" ,self.__class__.__name__, message.name, message.id)

        my_next = self
        if handler is not None:
            statechartLogger.debug("handler found !")
            my_next = handler(message)
            assert(my_next is not None, "None handler for current message")
            if my_next != self:
                my_next.context = self.context
                my_next.parent = self

            # stop recursion
            return my_next, True

        new_states = []

        for name, state in self.sub_states:
            if self.op == False:
                next, self.op = state.dispatch_message(message)
            else:
                next = state

            self.names[name]=next
            new_states.append((name, next))

        self.sub_states = new_states
        return my_next, self.op

    def show(self, depth=0):
        print " "*(depth*4), "-",self.__class__.__name__,
        if depth==1:
            print "(%s - %s)" % (self.context.mac, self.context.ip)
        else:
            print ""

        for n, s in self.sub_states:
            s.show(depth+1)

    def show_pendingACK(self, depth=0):
        if depth==1 and self.context.ip=="0.0.0.0":
            print "(%s - %s)" % (self.context.mac, self.context.ip)

        for n,s in self.sub_states:
            s.show_pendingACK(depth+1)

    def signal(self, message , sigqueue):
        assert(message is None, "Trying to insert null message into signal queues")
        sigqueue.put_nowait(message)

class Message(object):
    def __init__(self, name, mac=None, payload=None):
        self.mac = mac
        self.name = name
        self.payload = payload
        self.id = random.randint(0,1000)
