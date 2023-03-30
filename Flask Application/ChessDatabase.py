import oracledb
import os
from dotenv import load_dotenv
import bcrypt
from dahuffman import HuffmanCodec

# If using oracle (locally hosted database): https://www.oracle.com/database/technologies/appdev/python/quickstartpythononprem.html

# If using oracle autonomous database: https://www.oracle.com/database/technologies/appdev/python/quickstartpython.html

# if using sqlite3 locally hosted database: https://towardsdatascience.com/starting-with-sql-in-python-948e529586f2

# Indexing is useful if my database gets large

''' Documentation:
        Games Table:
            userID int            # Foreign Key for USERS
            pgnID int             # Foreign Key for PGNS
            datePlayed date
            platform varchar(20)  # chess.com, lichess, otb, etc...
            white varchar(50)
            black varchar(50)
            white_elo number(4)
            black_elo number(4)
            game_result varchar(5)
            termination varchar(70)
            time_control number(4)
            link varchar(60)
            
        Users Table:
            userID NUMBER generated by default as identity   # Primary Key
            userName varchar(50) UNIQUE                      # If a null value is provided, internal app logic should prevent insertion
            userPassword raw(70) UNIQUE                      # If a null value is provided, internal app logic should prevent insertion
            hashSalt raw(40)                                 # This will almost certainly be unique and will never be null
            
        PGNS Table:
            pgnID NUMBER generated by default as identity    # Primary Key
            pgn raw(4000) UNIQUE                             # varbinary(4000) equivalent
            '''

# connection pools will be stored in this global variable
pool = None


# this is veeeeeery broken
def addGame(given_date, given_userID, given_platform, given_pgn):
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use

    # should check for duplicates first...

    # insert into Games table
    sql_statement = ("insert into Games (USERID, datePlayed, platform, pgn)"
                     "values(TO_DATE(:newdate, 'YYYY-MM-DD'), :newplatform, :user_id, :newpgn)")
    cursor.execute(sql_statement, [given_userID, given_date, given_platform, given_pgn])
    print(cursor.rowcount, "row inserted")

    connection.commit()  # close the connection
    print("connection closed")


def addPGN(game, encoded_pgn):
    # setting up the connection
    global pool
    if pool is None:
        print("Connection pool was null, aborting addPGN operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()

    # try to add the pgn, if duplicate found return original
    pgn_id = cursor.var(int)
    sql_statement = "insert into PGNS(PGN) values(:pgn_bv) returning PGNID into :id_bv"
    try:
        cursor.execute(sql_statement, [encoded_pgn, pgn_id])
        # returning new pgn's id number
        return pgn_id.getvalue()[0]
    except oracledb.DataError as e:
        error_obj, = e.args
        print("error adding pgn to database, see errors.txt")
        print(f"error message: {error_obj}")
        error_file = open('errors.txt', 'w')
        error_file.write(game.pgn + "\n")
        error_file.write(game.link + "\n\n")
        connection.commit()
        # returning -1 means the pgn was not added and there is no duplicate
        return -1
    except oracledb.IntegrityError as e:
        error_obj = e.args
        print("Duplicate pgn was not added, returning original pgn's id number, see errors.txt for the affected pgn")
        print(f"error message: {error_obj}")
        error_file = open('errors.txt', 'w')
        error_file.write(game.pgn + "\n")
        error_file.write(game.link + "\n\n")
        connection.commit()
        # return the original in the case of duplicate
        sql_statement = "select PGNID from PGNS WHERE PGN = :encoded_pgn_bv"
        cursor.execute(sql_statement, [encoded_pgn])
        columns = [col[0] for col in cursor.description]
        cursor.rowfactory = lambda *args: dict(zip(columns, args))
        data = cursor.fetchone()
        if data is None:
            print("this should literally be impossible")
        else:
            return data["PGNID"]

    return -1


def getPGN(idNum):
    # setting up the connection
    global pool
    if pool is None:
        print("Connection pool was null, aborting getPGN operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()

    sql_statement = "select PGN from PGNS where PGNID = :id_bv"
    cursor.execute(sql_statement, [idNum])
    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    data = cursor.fetchone()
    if data is None:
        return -1
    return data['PGN']

def add_multiple_Games(Games, userID, platform):
    # setting up the connection
    global pool
    if pool is None:
        print("Connection pool was null, aborting add_multiple_Games operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()

    # training the huffman encoder
    training_file = open('training_data.txt', 'r')
    training_data = training_file.read()
    codec = HuffmanCodec.from_data(training_data)

    for game in Games.games:

        # encode each game
        try:
            encoded_game = codec.encode(game.pgn)
        except:
            print("could not encode the given game: see errors.txt for the affected pgn")
            error_file = open('errors.txt', 'w')
            error_file.write(game.pgn + "\n")
            error_file.write(game.link + "\n\n")
            connection.commit()
            return

        # add each game's pgn to the pgn table and get the corresponding id num
        pgn_id = addPGN(game, encoded_game)
        if (pgn_id == -1):
            connection.commit()
            # error message should have been generated by addPGN()
            return
        # add each game to the games table
        date = game.date.replace(".", "-")
        sql_statement = ("insert into Games(USERID, PGNID, DATEPLAYED, PLATFORM)"
                         "values(:id_bv, :pgn_id_bv, TO_DATE(:date_bv, 'YYYY-MM-DD'), :platform_bv)")
        cursor.execute(sql_statement, userID, pgn_id, date, platform)

    connection.commit()


# I think this only returns one game
def get_games_by_date(userID, date):
    # setting up the connection
    global pool
    if pool is None:
        print("Connection pool was null, aborting add_multiple_Games operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()

    # get pgn id
    sql_statement = ("select PGNID from Games where DATEPLAYED = TO_DATE(:date_bv, 'YYYY-MM-DD') and USERID = :id_bv")
    cursor.execute(sql_statement, [date, userID])
    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    data = cursor.fetchone()
    if data is None:
        return "no games found"

    # get the encoded pgn
    pgn = getPGN(data["PGN"])

    # training the huffman encoder
    training_file = open('training_data.txt', 'r')
    training_data = training_file.read()
    codec = HuffmanCodec.from_data(training_data)
    # returning decoded pgn
    return codec.decode(pgn)


def get_most_recent_game(userID):
    # setting up the connection
    global pool
    if pool is None:
        print("Connection pool was null, aborting get_most_recent_game operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()

    sql_statement = "select MAX(DATEPLAYED) from Games where USERID = :id_bv"
    cursor.execute(sql_statement, [userID])

    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    latest_date = cursor.fetchone()
    print(latest_date['MAX(DATEPLAYED)'])

    sql_statement = ("select PGNID from Games where DATEPLAYED = :latest_date_bv")
    cursor.execute(sql_statement, [latest_date['MAX(DATEPLAYED)']])

    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    data = cursor.fetchone()
    if (data is None):
        return "no games found"
    pgn_id = data["PGNID"]

    pgn = getPGN(pgn_id)
    # training the huffman encoder
    training_file = open('training_data.txt', 'r')
    training_data = training_file.read()
    codec = HuffmanCodec.from_data(training_data)
    return codec.decode(pgn)


# Uses the global field "pool" as defined by makeConnectionPool
def addUser(userName, password):
    # checking for valid inputs
    if userName is None:
        print("cannot insert null userName")
        return -1
    if password is None:
        print("cannot insert null password")
        return -1

    if (len(userName) < 1):
        return -1, "Username must be at least one character"
    if (len(password) < 7):
        return -1, "Password must be at least 7 characters"

    # setting up the connection
    global pool
    if pool is None:
        print("Connection pool was null, aborting addUser operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()
    id_num = cursor.var(int)

    # hashing the password
    password = bytes(password, 'utf-8')
    salt = bcrypt.gensalt()
    password_hashed = bcrypt.hashpw(password, salt)

    # Is the userName available?
    matches = cursor.execute("select 1 from Users where userName = :userName_bv", userName_bv=userName)
    for row in matches:
        if row[0] is not None:
            print("The provided username has already been taken, please provide another one")
            connection.commit()
            return -1, "The provided username has already been taken, please provide another one"

    # Is the password (post-hashing) available?
    matches = cursor.execute("select 1 from Users where userPassword = :userPassword_bv",
                             userPassword_bv=password_hashed)
    for row in matches:
        if row[0] is not None:
            print("The provided password has already been taken, please provide another one")
            connection.commit()
            return -1, "The provided password has already been taken, please provide another one"

    # inserting into the database
    sql_statement = ("insert into Users (userName, userPassword, hashSalt)"
                     "values (:userName_bv, :userPassword_bv, :hashSalt_bv)"
                     "returning userID into :id_bv")
    try:
        cursor.execute(sql_statement, [userName, password_hashed, salt, id_num])
    except oracledb.IntegrityError:
        print("Your password or username is already in use, aborting add operation.")
        connection.commit()
        return -1, "Your password or username is already in use, aborting add operation."

    print(f"Successfully added {userName} to the database with an id of {id_num.getvalue()[0]}")
    connection.commit()
    # returning the new user's id number
    return id_num.getvalue()[0], f"Successfully added {userName} to the database with an id of {id_num.getvalue()[0]}"


def check_credentials(userName, password):
    global pool
    if pool is None:
        print("Connection pool was null, aborting verify password operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()

    cursor.execute("select * from Users where userName = :userName_bv", userName_bv=userName)
    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    data = cursor.fetchone()
    if data is None:
        print("invalid username")
        connection.commit()
        return (False, 'invalid username')
    else:
        original_password_hashed = data['USERPASSWORD']
        given_password = bytes(password, 'utf-8')
        given_password_hashed = bcrypt.hashpw(given_password, data['HASHSALT'])
        if original_password_hashed == given_password_hashed:
            connection.commit()
            return (True, None)
        else:
            print("invalid password")
            connection.commit()
            return (False, 'invalid password')


# returns a single connection to the database: mainly used for testing
def makeConnection():
    connection = oracledb.connect(
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD"),
        dsn="(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)("
            "host=adb.us-ashburn-1.oraclecloud.com))(connect_data=("
            "service_name=g83c4ff870b21c6_chessdatabase_high.adb.oraclecloud.com))(security=("
            "ssl_server_dn_match=yes)))",

        config_dir="../Oracle Wallet",
        wallet_location="Oracle Wallet",
        wallet_password=os.getenv("PASSWORD")
    )
    print("connection established")
    return connection


# sets the global "pool" variable for use by other functions
def makeConnectionPool(pool_size):
    pool_min = pool_size
    pool_max = pool_size
    pool_inc = 0
    pool_gmd = oracledb.SPOOL_ATTRVAL_WAIT

    _pool = oracledb.SessionPool(user=os.getenv("USER"),
                                 password=os.getenv("PASSWORD"),
                                 dsn="(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)("
                                     "host=adb.us-ashburn-1.oraclecloud.com))(connect_data=("
                                     "service_name=g83c4ff870b21c6_chessdatabase_high.adb.oraclecloud.com))(security=("
                                     "ssl_server_dn_match=yes)))",
                                 config_dir="../Oracle Wallet",
                                 wallet_location="Oracle Wallet",
                                 wallet_password=os.getenv("PASSWORD"),
                                 min=pool_min,
                                 max=pool_max,
                                 increment=pool_inc,
                                 threaded=True,
                                 getmode=pool_gmd)
    global pool
    pool = _pool
    print("connection pool established")


def clearDatabase():
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use
    cursor.execute("drop table Games")
    cursor.execute("drop table Users")
    cursor.execute("drop table PGNS")
    connection.commit()
    print("database cleared")


def initializeDatabase():
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use
    # create Users and Games tables
    cursor.execute("""
    create table Users(userID NUMBER generated by default as identity, userName varchar(50) 
    UNIQUE, userPassword raw(70) UNIQUE, hashSalt raw(40), PRIMARY KEY (userID))""")

    cursor.execute("""
    create table PGNS(pgnID NUMBER generated by default as identity, PRIMARY KEY (pgnID), pgn raw(4000) UNIQUE )""")

    cursor.execute("""
    create table Games(userID int, FOREIGN KEY (userID) REFERENCES USERS(userID) ON DELETE CASCADE, 
    pgnID int, FOREIGN KEY (pgnID) REFERENCES PGNS(pgnID), datePlayed date, platform varchar(20), white varchar(50), black varchar(50),
    white_elo number(4), black_elo number(4), game_result varchar(5), termination varchar(70),
    time_control number(4), link varchar(60))""")

    connection.commit()
    print("database initialized")


def old_getUsers():
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use

    for row in cursor.execute('select userName from Users'):
        return row[0]
    connection.commit()


# returns some kind of list of all users
def get_allUsers():
    connection = makeConnection()
    cursor = connection.cursor()
    res = []
    for row in cursor.execute("select userName from Users"):
        res.append(row[0])
    return res


# returns a user dict or None if the user is not found
def getUser(user_name):
    # setting up the connection
    global pool
    if pool is None:
        print("Connection pool was null, aborting addUser operation")
        return -1
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute("select * from Users where USERNAME = :name_bv", [user_name])
    columns = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    data = cursor.fetchone()
    connection.commit()
    return data


if __name__ == '__main__':
    load_dotenv()
    print("welcome")
    #clearDatabase()
    #initializeDatabase()

    # print(get_allUsers())
    # makeConnection()
    # makeConnectionPool(4)

    # print(addUser('Gina', 'dkfjsdkfj'))

    '''password = 'dsjfdskjfsdkjflkdsjfkl'
    print(len(password))
    password = bytes(password, 'utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)

    print(f"password: {password}, password type: {type(password)}")
    print(f"salt: {salt} salt type: {type(salt)}")
    print(len(salt))
    print(f"hashed: {hashed} hashed type: {type(hashed)}")
    print(len(hashed))'''
