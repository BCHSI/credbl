import os
import yaml
import urllib
import logging
from .credentials import get_credentials

try:
    import pyodbc
    import sqlalchemy
except ImportError as ee:
    logging.warning(str(ee))

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

try:
    try:
        import winreg
    except:
        import _winreg as winreg
    proc_arch = os.environ['PROCESSOR_ARCHITECTURE'].lower()
    try:
        proc_arch64 = os.environ['PROCESSOR_ARCHITEW6432'].lower()
    except KeyError:
        proc_arch64 = None
    
    if proc_arch == 'x86' and not proc_arch64:
        arch_keys = {0}
    elif proc_arch == 'x86' or proc_arch == 'amd64':
        arch_keys = {winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY}
    else:
        raise Exception("Unhandled arch: %s" % proc_arch)
except:
    # skipping windows part
    pass


def _get_leafs(leaf_key, n_subsubkeys):
    result = {}
    for ii in range(n_subsubkeys):
        kk,vv, _ = winreg.EnumValue(leaf_key, ii)
        result[kk] = vv
    return result            


def check_odbc_entry_windows(server_name, reset=False,
                                 arch_keys = {'KEY_WOW64_32KEY', 'KEY_WOW64_64KEY'}):
    """checks whether the server is registered in the system,
    and if not launches ODBC management program"""
    arch_keys = [getattr(winreg, kk) for kk in arch_keys]
    if not reset:
        for arch_key in arch_keys:
            try:
                key = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,
                         r"Software\ODBC\ODBC.INI", 0, 
                         winreg.KEY_READ | arch_key)
                #skey = winreg.OpenKey(key, skey_name)
                n_subkeys, n_entries, _ = winreg.QueryInfoKey(key)
                
                for n in range(n_subkeys):
                    subkey = winreg.OpenKey(key, winreg.EnumKey(key, n))
                    n_subsubkeys, n_subentries, _ = winreg.QueryInfoKey(subkey)
                    keydict = (_get_leafs(subkey, n_subentries))
                    logging.debug("winreg entry: " + str(keydict))
                    if "Server" in keydict and (keydict["Server"]==server_name):
                        logging.debug("found a 'Server' entry: " + keydict["Server"])
                        return None
                # value = winreg.QueryValue(key, skey_name)
            except (FileNotFoundError, WindowsError):
                pass
    os.system('c:\\Windows\\SysWOW64\\odbcad32.exe')    
    return None


def _enclose_value_with_spaces(vv):
     return vv if not isinstance(vv,str) or " " not in vv else "{{{}}}".format(vv)


def get_mssql_connection_string(yamlfile, reset=False, urlencode=False, 
                                check_winreg=True, driver=None, **kwargs):
    """ Generate MS SQL Server connection string using a YAML config file and 
    credentials provided by the user and / or stored 
    in the system registry (Windows) or keyring (Mac, Unix).

    You may be asked your _computer_ password to authorize
    retrival of the stored database password.

    Input:
    - yamlfile -- configuration file with following  ODBC connection parameters:
        server   :  12.34.56.78 or mydatabase.mybusiness.com
        port:     
        database :  database name
        driver   :  (optional), e.g. FreeTDS
    - reset (default: False) -- whether to reset password in case
                                it is already in the registry
    - urlencode -- encode using `urllib.parse.quote_plus`
    - **kwargs  --  optional arguments that will be added to (and may override) 
                  the contents of the YAML configuration file

    parameters from the YAML file can be overriden by providing 
    named keyword arguments to this function, e.g.:
    get_mssql_connection_string("mydatabase.yaml", driver="{SQL Server}")

    Output:
    - connection string for pyodbc
    """
    kwargs = {kk.lower():vv for kk,vv in kwargs.items() if vv is not None}

    # set a default driver
    if driver is None:
        #import pyodbc
        #drivers = pyodbc.drivers()
        if os.name == 'nt':
            driver="SQL Server"
        else:
            driver="FreeTDS"
    kwargs["driver"] = driver
    
    with open(yamlfile) as fh:
        dbconfig = yaml.load(fh, Loader=yaml.SafeLoader)

    dbconfig = {kk.lower():vv for kk,vv in dbconfig.items()}
    dbconfig.update(**kwargs)

    name = dbconfig['name'] if ('name' in dbconfig) else dbconfig['server']

    # drop extra keys:
    for key in ["name", "driver_mac"]:
        if (key in dbconfig):
            dbconfig.pop(key)

    if os.name == 'nt':
        # assume passwordless LDAP authentication
        if check_winreg:
            check_odbc_entry_windows(name, reset=reset)
    else:
        username, pwd = get_credentials(name, reset=reset)
        if '\\' not in username and '@' not in username:
            logging.warning("Did you forget to enter domain "
                f"as in 'DOMAIN\\{username}' or '{username}@DOMAIN'?\n"+
                "No worries, re-run this function with `reset=True` flag")
        dbconfig['uid'] = username
        dbconfig['pwd'] = pwd

    connection_str = ";".join(["{}={}".format(kk.lower(), _enclose_value_with_spaces(vv))
                               for kk,vv in dbconfig.items()])

    if urlencode:
        connection_str = urllib.parse.quote_plus(connection_str)
    return connection_str


def connect_mssql(configfile, reset=False, backend=None, driver=None,
                  **kwargs):
    """
    returns a connection to a MS SQL server by using a server configuration file 
    and credentials stored in system's credentials manager

    Inputs:
    - configfile    -- (required) a path to a YAML server configuration file
                       (see `get_mssql_connection_string` documentation)
    - reset         -- reset the credentials
    - backend       -- default: "pyodbc", alternatives: "sqlalchemy"
    - driver        -- default: "SQL Server" for Windows and "FreeTDS" otherwise
    - **kwargs      -- other arguments that will be passed to the backend
    """
    if backend == 'sqlalchemy':
        urlencode=True
    else:
        urlencode=False

    while True:
        connection_str = get_mssql_connection_string(configfile,
                reset=reset, urlencode=urlencode,
                driver=driver,
                )

        if backend == 'sqlalchemy':
            connection_uri = 'mssql+pyodbc:///?odbc_connect={}'.format(connection_str)
            conn = sqlalchemy.create_engine(connection_uri, **kwargs)
            break 
        elif backend is None or backend in ("odbc", "pyodbc"):
            try:
                conn = pyodbc.connect(connection_str, **kwargs)
                break
            except pyodbc.ProgrammingError as ee:
                logging.warning(str(ee))
                if not 'Login failed for user' in str(ee):
                    raise ee

                logging.warning("Did you forget to enter your domain as in 'DOMAIN\\username'?")
                reset=True
        else:
            raise ValueError(f'unknown backend: "{backend}"')

    return conn
