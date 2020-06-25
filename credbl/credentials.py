import os
import click
import getpass
import keyring
import yaml
import urllib
import logging

try:
    from keyring.errors import NoKeyringError
except:
    NoKeyringError = Exception

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

def get_odbc_credentials_windows(server_name, reset=False,
                                 arch_keys = {'KEY_WOW64_32KEY', 'KEY_WOW64_64KEY'}):
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

def get_username(service_id=""):
    if 'USERNAME' in (os.environ): 
        username = os.environ['USERNAME']
    elif 'USER' in os.environ:
        username = os.environ['USER']
    else:
        username = ''
    username = click.prompt("enter user name for '{}':".format(service_id),
                  type=str, default=username)
    return username

def get_credentials(service_id,  reset=False):
    """request username & password or retrieve them from keyring;
    if reset=True, the password will be reset if found in the keyring"""
    try:
        username = keyring.get_password(service_id, "username")
    except NoKeyringError as ee:
        logging.warning(str(ee))
        logging.warning("credentials cannot be saved")
        username = get_username(service_id=service_id)
        pwd = getpass.getpass("enter password for '{}':".format(username))
        return username, pwd

    if reset or (username is None):
        username = get_username(service_id=service_id)
        # username = input("enter user name for '{}':".format(service_id))
        keyring.set_password(service_id, "username", username)

    pwd = keyring.get_password(service_id, username)
    if (pwd is None) or reset:
        pwd = getpass.getpass("enter password for '{}':".format(username))
        keyring.set_password(service_id, username, pwd)
    return username, pwd


def get_mssql_connection_string(yamlfile, reset=False, urlencode=False, 
                                check_winreg=True, **kwargs):
    """ Generate MS SQL Server connection string using a YAML config file and 
    credentials provided by the user and / or stored 
    in the system registry (Windows) or keyring (Mac, Unix).

    You may be asked your _computer_ password to authorize
    retrival of the stored database password.

    Input:
    - yamlfile -- configuration file with following  ODBC connection parameters:
        server:    12.34.56.78 or mydatabase.mybusiness.com
        port:     
        database:  database name
        driver:    (optional), e.g. FreeTDS
    - reset (default: False) -- whether to reset password in case it is already in the registry
    - urlencode -- encode using `urllib.parse.quote_plus`
    parameters from the YAML file can be overriden by providing 
    named keyword arguments to this function, e.g.:
    get_mssql_connection_string("mydatabase.yaml", driver="{SQL Server}")

    Output:
    - connection string for pyodbc
    """
    kwargs = {kk.lower():vv for kk,vv in kwargs.items()}
    
    with open(yamlfile) as fh:
        dbconfig = yaml.load(fh, Loader=yaml.SafeLoader)
        dbconfig = {kk.lower():vv for kk,vv in dbconfig.items()}
    
    if os.name == 'nt':
        dbconfig.update(**kwargs)
        name = dbconfig['name'] if ('name' in dbconfig) else dbconfig['server']
        if check_winreg:
            get_odbc_credentials_windows(name, reset=reset)
        connection_str = (
            'driver={SQL Server};'+
            'server={server};port={port};DATABASE={database};'.format(**dbconfig)
        )
    else:
        params = {'driver': 'FreeTDS',
                  #'tds_version':'7.3',
                  }
        
        for kk,vv in dbconfig.items():
            params[kk.lower()] = vv
        if len(kwargs)>0:
            params.update(**kwargs)
        username, pwd = get_credentials(params['server'], reset=reset)
        if '\\' not in username and '@' not in username:
            logging.warning("Did you forget to enter domain as in 'DOMAIN\\username' or 'username@DOMAIN'?\n"+
            "No worries, re-run this function with `reset=True` flag")
        connection_str = (
            'driver={{{driver}}};'
            # 'TDS_Version={tds_version};'
            'server={server};port={port};DATABASE={database};'
            'uid={username};pwd={pwd};').format(username=username, pwd=pwd, **params)
    if urlencode:
        connection_str = urllib.parse.quote_plus(connection_str)
    return connection_str

def get_password_qt5():
    "crashes"
    from PyQt5 import QtGui, QtCore, QtWidgets
    app = QtWidgets.QApplication([])
    pw = QtWidgets.QLineEdit()
    pw.setEchoMode(QtWidgets.QLineEdit.Password)
    pw.returnPressed.connect(app.exit)
    pw.activateWindow()
    pw.setWindowState(pw.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
    pw.show()
    app.exec_()
    
    return pw.text()

