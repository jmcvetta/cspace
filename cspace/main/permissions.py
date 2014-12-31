import os, re, StringIO
from cspace.main.common import profileSettings

permissionsHelp ="""\
For EVERY connection, rules are matched in SEQUENTIAL order.
If two rules match a particular connection, then the first
rule will take precedence

Format:
    (action-spec) (user-spec) service (service-spec)
Where:
    action-spec  -> allow | deny | prompt
    user-spec    -> nickname | <contact-user> | <any-user>
    service-spec -> servicename | <any-service>

Example:
allow  sreeram        service TextChat
allow  <contact-user> service FileTransfer
deny   <any-user>     service FileTransfer
prompt <any-user>     service <any-service>
"""

predefinedPermissions ="""\
prompt <contact-user> service RemoteDesktop
allow  <contact-user> service <any-service>
deny   <any-user>     service RemoteDesktop
allow  <any-user>     service TextChat
prompt <any-user>     service <any-service>
"""

ACCESS_ALLOW = 0
ACCESS_DENY = 1
ACCESS_PROMPT = 2
ACCESS_COUNT = 3

def _loadPredefinedPermissions() :
    return predefinedPermissions

def _loadUserPermissions( profile ) :
    entry = profile.storeEntry + '/Permissions'
    return profileSettings().getData( entry, '' )

def _storeUserPermissions( profile, data ) :
    entry = profile.storeEntry + '/Permissions'
    return profileSettings().setData( entry, data )

class BaseUser( object ) :
    def matches( self, userName ) :
        raise NotImplementedError
    def toString( self ) :
        raise NotImplementedError

class NamedUser( BaseUser ) :
    def __init__( self, userName ) :
        self.userName = userName
    def matches( self, userName ) :
        return userName == self.userName
    def toString( self ) :
        return self.userName

class ContactUser( BaseUser ) :
    def __init__( self, profile ) :
        self.profile = profile
    def matches( self, userName ) :
        contact = self.profile.getContactByName( userName )
        if contact is None : return False
        return True
    def toString( self ) :
        return '<contact-user>'

class AnyUser( BaseUser ) :
    def __init__( self ) :
        pass
    def matches( self, userName ) :
        return True
    def toString( self ) :
        return '<any-user>'

class BaseService( object ) :
    def matches( self, serviceName ) :
        raise NotImplementedError
    def toString( self ) :
        raise NotImplementedError

class NamedService( BaseService ) :
    def __init__( self, serviceName ) :
        self.serviceName = serviceName
    def matches( self, serviceName ) :
        return serviceName == self.serviceName
    def toString( self ) :
        return self.serviceName

class AnyService( BaseService ) :
    def __init__( self ) :
        pass
    def matches( self, serviceName ) :
        return True
    def toString( self ) :
        return '<any-service>'

class BadRuleError( Exception ) :
    def __init__( self, lineNumber=0 ) :
        Exception.__init__( self )
        self.lineNumber = lineNumber
    def setLineNumber( self, lineNumber ) :
        self.lineNumber = lineNumber
class BadUserInRuleError( BadRuleError ) :
    def __init__( self, user, lineNumber=0 ) :
        BadRuleError.__init__( self, lineNumber )
        self.user = user
class BadServiceInRuleError( BadRuleError ) :
    def __init__( self, service, lineNumber=0 ) :
        BadRuleError.__init__( self, lineNumber )
        self.service = service

class BlankRule( object ) :
    def __init__( self, line ) :
        self.line = line

    def execute( self, userName, serviceName ) :
        return None

    def toLine( self ) :
        return self.line

class PermissionRule( object ) :
    def __init__( self, accessAction, userMatcher, serviceMatcher ) :
        self.s = [''] * 5
        self.s[0] = ''
        self.accessAction = accessAction
        self.s[1] = ''
        self.userMatcher = userMatcher
        self.s[2] = ''
        self.s[3] = ''
        self.serviceMatcher = serviceMatcher
        self.s[4] = ''

    def execute( self, userName, serviceName ) :
        if (self.userMatcher.matches(userName) and
                self.serviceMatcher.matches(serviceName)) :
            return self.accessAction
        return None

    def toLine( self ) :
        actions = [ 'allow', 'deny', 'prompt' ]
        act = actions[ self.accessAction ]
        user = self.userMatcher.toString()
        service = self.serviceMatcher.toString()
        s = self.s
        return ''.join( [s[0],act,s[1],user,s[2],'service',s[3],service,s[4]] )

    def fromLine( line, profile, serviceList ) :
        comment = ''
        x = line.find('#')
        if x >= 0 :
            line,comment = line[:x],line[x:]
        if not line.strip() :
            return BlankRule( line+comment )
        toks = re.split( '(\S+)', line )
        if len(toks) != 9 :
            raise BadRuleError()
        s = [''] * 5
        s[0],act,s[1],user,s[2],dummy,s[3],service,s[4] = toks
        s[4] += comment
        if dummy != 'service' :
            raise BadRuleError()
        actions = dict( allow=ACCESS_ALLOW, deny=ACCESS_DENY,
                prompt=ACCESS_PROMPT )
        accessAction = actions.get( act.lower(), None )
        if accessAction is None :
            raise BadRuleError()
        if user.lower() == '<contact-user>' :
            userMatcher = ContactUser( profile )
        elif user.lower() == '<any-user>' :
            userMatcher = AnyUser()
        else :
            contact = profile.getContactByName( user )
            if contact is None :
                raise BadUserInRuleError( user )
            userMatcher = NamedUser( user )
        if service.lower() == '<any-service>' :
            serviceMatcher = AnyService()
        else :
            if service not in serviceList :
                raise BadServiceInRuleError( service )
            serviceMatcher = NamedService( service )
        rule = PermissionRule( accessAction, userMatcher, serviceMatcher )
        rule.s = s
        return rule
    fromLine = staticmethod(fromLine)

class Permissions( object ) :
    def __init__( self, profile, serviceList ) :
        self.profile = profile
        self.serviceList = serviceList
        self.predefinedRules = []
        self.userRules = []
        self.modified = False

        data = _loadUserPermissions( profile )
        self.setUserPermissions( data, ignoreBadRules=True )
        data = _loadPredefinedPermissions()
        self.setPredefinedPermissions( data, ignoreBadRules=True )

    def isModified( self ) : return self.modified
    def setModified( self, modified ) :
        self.modified = modified

    def execute( self, userName, serviceName ) :
        rules = self.userRules + self.predefinedRules
        for r in rules :
            result = r.execute( userName, serviceName )
            if result is not None : return result
        return ACCESS_PROMPT

    def _parsePermissions( self, data, ignoreBadRules=False ) :
        rules = []
        hasBadRules = False
        for num,line in enumerate(data.splitlines()) :
            try :
                rule = PermissionRule.fromLine( line, self.profile,
                        self.serviceList )
                rules.append( rule )
            except BadRuleError, e :
                if not ignoreBadRules :
                    e.setLineNumber( num+1 )
                    raise
                line = '# BadRule: ' + line
                rule = BlankRule( line )
                rules.append( rule )
                hasBadRules = True
        return rules,hasBadRules

    def setPredefinedPermissions( self, data, ignoreBadRules=False ) :
        rules,hasBadRules = self._parsePermissions( data,
                ignoreBadRules )
        self.predefinedRules = rules

    def setUserPermissions( self, data, ignoreBadRules=False ) :
        rules,hasBadRules = self._parsePermissions( data,
                ignoreBadRules )
        self.userRules = rules
        self.modified = hasBadRules

    def getHelpText( self ) :
        return permissionsHelp

    def getPredefinedPermissions( self ) :
        out = StringIO.StringIO()
        for rule in self.predefinedRules :
            print>>out, rule.toLine()
        return out.getvalue()

    def getUserPermissions( self ) :
        out = StringIO.StringIO()
        for rule in self.userRules :
            print>>out, rule.toLine()
        return out.getvalue()

    def changeContactName( self, oldName, newName ) :
        for rule in self.userRules :
            if isinstance(rule,PermissionRule) :
                userMatcher = rule.userMatcher
                if isinstance(userMatcher,NamedUser) :
                    if oldName == userMatcher.userName :
                        userMatcher.userName = newName
                        self.modified = True

    def removeContact( self, name ) :
        newRules = []
        for rule in self.userRules :
            if isinstance(rule,PermissionRule) and \
                    isinstance(rule.userMatcher,NamedUser) and \
                    (rule.userMatcher.userName == name) :
                rule = BlankRule( '# Contact removed: ' + rule.toLine() )
                self.modified = True
            newRules.append( rule )
        self.userRules = newRules

    def savePermissions( self ) :
        perm = self.getUserPermissions()
        _storeUserPermissions( self.profile, perm )
        self.modified = False
