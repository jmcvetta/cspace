from cspace.util.settings import LocalSettings, AppSettings

SETTINGS_VERSION = 3

_localSettings = None
def localSettings() :
    global _localSettings
    if _localSettings is None :
        _localSettings = LocalSettings( 'CSpace' )
    return _localSettings

_profileSettings = None
def profileSettings() :
    global _profileSettings
    if _profileSettings is None :
        _profileSettings = LocalSettings( 'CSpaceProfiles' )
    return _profileSettings

_appSettings = None
def appSettings() :
    global _appSettings
    if _appSettings is None :
        _appSettings = AppSettings()
    return _appSettings

MAX_NAME_LENGTH = 32

def _init() :
    global validUserChars, validServiceChars
    allowed = ''.join( [chr(x+ord('a')) for x in range(26)] )
    allowed += ''.join( [chr(x+ord('0')) for x in range(10)] )
    allowed += '_'
    validUserChars = set( allowed )
    allowed += ''.join( [chr(x+ord('A')) for x in range(26)] )
    validServiceChars = set( allowed )
_init()

def isValidUserName( name ) :
    if not (0 < len(name) <= MAX_NAME_LENGTH) : return False
    for x in name :
        if not x in validUserChars : return False
    return True

def isValidServiceName( name ) :
    if not (0 < len(name) <= MAX_NAME_LENGTH) : return False
    for x in name :
        if not x in validServiceChars : return False
    return True
