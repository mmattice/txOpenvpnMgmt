from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.python import log
from twisted.internet.task import LoopingCall
import sys
from txopenvpnmgmt.openvpn import Mgmt

from twisted.internet import error as twisted_error
from twistedsnmp import agent, agentprotocol, bisectoidstore
from twistedsnmp.pysnmpproto import v2c,v1,error

OB = {'IF-MIB::ifNumber' : '.1.3.6.1.2.1.2.1.0',
      'IF-MIB::ifIndex'  : '.1.3.6.1.2.1.2.2.1.1',
      'IF-MIB::ifDescr'  : '.1.3.6.1.2.1.2.2.1.2',
      'IF-MIB::ifType'   : '.1.3.6.1.2.1.2.2.1.3',
      'IF-MIB::ifAdminStatus' : '.1.3.6.1.2.1.2.2.1.7',
      'IF-MIB::ifOperStatus' : '.1.3.6.1.2.1.2.2.1.8',
      'IF-MIB::ifInOctets' : '.1.3.6.1.2.1.2.2.1.10',
      'IF-MIB::ifOutOctets' : '.1.3.6.1.2.1.2.2.1.16',
      'IF-MIB::ifName' : '.1.3.6.1.2.1.31.1.1.1.1',
      }

class MgmtDataCollection(Mgmt):
    clientinfo = {}

    def connectionMade(self):
        self.ds = self.factory.datastore
        self.ByteCount(5).addCallback(log.msg)
        self.Hold('release').addCallback(log.msg)
        if len(sys.argv) > 3:
            reactor.callLater(5, self.killhost, sys.argv[3])

    def killhost(self, hostid):
        self.Kill(hostid).addCallback(log.msg)

    def sv(self, oidname, index, value):
        oid = '%s.%i' % (OB[oidname], index)
        #log.msg("Setting %s to %s" % (oid, value))
        self.ds.setValue(oid, value)

    def addoid(self, cn):
        num = int(cn[3:7])
        self.sv('IF-MIB::ifIndex', num, num)
        self.sv('IF-MIB::ifDescr', num, 'tunnel to %s' % (cn,))
        self.sv('IF-MIB::ifType', num, 1)
        self.sv('IF-MIB::ifAdminStatus', num, 1)
        self.sv('IF-MIB::ifOperStatus', num, 1)
        self.sv('IF-MIB::ifName', num, cn)

    def updateoctets(self, cn, inoctets, outoctets):
        num = int(cn[3:7])
        self.sv('IF-MIB::ifInOctets', num, v2c.Counter32(inoctets))
        self.sv('IF-MIB::ifOutOctets', num, v2c.Counter32(outoctets))

    def established(self, clientnum, clientdata):
        log.msg("client %i connected: %s" % (clientnum, clientdata['common_name']))
        cn = clientdata['common_name']
        num = int(cn[3:7])
        self.clientinfo[cn] = clientdata
        count = self.ds.getExactOID(OB['IF-MIB::ifNumber'])[1]
        self.ds.setValue(OB['IF-MIB::ifNumber'], max(count, num + 1))
        self.addoid(cn)

    def disconnect(self, clientnum, clientdata):
        log.msg("client %i disconnected: %s" % (clientnum, clientdata['common_name']))
        num = int(cn[3:7])
        self.sv('IF-MIB::ifOperStatus', num, 0)

    def connect(self, clientnum, clientdata):
        pass

    def reauth(self, clientnum, clientdata):
        pass

    def _handle_CLIENT(self, data):
        fields = data.split(',')
        infotype = fields.pop(0)
        if infotype == 'ESTABLISHED':
            self._cli_num = int(fields[0])
            self._handler = self.established
            if self._cli_num not in self.clients:
                self.clients[self._cli_num] = {}
        elif infotype == 'ENV':
            if '=' in fields[0]:
                key, value = fields[0].split('=', 1)
                self.clients[self._cli_num][key] = value
            elif fields[0] == 'END':
                if self._handler:
                    self._handler(self._cli_num, self.clients[self._cli_num])
                self._cli_num = None
                self._handler = None
        elif infotype == 'DISCONNECT':
            self._cli_num = int(fields[0])
            self._handler = self.disconnect
        elif infotype in ('CONNECT', 'REAUTH'):
            self._cli_num, kid = map(int, fields)
            if self._cli_num not in self.clients:
                self.clients[self._cli_num] = {}
            self.ClientAuthNT(self._cli_num, kid)

    def _handle_BYTECOUNT_CLI(self, data):
        cli_num, bytesin, bytesout = map(int,data.split(','))
        if cli_num not in self.clients:
            self.clients[cli_num] = {}
        self.clients[cli_num]['traffic'] = (bytesin, bytesout)
        if 'common_name' in self.clients[cli_num]:
            self.updateoctets(self.clients[cli_num]['common_name'], bytesin, bytesout)

class MgmtDataFactory(ReconnectingClientFactory):
    protocol = MgmtDataCollection

    def __init__(self, datastore):
        self.datastore = datastore
        log.msg( self.datastore )

log.startLogging(sys.stdout)
baseoids = {
    '.1.3.6.1.2.1.1.1.0': 'Openvpn Bandwidth Monitor',
    '.1.3.6.1.2.1.1.2.0': v2c.ObjectIdentifier('.1.3.6.1.4.1.88.3.1'),
    '.1.3.6.1.2.1.1.3.0': 0,
    '.1.3.6.1.2.1.1.4.0': "responsible@example.com",
    '.1.3.6.1.2.1.1.5.0': "host openvpn",
    '.1.3.6.1.2.1.1.6.0': "location",
    OB['IF-MIB::ifNumber']: 0,
    }

datastore = bisectoidstore.BisectOIDStore(OIDs = baseoids,)
agentprotocol = agentprotocol.AgentProtocol(snmpVersion = 'v2c',
                                            agent = agent.Agent(datastore),
                                            )
agentObject = reactor.listenUDP(1161, agentprotocol)

reactor.connectTCP(sys.argv[1],int(sys.argv[2]), MgmtDataFactory(datastore))
reactor.run()
