from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred
from twisted.python import log

class Mgmt(LineReceiver):
    _defs = []
    clients = {}
    _cli_num, _cli_kid, _handler = None, None, None
    verbose = False

    def lineReceived(self, line):
        if self.verbose:
            print line
        if line[0] == '>':
            try:
                infotype, data = line[1:].split(':', 1)
                infotype = infotype.replace('-','_')
            except Exception, msg:
                print "failed to parse '%r': %s" % (line, msg)
                raise
            m = getattr(self, '_handle_%s' % infotype, None)
            if m:
                try:
                    m(data)
                except Exception, msg:
                    print "Failure in _handle_%s: %s" % (infotype, msg)
            else:
                self._handle_unknown(infotype, data)
        else:
            status, data = line.split(': ', 1)
            if status in ('ERROR', 'SUCCESS'):
                d = self._defs.pop(0)
                if status == 'SUCCESS':
                    d.callback(line)
                else:
                    d.errback(line)

    def _handle_unknown(self, infotype, data):
        log.msg('Recieved unhandled infotype %s with data %s' % (infotype, data))

    def _handle_BYTECOUNT(self, data):
        pass

    def _handle_BYTECOUNT_CLI(self, data):
        cli_num, bytesin, bytesout = map(int,data.split(','))
        if cli_num not in self.clients:
            self.clients[cli_num] = {}
        self.clients[cli_num]['traffic'] = (bytesin, bytesout)

    def _handle_CLIENT(self, data):
        fields = data.split(',')
        infotype = fields.pop(0)
        if infotype in ('ESTABLISHED', 'DISCONNECT', 'CONNECT', 'REAUTH'):
            self._cli_num, self._cli_kid = int(fields[0]), None
            if len(fields) > 1:
                self._cli_kid = int(fields[1])
            self._handler = getattr(self, infotype.lower(), None)
            if self._cli_num not in self.clients:
                self.clients[self._cli_num] = {}
        elif infotype == 'ENV':
            if '=' in fields[0]:
                key, value = fields[0].split('=', 1)
                self.clients[self._cli_num][key] = value
            elif fields[0] == 'END':
                if self._handler:
                    self._handler(self._cli_num, self._cli_kid, self.clients[self._cli_num])
                self._cli_num, self._cli_kid, self._handler = None, None, None

    def _handle_ECHO(self, data):
        pass

    def _handle_FATAL(self, data):
        pass

    def _handle_HOLD(self, data):
        pass

    def _handle_INFO(self, data):
        pass

    def _handle_LOG(self, data):
        pass

    def _handle_NEED_OK(self, data):
        pass

    def _handle_NEED_STR(self, data):
        pass

    def _handle_PASSWORD(self, data):
        pass

    def _handle_STATE(self, data):
        pass

    def established(self, clientnum, kid, clientdata):
        pass

    def disconnect(self, clientnum, kid, clientdata):
        pass

    def connect(self, clientnum, kid, clientdata):
        pass

    def reauth(self, clientnum, kid, clientdata):
        pass

    def _pushdef(self):
        d = Deferred()
        self._defs.append(d)
        return d

    def ByteCount(self, interval=0):
        d = self._pushdef()
        self.sendLine('bytecount %d' % (interval,))
        return d

    def ClientAuthNT(self, cid, kid):
        d = self._pushdef()
        self.sendLine('client-auth-nt %i %i' % (cid, kid))
        return d

    def _parseHoldstatus(self, result):
        return result.split('=')[0] == '1'

    def Hold(self, p=''):
        d = self._pushdef()
        self.sendLine('hold %s' % (p,))
        if p == '':
            d.addCallback(self._parseHoldstatus)
        return d

    def Kill(self, client):
        d = self._pushdef()
        self.sendLine('kill %s' % (client,))
        return d

    def _parsePid(self, result):
        return int(result.split('=')[1])

    def Pid(self):
        d = self._pushdef()
        self.sendLine('pid')
        d.addCallback(self._parsePid)
        return d
