from .credentials import get_mssql_connection_string
import logging
try:
    import pyodbc
except ImportError as ee:
    logging.warning(str(ee))

def connect_mssql(configfile, reset=False):
    while True:
        connection_str = get_mssql_connection_string(configfile, reset=reset)
        try:
            conn = pyodbc.connect(connection_str)
            break
        except pyodbc.ProgrammingError as ee:
            logging.warning(str(ee))
            if not 'Login failed for user' in str(ee):
                raise ee

            logging.warning("Did you forget to enter your domain as in 'DOMAIN\\username'?")
            reset=True

    return conn
