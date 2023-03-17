"""
Before running, set these environment variables:

    PYTHON_USERNAME       - your DB username
    PYTHON_PASSWORD       - your DB password
    PYTHON_CONNECTSTRING  - the connection string to the DB, e.g. "example.com/XEPDB1"
    PORT                  - port the web server will listen on.  The default in 8080

"""

import os
import oracledb
from flask import Flask, render_template, request
from dotenv import load_dotenv

################################################################################
#
# On macOS tell cx_Oracle 8 where the Instant Client libraries are.  You can do
# the same on Windows, or add the directories to PATH.  On Linux, use ldconfig
# or LD_LIBRARY_PATH.  cx_Oracle installation instructions are at:
# https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html
'''if sys.platform.startswith("darwin"):
    cx_Oracle.init_oracle_client(lib_dir=os.environ.get("HOME")+"/instantclient_19_3")
elif sys.platform.startswith("win32"):
    cx_Oracle.init_oracle_client(lib_dir=r"c:\oracle\instantclient_19_8")'''

################################################################################
#
# Start a connection pool.
#
# Connection pools allow multiple, concurrent web requests to be efficiently
# handled.  The alternative would be to open a new connection for each use
# which would be very slow, inefficient, and not scalable.  Connection pools
# support Oracle high availability features.
#
# Doc link: https://cx-oracle.readthedocs.io/en/latest/user_guide/connection_handling.html#connection-pooling


# init_session(): a 'session callback' to efficiently set any initial state
# that each connection should have.
#
# If you have multiple SQL statements, then them all in a PL/SQL anonymous
# block with BEGIN/END so you only call execute() once.  This is shown later in
# create_schema().
#
# This particular demo doesn't use dates, so sessionCallback could be omitted,
# but it does show settings many apps would use.
#
# Note there is no explicit 'close cursor' or 'close connection'.  At the
# end-of-scope when init_session() finishes, the cursor and connection will be
# closed automatically.  In real apps with a bigger code base, you will want to
# close each connection as early as possible so another web request can use it.
#
# Doc link: https://cx-oracle.readthedocs.io/en/latest/user_guide/connection_handling.html#session-callbacks-for-setting-pooled-connection-state
#
def init_session(connection, requestedTag_ignored):
    cursor = connection.cursor()
    cursor.execute("""
        ALTER SESSION SET
          TIME_ZONE = 'UTC'
          NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI'""")

# start_pool(): starts the connection pool
def start_pool():
    # Generally a fixed-size pool is recommended, i.e. pool_min=pool_max.
    # Here the pool contains 4 connections, which is fine for 4 conncurrent
    # users.
    #
    # The "get mode" is chosen so that if all connections are already in use, any
    # subsequent acquire() will wait for one to become available.

    pool_min = 4
    pool_max = 4
    pool_inc = 0
    pool_gmd = oracledb.SPOOL_ATTRVAL_WAIT

    print("Connecting to", "(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)("
          "host=adb.us-ashburn-1.oraclecloud.com))(connect_data=("
          "service_name=g83c4ff870b21c6_chessdatabase_high.adb.oraclecloud.com))(security=("
          "ssl_server_dn_match=yes)))")

    pool = oracledb.SessionPool(user=os.getenv("USER"),
                                password=os.getenv("PASSWORD"),
                                dsn="(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)("
                                    "host=adb.us-ashburn-1.oraclecloud.com))(connect_data=("
                                    "service_name=g83c4ff870b21c6_chessdatabase_high.adb.oraclecloud.com))(security=("
                                    "ssl_server_dn_match=yes)))",
                                config_dir="Oracle Wallet",
                                wallet_location="Oracle Wallet",
                                wallet_password=os.getenv("PASSWORD"),
                                min=pool_min,
                                max=pool_max,
                                increment=pool_inc,
                                threaded=True,
                                getmode=pool_gmd,
                                sessionCallback=init_session)
    return pool

################################################################################
#
# create_schema(): drop and create the demo table, and add a row
#
def insert_starting_user():
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute("""
        begin
          execute immediate 'insert into Users (userName) values (''Joseph'')';

          commit;
        end;""")

################################################################################
#
# Specify some routes
#
# The default route will display a welcome message:
#   http://127.0.0.1:8080/
#
# To insert new a user 'fred' you can call:
#    http://127.0.0.1:8080/post/fred
#
# To find a username you can pass an id, for example 1:
#   http://127.0.0.1:8080/user/1
#

app = Flask(__name__)

# Display a welcome message on the 'home' page
@app.route('/')
def index():
    return render_template('index.html')

# Add a new username
#
# The new user's id is generated by the DB and returned in the OUT bind
# variable 'idbv'.  As before, we leave closing the cursor and connection to
# the end-of-scope cleanup.
@app.route('/insert/<string:username>')
def insertUser(username):
    connection = pool.acquire()
    cursor = connection.cursor()
    print("connection established")
    connection.autocommit = True
    id_bv = cursor.var(int)
    cursor.execute("""
        insert into Users (username)
        values (:userName_bv)
        returning userID into :id_bv""", [username, id_bv])
    # returns the id number for the newly added user
    return id_bv.getvalue()[0]

# Show the username for a given id
@app.route('/user/<int:id>')
def show_username(id):
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute("select userName from Users where userId = :id_bv", [id])
    # fetching the first row from the previously executed query
    r = cursor.fetchone()
    return (r[0] if r else "Unknown user id")

@app.route('/add_user', methods = ["GET", "POST"])
def add_user_page():
    if request.method == "POST":
        # getting input with name = fname in HTML form
        user_name = request.form.get("name")
        id_num = insertUser(user_name)
        return f"Added {user_name} to the database with an ID number of: {id_num}"
    return render_template('add_view.html')


################################################################################
#
# Initialization is done once at startup time
#
if __name__ == '__main__':
    # get environment variables from .env
    load_dotenv()

    # Start a pool of connections
    pool = start_pool()

    # insert a default starting user
    #insert_starting_user()

    # Start a webserver
    app.run(port=int(os.environ.get('PORT', '8080')))
