from dahuffman import HuffmanCodec
import ChessDatabase as ChessDB
import ChessCom
import pygame
from pygame.locals import *

if __name__ == '__main__':
    FebruaryGames = ChessCom.GameCollection()
    FebruaryGames.get_month_games("Cheesecube01", "2023", "02")

    # training the huffman encoder
    training_data = FebruaryGames.month_pgns_string
    codec = HuffmanCodec.from_data(training_data)
    # getting a single pgn from the database and decrypting it
    encodedPGN = ChessDB.getGames()
    unencodedPGN = codec.decode(encodedPGN)
    print(unencodedPGN)

    # playing that game on a chess board
    '''pgn = io.StringIO(unencodedPGN)
    first_game = chess.pgn.read_game(pgn)
    board = first_game.board()
    for move in first_game.mainline_moves():
        board.push(move)
        print(board)
        val = input("Press 1 to continue, or 0 to quit")
        if (val != "1"):
            break
        print()'''



    # Pygame stuff

    # resizable window
    pygame.init()
    screen = pygame.display.set_mode((500, 500), HWSURFACE | DOUBLEBUF | RESIZABLE)
    pic = pygame.image.load("empty_board.png")
    screen.blit(pygame.transform.scale(pic, (500, 500)), (0, 0))
    pygame.display.flip()
    while True:
        pygame.event.pump()
        event = pygame.event.wait()
        if event.type == QUIT:
            pygame.display.quit()
        elif event.type == VIDEORESIZE:
            screen = pygame.display.set_mode(
                event.dict['size'], HWSURFACE | DOUBLEBUF | RESIZABLE)
            screen.blit(pygame.transform.scale(pic, event.dict['size']), (0, 0))
            pygame.display.flip()



