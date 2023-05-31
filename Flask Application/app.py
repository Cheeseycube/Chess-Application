import io
import os
import flask
import flask_login
from flask import Flask, render_template, request, flash, session
from dotenv import load_dotenv
import ChessDatabase as ChessDB
import ChessCom
import chess.pgn
import chess
import re
from flask_login import LoginManager
from turbo_flask import Turbo
from datetime import timedelta







# log in
# https://flask-login.readthedocs.io/en/latest/

# CX_oracle docs cover basically everything: https://cx-oracle.readthedocs.io/en/latest/

# return json
#https://stackoverflow.com/questions/22195065/how-to-send-a-json-object-using-html-form-data
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
turbo = Turbo(app)
app.secret_key = 'secret-string'
login_manager = LoginManager()
login_manager.init_app(app)


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(user_name):
    userData = ChessDB.getUser(user_name)
    if userData is None:
        return
    user = User()
    user.id = userData['USERID']
    user.name = userData['USERNAME']
    return user


@login_manager.request_loader
def request_loader(request):
    userName = request.form.get('name')
    userData = ChessDB.getUser(userName)
    if userData is None:
        return
    user = User()
    user.id = userData['USERID']
    user.name = userData['USERNAME']
    return user


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401


@app.context_processor
def inject_load():
    global isLoading
    return {'loading': isLoading}


# This is the home page
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create_account', methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        # getting input with name = fname in HTML form
        user_name = request.form.get("name")
        password = request.form.get("password")
        res = ChessDB.addUser(user_name, password)
        if res[0] == -1:
            flash(res[1], 'error')
            return render_template('create_account_view.html')
        else:
            flash(res[1])
            return flask.redirect(flask.url_for('login'))
    return render_template('create_account_view.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_name = request.form.get("name")
        password = request.form.get("password")

        # checking credentials
        check_results = ChessDB.check_credentials(user_name, password)
        if check_results[0]:
            user = User()
            user.id = user_name
            flask_login.login_user(user)
            return flask.redirect(flask.url_for('view_profile'))
        else:
            flash(check_results[1], 'error')
            return render_template('login_view.html')
    return render_template('login_view.html')


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('index'))


# show the 5 most recent games perhaps
@app.route('/profile')
@flask_login.login_required
def view_profile():
    return render_template('profile_view.html', name=flask_login.current_user.name)


@app.route('/addGames', methods=["GET", "POST"])
@flask_login.login_required
def addGames():
    global isLoading
    if request.method == "POST":
        # add games
        print("add games tasks are executing")
        gameCol = ChessCom.GameCollection()
        gameCol.get_month_games(request.form.get("userName"), request.form.get("year"), request.form.get("month"))
        ChessDB.add_multiple_Games(gameCol, flask_login.current_user.id, 'Chess.com')
        isLoading = False
        return flask.redirect(flask.url_for('viewGames'))
    return render_template('addGames_view.html')


@app.route('/viewGames', methods=['GET', 'POST'])
@flask_login.login_required
def viewGames():
    """if request.method == "POST":
        cur_game = request.form.get("cur_game")
        print(cur_game)
        return flask.redirect(flask.url_for('analyze_game', pgnid=cur_game))"""
    games = ChessDB.get_all_games(flask_login.current_user.id)
    return render_template('games_view.html', games=games)


def convert_seconds(seconds):
    if seconds < 60:
        if seconds < 10:
            return f"0:0{seconds:.1f}"
        else:
            return f"0:{seconds:.1f}"
    if seconds < 3600:  # Less than an hour
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    else:  # An hour or more
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 3600) % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@app.route('/analyze/gameID:<gameid>', methods=['GET', 'POST'])
@flask_login.login_required
def analyze_game(gameid):
    game = ChessDB.get_game_by_id(gameid)
    if game is None:
        return "No game found"
    encoded_pgn = ChessDB.getPGN(game['PGNID'])
    pgn = ChessDB.decodePGN(encoded_pgn)

    # Parse the PGN using python-chess library
    parsed_game = chess.pgn.read_game(io.StringIO(pgn))
    board = parsed_game.board()
    fen_positions = []

    # Iterate through the moves and collect FEN positions
    for move in parsed_game.mainline_moves():
        board.push(move)
        fen_positions.append(board.fen())

    # timestamp stuff
    timestamps = []
    timestamps_string = []

    # gives us a string in hh mm ss format
    for node in parsed_game.mainline():
        time_elapsed = node.clock()
        if time_elapsed is not None:
            if (time_elapsed < 60):
                time_elapsed = round(time_elapsed, 2)
            else:
                time_elapsed = int(time_elapsed)
            #time_str = str(timedelta(seconds=time_elapsed))
            time_str = convert_seconds(time_elapsed)
            print(f"{node.move}: {time_elapsed}")
            print(f"{node.move}: {time_str}")
            timestamps.append(time_elapsed)
            timestamps_string.append(time_str)

    # time control
    time_control = int(game['TIME_CONTROL'])
    time_control_string = str(timedelta(seconds=time_control))

    return render_template('analyze_game_view.html', given_game=game, given_pgn=pgn, fen_positions=fen_positions,
                           timestamps=timestamps, timestamps_string=timestamps_string, time_control=time_control,
                           time_control_string=time_control_string)

@app.route('/bootstrap_practice')
def bootstrap_practice():
    return render_template('bootstrap_practice.html')
################################################################################
#
# Initialization is done once at startup time
#
if __name__ == '__main__':
    # get environment variables from .env
    load_dotenv()

    # Start a pool of connections
    pool = ChessDB.makeConnectionPool(4)

    # global loading bool
    isLoading = False

    # Start a webserver
    app.run(port=int(os.environ.get('PORT', '8080')))
