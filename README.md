# Credbl: database credential management package

## Installation

### Python package

from terminal shell:

    git clone https://github.com/BCHSI/credbl
    cd credbl
    pip install .

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

    
## Usage examples:

### connecting to a MS SQL Server

    from credbl import get_mssql_connection_string
    import pyodbc
    

    # if called for the first time, will request credentials
    # second time may ask for your _system_ credentials; mark "always allow"

    connection_str = get_mssql_connection_string("tp-mssql-settings.yaml")
    
    # if you believe you've entered wrong credentials first time, call with `reset=True`
    connection_str = get_mssql_connection_string("tp-mssql-settings.yaml", reset=True)
    
    conn = pyodbc.connect(connection_str)
    
Contents of `"tp-mssql-settings.yaml"` (assuming it is in the same folder as your script):

    server:    12.34.56.78 (OR) mydatabase.mybusiness.com
    port:      1234
    database:  tp-inventory
    driver:    FreeTDS (optional)

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
