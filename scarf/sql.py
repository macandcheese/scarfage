import MySQLdb
from scarf import app
import socket
from time import time
import datetime

from memoize import memoize_with_expiry, cache_persist, long_cache_persist
from config import dbHost, dbName, dbUser, dbPass

db = None

def read(table, **kwargs):
    """ Generates SQL for a SELECT statement matching the kwargs passed. """
    sql = list()
    sql.append("SELECT * FROM %s " % table)
    if kwargs:
        sql.append("WHERE " + " AND ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)

def upsert(table, **kwargs):
    """ update/insert rows into objects table (update if the row already exists)
        given the key-value pairs in kwargs """
    keys = ["%s" % k for k in kwargs]
    values = ["'%s'" % v for v in kwargs.values()]
    sql = list()
    sql.append("INSERT INTO %s (" % table)
    sql.append(", ".join(keys))
    sql.append(") VALUES (")
    sql.append(", ".join(values))
    sql.append(") ON DUPLICATE KEY UPDATE ")
    sql.append(", ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)

def delete(table, **kwargs):
    """ deletes rows from table where **kwargs match """
    sql = list()
    sql.append("DELETE FROM %s " % table)
    sql.append("WHERE " + " AND ".join("%s = '%s'" % (k, v) for k, v in kwargs.iteritems()))
    sql.append(";")
    return "".join(sql)

def doupsert(query):
    # dump the cache since we're writing to the db
    query_cache.clear()

    app.logger.debug(query)
    global db

    try:
        if db is None:
            app.logger.info("Connecting to db host")
            db = MySQLdb.connect(host=dbHost, db=dbName, user=dbUser, passwd=dbPass)

        cursor = db.cursor()
        cursor.execute(query)
        db.commit()
        cursor.close()
        data = cursor.lastrowid

        return data

    except MySQLdb.MySQLError as e:
        db = None
        app.logger.error("Cannot connect to database. MySQL error: " + str(e))
        raise

query_cache = dict()
@memoize_with_expiry(query_cache, cache_persist)
def doquery(query):
    app.logger.debug(query)
    global db

    try:
        if db is None:
            app.logger.info("Connecting to db host")
            db = MySQLdb.connect(host=dbHost, db=dbName, user=dbUser, passwd=dbPass)

        cur = db.cursor()
        cur.execute(query)

        data = cur.fetchall()

        db.commit()

        return data

    except MySQLdb.MySQLError as e:
        db = None
        app.logger.error("Cannot connect to database. MySQL error: " + str(e))
        raise