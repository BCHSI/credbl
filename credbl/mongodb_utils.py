# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 10:03:22 2020

@author: DLituiev
"""
import yaml
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo import errors as mongoerrors
from .credentials import get_credentials


def get_mongo_handle(url=None, ip=None, server=None, port=27017,
                     username=None, password=None, db=None):
    
    client = MongoClient(url or ip or server,
                         port=port,
                         username=username,
                         password=password)

    if db is not None:
        try:
            dbconn = client[db]
        except Exception as err:
            print("Mongo database {} is not available in this connection".format(db))
            print(mongoerrors.__dict__.keys())
            raise err
        return dbconn
    else:
        return client


def connect_mongodb(configfile, reset=False, **kwargs):
    """Connect to a mongodb given a YAML config file.
    Credentials are requested or retrieved from keyring separately.
    The YAML file must contain following:
        
        url: mongodb://10.20.30.40:27017
        db: 'databasename'
    
    Alternatively / optionally to URL, server / ip and port can be provided:
        server: xyz.company.org
        port: 27017
        ip: 10.20.30.40
    Optional keyword arguments:
        db   -- database name
        name -- name of credentials entry
    """
    
    with open(configfile) as fh:
        dbconfig = yaml.load(fh, Loader=yaml.SafeLoader)
        
    kwargs = {kk.lower():vv for kk,vv in kwargs.items()}
    dbconfig.update(**kwargs)
    
    if 'server' not in dbconfig:
        dbconfig['server'] = (dbconfig["url"]
                              .replace("mongodb://","")
                              .split("/")[0].split(":")[0]
                              )

    name = dbconfig['name'] if ('name' in dbconfig) else dbconfig['server']
    
    while True:
        username, pwd = get_credentials(name, reset=reset)
        try:
            db = get_mongo_handle(username= username, 
                                password = pwd,
                                **dbconfig)
            break
        except OperationFailure as ee:
            logging.warning(str(ee))
            if not 'Authentication failed' in str(ee):
                raise ee
            reset=True
    return db
