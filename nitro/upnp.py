import logging
from StringIO import StringIO
from socket import socket, AF_INET, SOCK_DGRAM, inet_aton
from socket import IPPROTO_IP, IP_ADD_MEMBERSHIP, IP_DROP_MEMBERSHIP
from socket import error as sock_error
from urlparse import urljoin
from elementtree import ElementTree
from nitro.async import AsyncOp
from nitro.http import HttpRequest

logger = logging.getLogger( 'nitro.upnp' )

UPNP_MCAST_GROUP = '239.255.255.250'
UPNP_PORT = 1900
UPNP_SERVICE_TYPE = 'urn:schemas-upnp-org:device:InternetGatewayDevice:1'
UPNP_SEARCH_MSG = (
        'M-SEARCH * HTTP/1.1\r\n' +
        'Host:%s:%d\r\n' % (UPNP_MCAST_GROUP,UPNP_PORT) +
        'ST:%s\r\n' % UPNP_SERVICE_TYPE +
        'Man:"ssdp:discover"\r\n' +
        'MX:3\r\n' +
        '\r\n' )
UPNP_SERVICES = ['urn:schemas-upnp-org:service:WANIPConnection:1',
                'urn:schemas-upnp-org:service:WANPPPConnection:1']

class UPnpError( Exception ) : pass

class UPnpActionArg( object ) :
    def __init__( self, name, direction ) :
        assert direction in ('in','out')
        self.name = name
        self.direction = direction

class UPnpAction( object ) :
    def __init__( self, name, args ) :
        self.name = name 
        self.args = args

class UPnpDevice( object ) :
    def __init__( self, scpdUrl, controlUrl, service ) :
        self.scpdUrl = scpdUrl
        self.controlUrl = controlUrl
        self.service = service
        self.friendlyName = None
        self.manufacturer = None
        self.actions = []

    def getAction( self, name ) :
        for action in self.actions :
            if action.name == name : return action
        return None

    def getActionPayload( self, name, params ) :
        action = self.getAction( name )
        params = dict(params)
        inArgs = []
        for arg in action.args :
            if arg.direction == 'in' :
                value = params.pop( arg.name, None )
                if value is None :
                    raise UPnpError, 'missing parameter: %s' % arg.name
                inArgs.append( (arg.name,str(value)) )
        if params :
            raise UPnpError, 'invalid parameter(s): %s' % str(params.keys())
        out = StringIO()
        sns = 'http://schemas.xmlsoap.org/soap/envelope/'
        enc = 'http://schemas.xmlsoap.org/soap/encoding/'
        print>>out, '<s:Envelope xmlns:s="%s" s:encodingStyle="%s">' % (sns,enc)
        print>>out, '<s:Body>'
        print>>out, '<u:%s xmlns:u="%s">' % (name,self.service)
        for arg,value in inArgs :
            print>>out, '<%s>%s</%s>' % (arg,value,arg)
        print>>out, '</u:%s>' % name
        print>>out, '</s:Body>'
        print>>out, '</s:Envelope>'
        return out.getvalue()

    def _onActionResponse( self, op, name, result, data ) :
        if result != 200 :
            logger.info( 'action response error: http request failed' )
            op.notify( -1, None )
            return
        def check( cond, errMsg ) :
            if not cond : raise UPnpError, errMsg
        try :
            input = StringIO( data )
            try :
                root = ElementTree.parse(input).getroot()
            except :
                logger.exception( 'error parsing xml' )
                raise UPnpError, 'invalid response xml'
            try :
                sns = root.tag[root.tag.index('{')+1:root.tag.index('}')]
            except ValueError :
                raise UPnpError, 'no soap namespace found'
            check( root.tag == '{%s}Envelope'%sns, 'unknown root element' )
            body = root.find('{%s}Body'%sns)
            check( body is not None, 'soap body not found' )
            response = body.find( '{%s}%sResponse' % (self.service,name) )
            check( response is not None, 'action response not found' )
            action = self.getAction( name )
            check( action is not None, 'invalid action name' )
            responseArgs = dict( [(arg.tag,arg.text or '') for arg in response] )
            outArgs = []
            for arg in action.args :
                if arg.direction == 'out' :
                    value = responseArgs.pop( arg.name, None )
                    if value is not None :
                        outArgs.append( (arg.name,value) )
        except UPnpError, errMsg :
            logger.warning( 'action response error: %s', errMsg )
            op.notify( -1, None )
            return
        op.notify( 0, outArgs )

    def callAction( self, name, params, reactor, callback=None ) :
        payload = self.getActionPayload( name, params )
        http = HttpRequest( reactor )
        http.addHeader( 'Content-Type: text/xml; charset="utf-8"' )
        http.addHeader( 'SOAPACTION: "%s#%s"' % (self.service,name) )
        def onResponse( result, data ) :
            self._onActionResponse( op, name, result, data )
        httpOp = http.post( self.controlUrl, payload, onResponse )
        op = AsyncOp( callback, httpOp.cancel )
        return op

class UPnpFinder( object ) :
    def __init__( self, reactor ) :
        self.reactor = reactor
        self.discoverCallback = None
        self.httpOps = {}
        self.sock = socket( AF_INET, SOCK_DGRAM )
        self.sock.bind( ('',0) )
        try :
            addr = inet_aton( UPNP_MCAST_GROUP )
            interface = inet_aton( '0.0.0.0' )
            self.sock.setsockopt( IPPROTO_IP, IP_ADD_MEMBERSHIP,
                    inet_aton(UPNP_MCAST_GROUP)+inet_aton('0.0.0.0') )
        except sock_error, (err,errMsg) :
            logger.exception( 'socket error(%d): %s', err, errMsg )
        self.reactor.addReadCallback( self.sock.fileno(), self._onRead )

    def setDiscoverCallback( self, discoverCallback ) :
        self.discoverCallback = discoverCallback

    def close( self ) :
        for op in self.httpOps.keys() :
            op.cancel()
        self.httpOps.clear()
        self.reactor.removeReadCallback( self.sock.fileno() )
        self.sock.close()
        self.sock = None

    def sendQuery( self ) :
        dest = (UPNP_MCAST_GROUP,UPNP_PORT)
        try :
            self.sock.sendto( UPNP_SEARCH_MSG, dest )
        except sock_error, (err,errMsg) :
            logger.exception( 'socket error(%d): %s', err, errMsg )

    def _onRead( self ) :
        try :
            data,fromaddr = self.sock.recvfrom( 8192 )
        except sock_error, (err,errMsg) :
            logger.exception( 'socket error(%d): %s', err, errMsg )
            return
        lines = data.splitlines()
        if not lines : return
        header = lines[0].split(None,2)
        if len(header) != 3 : return
        httpVersion,httpCode,httpMsg = header
        if not httpVersion.startswith('HTTP/') : return
        if httpCode != '200' : return
        location = None
        for line in lines[1:] :
            header = line.split(':',1)
            if len(header) != 2 : break
            name,value = header
            if name.lower() == 'location' :
                location = value.strip()
                break
        if location is None : return
        def onResult( result, data ) :
            self._onHttpGet( httpOp, result, data, location )
        httpOp = HttpRequest( self.reactor ).get( location, onResult )
        self.httpOps[httpOp] = 1

    def _onHttpGet( self, httpOp, result, data, httpUrl ) :
        del self.httpOps[httpOp]
        if result != 200 : return
        assert data is not None
        input = StringIO( data )
        try :
            root = ElementTree.parse(input).getroot()
        except :
            logger.exception( 'error parsing xml' )
            return
        try :
            ns = root.tag[root.tag.index('{')+1:root.tag.index('}')]
        except ValueError :
            logger.exception( 'no namespace found' )
            return
        baseUrl = ''
        scpdUrl = None
        controlUrl = None
        service = None
        friendlyName = None
        manufacturer = None
        for elem in root.findall('.//{%s}friendlyName'%ns) :
            friendlyName = elem.text
            break
        for elem in root.findall('.//{%s}manufacturer'%ns) :
            manufacturer = elem.text
            break
        for elem in root.findall('.//{%s}URLBase'%ns) :
            baseUrl = elem.text
            break
        for elem in root.findall('.//{%s}service'%ns) :
            serviceTypeElem = elem.find( '{%s}serviceType'%ns )
            if serviceTypeElem is None : continue
            service = serviceTypeElem.text
            if service not in UPNP_SERVICES : continue
            scpdUrlElem = elem.find( '{%s}SCPDURL'%ns )
            if scpdUrlElem is None : continue
            controlUrlElem = elem.find( '{%s}controlURL'%ns )
            if controlUrlElem is None : continue
            scpdUrl = urljoin( baseUrl, scpdUrlElem.text )
            controlUrl = urljoin( baseUrl, controlUrlElem.text )
            break
        if not scpdUrl : return
        if not controlUrl : return
        if not scpdUrl.startswith('http:') :
            scpdUrl = urljoin( httpUrl, scpdUrl )
        if not controlUrl.startswith('http:') :
            controlUrl = urljoin( httpUrl, controlUrl )
        device = UPnpDevice( scpdUrl, controlUrl, service )
        device.friendlyName = friendlyName
        device.manufacturer = manufacturer
        def onResult( result, data ) :
            self._onScpdGet( httpOp, device, result, data )
        httpOp = HttpRequest( self.reactor ).get( scpdUrl, onResult )
        self.httpOps[httpOp] = 1

    def _onScpdGet( self, httpOp, device, result, data ) :
        del self.httpOps[httpOp]
        if result != 200 : return
        assert data is not None
        input = StringIO( data )
        try :
            root = ElementTree.parse(input).getroot()
        except :
            logger.exception( 'error parsing xml' )
            return
        try :
            ns = root.tag[root.tag.index('{')+1:root.tag.index('}')]
        except ValueError :
            logger.exception( 'no namespace found' )
            return
        actionElements = root.findall('.//{%s}action'%ns)
        for actionElem in actionElements :
            nameElem = actionElem.find('{%s}name'%ns)
            if nameElem is None : continue
            actionName = nameElem.text
            actionArgs = []
            for arg in actionElem.findall('.//{%s}argument'%ns) :
                nameElem = arg.find('{%s}name'%ns)
                if nameElem is None : continue
                argName = nameElem.text
                direction = 'in'
                dirElem = arg.find('{%s}direction'%ns)
                if dirElem is not None :
                    direction = dirElem.text.lower()
                    if direction not in ('in','out') : continue
                actionArg = UPnpActionArg( argName, direction )
                actionArgs.append( actionArg )
            action = UPnpAction( actionName, actionArgs )
            device.actions.append( action )
        if self.discoverCallback :
            self.discoverCallback( device )

class UPnpActions( object ) :
    def findDevice( reactor, callback=None ) :
        def doCancel() :
            finder.close()
            timerOp.cancel()
        def onDiscover( device ) :
            finder.close()
            timerOp.cancel()
            op.notify( device )
        def onTimeout() :
            finder.close()
            op.notify( None )
        finder = UPnpFinder( reactor )
        finder.setDiscoverCallback( onDiscover )
        finder.sendQuery()
        finder.sendQuery()
        timerOp = reactor.callLater( 20, onTimeout )
        op = AsyncOp( callback, doCancel )
        return op
    findDevice = staticmethod( findDevice )

    def getExternalIP( device, reactor, callback=None ) :
        def onResponse( result, data ) :
            if result < 0 :
                op.notify( None )
                return
            externalIP = dict(data).get('NewExternalIPAddress',None)
            op.notify( externalIP )
        actionOp = device.callAction( 'GetExternalIPAddress', {},
                reactor, onResponse )
        op = AsyncOp( callback, actionOp.cancel )
        return op
    getExternalIP = staticmethod( getExternalIP )

    def listMappings( device, reactor, callback=None ) :
        class Dummy : pass
        obj = Dummy()
        def doCancel() :
            obj.actionOp.cancel()
        def parsePortMapping( data ) :
            data = dict( data )
            try :
                remote = data['NewRemoteHost']
                external = int( data['NewExternalPort'] )
                proto = data['NewProtocol']
                internal = int( data['NewInternalPort'] )
                client = data['NewInternalClient']
                enabled = int( data['NewEnabled'] )
                desc = data['NewPortMappingDescription']
                lease = int(data['NewLeaseDuration'])
            except (KeyError,ValueError,TypeError) :
                raise UPnpError
            return (remote,external,proto,internal,client,enabled,desc,lease)
        def onResponse( result, data ) :
            obj.actionOp = None
            try :
                if result < 0 : raise UPnpError
                mapping = parsePortMapping( data )
            except UPnpError :
                obj.op.notify( None )
                return
            obj.index += 1
            doAction()
            obj.op.notify( mapping )
        def doAction() :
            params = { 'NewPortMappingIndex':obj.index }
            obj.actionOp = device.callAction( 'GetGenericPortMappingEntry',
                    params, reactor, onResponse )
        obj.index = 0
        doAction()
        obj.op = AsyncOp( callback, doCancel )
        return obj.op
    listMappings = staticmethod( listMappings )

    def listAllMappings( device, reactor, callback=None ) :
        mappings = []
        def onResponse( mapping ) :
            if mapping is not None :
                mappings.append( mapping )
                return
            op.notify( mappings )
        listOp = UPnpActions.listMappings( device, reactor, onResponse )
        op = AsyncOp( callback, listOp.cancel )
        return op
    listAllMappings = staticmethod( listAllMappings )

    def addMapping( device, externalPort, protocol, internalPort,
            internalIP, description, reactor, callback=None ) :
        assert protocol in ('TCP','UDP')
        params = {
            'NewRemoteHost' : '',
            'NewExternalPort' : externalPort,
            'NewProtocol' : protocol,
            'NewInternalPort' : internalPort,
            'NewInternalClient' : internalIP,
            'NewEnabled' : 1,
            'NewPortMappingDescription' : description,
            'NewLeaseDuration' : 0 }
        def onResponse( result, data ) :
            op.notify( result == 0 )
        actionOp = device.callAction( 'AddPortMapping', params, reactor, onResponse )
        op = AsyncOp( callback, actionOp.cancel )
        return op
    addMapping = staticmethod( addMapping )

    def delMapping( device, externalPort, protocol, reactor, callback=None ) :
        assert protocol in ('TCP','UDP')
        params = {
            'NewRemoteHost' : '',
            'NewExternalPort' : externalPort,
            'NewProtocol' : protocol }
        def onResponse( result, data ) :
            op.notify( result == 0 )
        actionOp = device.callAction( 'DeletePortMapping', params, reactor, onResponse )
        op = AsyncOp( callback, actionOp.cancel )
        return op
    delMapping = staticmethod( delMapping )
