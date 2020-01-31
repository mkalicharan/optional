import socket
import getpass
from ldap3 import Server, Connection, Reader, ObjectDef, ALL
import pyodbc
import logging
from time import localtime, strftime
import linecache
import sys


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    error_message = 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)
    

def get_machine_name():
    try:
        logging.info(' Fetching the machine name ')
        MachineName = socket.gethostname()
        return MachineName
    except:
        logging.error(' Error in "get_machine_name" function ')
        error_message = PrintException()
        logging.error(error_message)
        raise
        

def get_logged_in_user():
    try:
        logging.info(' Fetching the logged in user ')
        LoggedInUser = getpass.getuser()
        return LoggedInUser
    except:
        logging.error(' Error in "get_logged_in_user" function ')
        error_message = PrintException()
        logging.error(error_message)
        raise


def get_mail_country_and_location():
    try: 
        logging.info(' Fetching the country and location ')
        host = 'LDAP://WorleyParsons.com'
        user = 'automation.anywhere'
        password = 'Auto@AnyIndia99'
        searchfilter = '(sAMAccountName=' + getpass.getuser() + ')'

        server = Server(host, get_info=ALL)
        conn = Connection(server, user, password, auto_bind=True, check_names=True)
        conn.search('dc=WorleyParsons,dc=com', searchfilter, attributes=['co', 'displayName', 'mail'])
        for info in conn.entries:
            info = str(info).split("\r\n")
            Country = str(info[1]).strip().split("co: ")[1]
            Location = (str(info[2]).strip().split("(")[1])[:-1]
            mail = str(info[3]).strip().split("mail: ")[1]
        return Country, Location, mail
    except:
        logging.error(' Error in "get_mail_country_and_location" function ')
        error_message = PrintException()
        logging.error(error_message)
        raise

def sql_connection_status(server,database,username,password):
    global cnxn
    try:
        cnxn = pyodbc.connect('DRIVER={'+pyodbc.drivers()[0]+'};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
        logging.info('Using driver : ' + pyodbc.drivers()[0])
        return True
    except pyodbc.Error as ex:
        logging.error(' Error in "connect_to_sql_status" function ')
        error_message = str(ex.args[1])
        logging.error(error_message)
        return False



def storing_in_db(TaskName,StartDateTime,EndDateTime,Status,LoggedInUser,MachineName,Country,Location,AutomationType,NoOfUnits):
    try:
        logging.info(' Storing the execution log in database ')
        server = 'SGAZRDEVSQL02v'
        database = 'GDCSRPAData'
        username = 'AutomationAnywhere'
        password = 'pass$911'
        if sql_connection_status(server,database,username,password):
            if cnxn!=None:
                cursor = cnxn.cursor()
                cursor.execute("Insert into BotExecutionTimeLog values (?,?,?,?,?,?,?,?,?,?)",TaskName,StartDateTime,EndDateTime,Status,LoggedInUser,MachineName,Country,Location,AutomationType,NoOfUnits)
                cnxn.commit()
    except:
        logging.error(' Error in "storing_in_db" function ')
        error_message = str(PrintException())
        logging.error(error_message)
        raise
