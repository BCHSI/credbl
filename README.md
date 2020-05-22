
#

## Usage examples:

    In [1]: import credb

    In [2]: credb.get_credentials('something')
    enter user name for 'something': []: myname
    enter password for 'myname'
    Out[2]: ('myname', 'xyz')

    In [3]: credb.get_credentials('something')
    Out[3]: ('myname', 'xyz')

## Files

- [dbfunctions.R](dbfunctions.R) authentication (keyring and Windows ODBC) and dbplyr-based shortcuts
- [credentials.py](credentials.py) authentication
- [mongodb_utils.py](mongodb_utils.py) wrapper for db connection and authentication for MongoDB
