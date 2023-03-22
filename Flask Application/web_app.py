import os
import oracledb
from flask import Flask, render_template, request
from dotenv import load_dotenv
import ChessDatabase as ChessDB

# log in tutorials:
# https://flask-login.readthedocs.io/en/latest/
# https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login
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
# Doc link: https://cx-oracle.readthedocs.io/en/latest/user_guide/connection_handling.html#session-callbacks-for-setting-pooled-connection-state
#
def init_session(connection, requestedTag_ignored):
    cursor = connection.cursor()
    cursor.execute("""
        ALTER SESSION SET
          TIME_ZONE = 'UTC'
          NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI'""")


# Specify some routes
#
# The default route will display a welcome message:
#   http://127.0.0.1:8080/

app = Flask(__name__)

# Display a welcome message on the 'home' page
@app.route('/')
def index():
    return render_template('index.html')

# Show the username for a given id
@app.route('/user/<int:id>')
def show_username(id):
    global pool
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute("select userName from Users where userId = :id_bv", [id])
    # fetching the first row from the previously executed query
    r = cursor.fetchone()
    return (r[0] if r else "Unknown user id")

@app.route('/create_account', methods = ["GET", "POST"])
def create_account():
    if request.method == "POST":
        # getting input with name = fname in HTML form
        user_name = request.form.get("name")
        password = request.form.get("password")
        id_num = ChessDB.addUser(user_name, password)
        if id_num == -1:
            return f"Could not add {user_name} to the database"
        return f"Added {user_name} to the database with an ID number of: {id_num}"
    return render_template('create_account_view.html')

@app.route('/login', methods = ["GET", "POST"])
def login():
    return render_template('login_view.html')

################################################################################
#
# Initialization is done once at startup time
#
if __name__ == '__main__':
    # get environment variables from .env
    load_dotenv()

    # Start a pool of connections
    pool = ChessDB.makeConnectionPool(4)

    # Start a webserver
    app.run(port=int(os.environ.get('PORT', '8080')))
