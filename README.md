# Credbl: database settings and credentials simplified

There are many moving parts when setting up programmatic access to a database. Credbl divides (and conquers) those bits and pieces the following way:
- [connect-where] database server specific settings are read from a YAML configuration file provided by the database admin
- [connect-who] user's credentials are requested and stored in [keyring](https://github.com/jaraco/keyring) or winreg (on Windows).

    The first time the user connects to the database with `connect_*` functions, the credentials will be requested and stored. Subsequent times, they will be silently retrieved and used to authenticate. If authentication fails due to wrong credentials, the user will be asked to enter credentials again.
- [connect-how] database drivers are chosen based on user's Operation system. 

Currently credbl focuses on MS SQL Server and MongoDB connections. You are welcome to submit issues and pull requests for other database types.

## Installation

### Python package

from terminal shell (standard):
- latest release: `pip install credbl`

- bleeding edge: `pip install git+git://github.com/BCHSI/credbl.git#egg=credbl`

- development mode

        git clone https://github.com/BCHSI/credbl
        cd credbl
        pip install -e .

### R package

from R:

```R
install.packages('devtools')
library(devtools)
install_github('https://github.com/BCHSI/credbl')
```

or terminal + R:

    git clone https://github.com/BCHSI/credbl
    cd credbl
    R
    > install.packages('devtools')
    > library(devtools)
    > install('.')

get help:
    
```R
?credbl
```
    
## Usage examples:

### connecting to a MS SQL Server

    from credbl import connect_mssql
    conn = connect_mssql("tp-mssql-settings.yaml")

    
### Contents of database configuration file
In a previous example, `"tp-mssql-settings.yaml"` must contain:

    server:    12.34.56.78 (OR) mydatabase.mybusiness.com
    port:      1234
    database:  tp-inventory
    driver:    FreeTDS (optional)

### Low-level interface: 
You might need to understand it if you would like to use SQL drivers
or driver wrappers other than pyodbc, such as SQLAlchemy.

#### with pyodbc

    import pyodbc
    from credbl import get_mssql_connection_string 

    # if called for the first time, will request credentials
    # second time may ask for your _system_ credentials; mark "always allow"

    connection_str = get_mssql_connection_string("tp-mssql-settings.yaml")
    # you'll be requested to enter your credentials when running it for the first time
    conn = pyodbc.connect(connection_str)
    
    
#### if you believe you've entered wrong credentials first time, call with `reset=True`

    connection_str = get_mssql_connection_string("tp-mssql-settings.yaml", reset=True)
    
    conn = pyodbc.connect(connection_str)

### with SqlAlchemy

    import sqlalchemy
    from credbl import get_mssql_connection_string 

    connection_str_encoded = get_mssql_connection_string('covid19_omop.yaml',
                                                     urlencode=True)
    connection_uri = 'mssql+pyodbc:///?odbc_connect={}'.format(connection_str_encoded)
    conn = sqlalchemy.create_engine(connection_uri)

### connecting to mongodb

    from credbl import connect_mongodb
    
    # if called for the first time, will request database credentials
    mdb = connect_mongodb("mongo-settings.yaml")
    
    mdb.list_collection_names()
    
The `"mongo-settings.yaml"` file must contain following:

    url: mongodb://10.20.30.40:27017
    db: 'databasename'

Alternatively / optionally to URL, server or IP address and port can be provided:

    server: xyz.company.org
    ip: 10.20.30.40
    port: 27017

    
### storing credentials in `keyring` (Mac, Unix) or Windows key storage:

    In [1]: import credbl

    In [2]: credbl.get_credentials('something')
    enter user name for 'something': []: myname
    enter password for 'myname':
    Out[2]: ('myname', 'xyz')

    In [3]: credbl.get_credentials('something')
    Out[3]: ('myname', 'xyz')
    

## Files

- [dbfunctions.R](dbfunctions.R) authentication (keyring and Windows ODBC) and dbplyr-based shortcuts
- [credentials.py](credbl/credentials.py) authentication
- [mongodb_utils.py](credbl/mongodb_utils.py) wrapper for db connection and authentication for MongoDB
