from dahuffman import HuffmanCodec
import ChessCom

# python chess library: https://pypi.org/project/python-chess/
# python stockfish library: https://pypi.org/project/stockfish/
# python chess.com api: https://pypi.org/project/chess.com/
# chess.com api official documentation: https://www.chess.com/news/view/published-data-api#pubapi-general

# pgn compression resources:
# https://compress.max.fan/
# https://lichess.org/blog/Wqa7GiAAAOIpBLoY/developer-update-275-improved-game-compression
# https://pypi.org/project/dahuffman/


# Demo Ideas:
# Show source code using environment variables
# the application itself will be primarily accessible via a web link



if __name__ == '__main__':

    FebruaryGames = ChessCom.GameCollection()
    FebruaryGames.get_month_games("Cheesecube01", "2023", "02")

    # training the huffman encoder
    training_data = FebruaryGames.month_pgns_string
    codec = HuffmanCodec.from_data(training_data)

    # finding the longest pgn and encoding it
    largest_pgn = ""
    for pgn in FebruaryGames.month_pgns:
        if (len(largest_pgn) < len(pgn)):
            largest_pgn = pgn
    encodedPgn = codec.encode(largest_pgn)


    # adding to the database
    i = 0
    for game in FebruaryGames.month_games:
        i += 1
        if (i > 20):
            break
        print(f"Adding a pgn with length in bytes: {len(codec.encode(game.pgn))}")
        #ChessDB.addGame(game.date.replace(".", "-"), "Joseph", "Chess.com", codec.encode(game.pgn))

    # getting a single pgn from the database and decrypting it
    '''encodedPGN = ChessDB.getGames()
    unencodedPGN = codec.decode(encodedPGN)
    print(unencodedPGN)

    # playing that game on a chess board
    pgn = io.StringIO(unencodedPGN)
    first_game = chess.pgn.read_game(pgn)
    board = first_game.board()
    for move in first_game.mainline_moves():
        board.push(move)
        print(board)
        print()'''

    # getting the stockfish engine for use by the Chess API
    '''engine = chess.engine.SimpleEngine.popen_uci(
        r"stockfish_15.1_win_x64_avx2\stockfish-windows-2022-x86-64-avx2.exe")

    # the battle of the titans: who will win--stockfish or stockfish?
    board = chess.Board()
    while not board.is_game_over():
        result = engine.play(board, chess.engine.Limit(time=0.001))
        board.push(result.move)
        print(board)
        print()

    engine.quit()'''

    # Use NAGS in chess analyzer

    # TO DO: make a separate chess engine class to handle all this

