import oracledb
import os
from dotenv import load_dotenv
# If using oracle (locally hosted database): https://www.oracle.com/database/technologies/appdev/python/quickstartpythononprem.html

# If using oracle autonomous database: https://www.oracle.com/database/technologies/appdev/python/quickstartpython.html #first-option-tab

# if using sqlite3 locally hosted database: https://towardsdatascience.com/starting-with-sql-in-python-948e529586f2

# Indexing is useful if my database gets large

''' Documentation:
        Games Table:
            datePlayed date
            userName varchar(50)
            platform varchar(20)  # chess.com, lichess, otb, etc...
            pgn raw(3000)''' # this is the oracle equivalent of varbinary(3000)


def addGame(given_date, given_userName, given_platform, given_pgn):
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use

    # use "INSERT IGNORE" to avoid inserting duplicates

    # insert into Games table
    sql_statement = ("insert into Games (datePlayed, userName, platform, pgn) "
                     "values(TO_DATE(:newdate, 'YYYY-MM-DD'), :newplatform, :newuser, :newpgn)")
    #sql_statement = """insert into Games (datePlayed, userName, pgn) values(TO_DATE('2023-02-23', 'YYY-MM-DD'), 'user_name', 'pgn_')"""
    #cursor.execute(sql_statement, ["generic_name"])
    cursor.execute(sql_statement, [given_date, given_userName, given_platform, given_pgn])
    print(cursor.rowcount, "row inserted")

    connection.commit()  # close the connection
    print("connection closed")

# todo: make addMultipleGames() or something like that

def makeConnection():
    connection = oracledb.connect(
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD"),
        dsn="(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)("
            "host=adb.us-ashburn-1.oraclecloud.com))(connect_data=("
            "service_name=g83c4ff870b21c6_chessdatabase_high.adb.oraclecloud.com))(security=("
            "ssl_server_dn_match=yes)))",

        config_dir="Oracle Wallet",
        wallet_location="Oracle Wallet",
        wallet_password=os.getenv("PASSWORD")
    )
    print("connection established")
    return connection


def clearDatabase():
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use
    cursor.execute("drop table Games")
    cursor.execute("drop table Users")
    connection.commit()
    print("database cleared")


def initializeDatabase():
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use
    # create Users and Games tables
    cursor.execute("""create table Users(userID NUMBER generated by default as identity, userName varchar(50) NOT NULL, PRIMARY KEY (userID))""")
    cursor.execute("""create table Games(userID int, FOREIGN KEY (userID) REFERENCES Users(userID) ON DELETE CASCADE, 
    datePlayed date, platform varchar(20), pgn raw(3000))""")
    connection.commit()
    print("database initialized")


def getGames():
    connection = makeConnection()
    cursor = connection.cursor()  # defining cursor for later use

    for row in cursor.execute('select pgn from Games'):
        return row[0]


if __name__ == '__main__':
    load_dotenv()
    print("welcome")
    #os.environ["CONNECTION_STRING"] =
    # "(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(""host=adb.us-ashburn-1.oraclecloud.com))(connect_data=(""service_name=g83c4ff870b21c6_chessdatabase_high.adb.oraclecloud.com))(security=(""ssl_server_dn_match=yes)))"

    makeConnection()
    #clearDatabase()
    #initializeDatabase()

    # drop Games table
    #connection = makeConnection()
    #cursor = connection[1].cursor()
    #cursor.execute("drop table Games")

    # create Games table
    #cursor.execute("""create table Games(datePlayed date, userName varchar(50),
    #platform varchar(20), pgn raw(3000))""")

    # insert into Games table
    #cursor.execute("insert into Games (datePlayed, userName, pgn) values(TO_DATE('2023-02-23', 'YYYY-MM-DD'), 'Joseph', 'sample_pgn')")
    #print(cursor.rowcount, "row(s) inserted")

    # printing out the contents of Games
    #for row in cursor.execute('select dateVar, userName from Games'):
        #print(f"date: {row[0]} user: {row[1]}")

    #for row in cursor.execute('select pgn from Games'):
     #   print(row)