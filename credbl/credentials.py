import os
import click
import getpass
import keyring
import logging

try:
    from keyring.errors import NoKeyringError
except:
    NoKeyringError = Exception


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


def get_credentials_windows(service_id, reset=False, attempts=3,
                            info=None):
    keyring;
    while attempts>0:
        attempts -= 1
        try:
            if reset: # an event flow trick
                logging.debug("resetting the credentials")
                raise ValueError
            logging.info(f"attempting to retrieve crdentials for {service_id}")
            kr = keyring.get_credential(service_id, None)
            if kr is None:
                #logging.warning(f"no credentials found for {service_id} in Windows registry")
                raise ValueError(f"no credentials found for {service_id} in Windows registry")
            return kr.username, kr.password
        except (ValueError, NoKeyringError) as ee:
            print("")
            print("="*50)
            print("")
            print(f'Please create an account for "{service_id}" by clicking "Add..."')
            print("Enter following:")
            print(f"Log on to:     {service_id}")
            print("Username :     your username")
            print("Password :     your password")
            if info:
                print(info)
            # os.system("control keymgr.dll") # this one returns asynchronously
            os.system("rundll32.exe keymgr.dll, KRShowKeyMgr")
            reset = False
    else:
        logging.warning("number of attempts exceeded")
        raise ValueError("unable to retrieve credentials. Number of attempts exceeded")


def get_credentials(service_id,  reset=False, windows_info=None):
    """request username & password or retrieve them from keyring;
    if reset=True, the password will be reset if found in the keyring"""
    if os.name == 'nt':
        return get_credentials_windows(service_id,  reset=reset, info=windows_info)
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

