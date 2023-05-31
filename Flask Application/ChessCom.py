from chessdotcom import get_player_games_by_month_pgn


# python chess.com api wrapper: https://pypi.org/project/chess.com/
# chess.com api official documentation: https://www.chess.com/news/view/published-data-api#pubapi-general


# Defining a "Game" object
class Game:
    def __init__(self, date, white, black, white_elo, black_elo, result, termination, time_control, start_time,
                 end_time, link, pgn):
        self.date = date
        self.white = white
        self.black = black
        self.white_elo = white_elo
        self.black_elo = black_elo
        self.result = result
        self.termination = termination
        self.time_control = time_control
        self.start_time = start_time
        self.end_time = end_time
        self.link = link
        self.pgn = pgn


# Defining a Chess.com collection object
class GameCollection:
    def __init__(self):
        self.pgns = []
        self.pgns_string = ""
        self.games = []

    # returns a list of games, and sets the private fields
    def get_month_games(self, user, year, month):
        # Getting all games for a month
        month_games = get_player_games_by_month_pgn(user, year, month)
        all_games = month_games.text
        split_games = all_games.split('[Event')
        split_games.pop(0)  # popping first element b/c it is empty
        game_counter = 0

        # extracting individual games
        for game in split_games:
            game_counter += 1
            # splitting each game by \n and removing the first line because it is irrelevant
            game_lines = game.split('\n')
            game_lines.pop(0)

            # removing any blank lines
            while "" in game_lines:
                game_lines.remove("")

            # extracting the pgn
            pgn = game_lines.pop(len(game_lines) - 1)

            # formatting the strings so we can make a dictionary
            for x in range(len(game_lines)):
                game_lines[x] = game_lines[x].replace('[', '').replace(']', '').replace('"', '')

            # creating the dictionary
            game_dict = {}
            game_dict["Pgn"] = pgn
            for line in game_lines:
                command, description = line.strip().split(None, 1)
                game_dict[command] = description.strip()

            # adding the game and pgn to various collections
            self.pgns.append(pgn)
            self.pgns_string += pgn
            # if time control is invalid set to 0
            try:
                game_dict["TimeControl"] = int(game_dict["TimeControl"])
            except:
                game_dict["TimeControl"] = 0
            self.games.append(
                Game(game_dict["Date"], game_dict["White"], game_dict["Black"], game_dict["WhiteElo"],
                     game_dict["BlackElo"], game_dict["Result"], game_dict["Termination"],
                     game_dict["TimeControl"], game_dict["StartTime"],
                     game_dict["EndTime"], game_dict["Link"], pgn))
            # print(f"game {game_counter} date: {game_dict['Date']}")
            # ChessDB.addGame('2023-02-27', 'Joseph', huffEncode(big_pgn_string, pgn))

        return self.games

