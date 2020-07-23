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

