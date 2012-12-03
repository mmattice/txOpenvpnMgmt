from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.python import log
from twisted.internet.task import LoopingCall
import sys
from txopenvpnmgmt.openvpn import Mgmt

class MgmtDataCollection(Mgmt):
    clientinfo = {}

    def connectionMade(self):
        self.ByteCount(60).addCallback(log.msg)
        self.Hold('release').addCallback(log.msg)
        if len(sys.argv) > 3:
            reactor.callLater(5, self.killhost, sys.argv[3])
        self.lc = LoopingCall(self.showtraffic)
        self.lc.start(300)

    def killhost(self, hostid):
        self.Kill(hostid).addCallback(log.msg)

    def established(self, clientnum, clientdata):
        print "client %i: %s" % (clientnum, clientdata['common_name'])
        cn = clientdata['common_name']
        self.clientinfo[cn] = clientdata

    def showtraffic(self):
        for cn, ci in self.clientinfo.iteritems():
            print "%-20s  %20i  %20i" % (cn, ci['traffic'][0], ci['traffic'][1])

class MgmtDataFactory(ClientFactory):
    protocol = MgmtDataCollection

log.startLogging(sys.stdout)
reactor.connectTCP(sys.argv[1],int(sys.argv[2]), MgmtDataFactory())
reactor.run()
