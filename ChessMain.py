"""
main driver file.
Responsible for handling user input and displaying current gamestate
"""
import time

import pygame as p
import ChessEngine
import BestMoveFinder
import tkinter as tk
from tkinter import messagebox

p.init()
BOARD_WIDTH = BOARD_HEIGHT = 512  # size of our board
MOVE_LOG_PANEL_WIDTH = 256
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8  # Dimension of our chess board is 8x8
SQ_SIZE = BOARD_WIDTH // DIMENSION  # size of each square
MAX_FPS = 30

# if a human is playing white,it'll be true, else if bot is playing, it'll be false
playerOne = False
playerTwo = False

# initialize global directory of images .This will be called exactly once in the main
IMAGES = {}

colors = [(240, 217, 181), (181, 136, 99)]  # light , dark squares


def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load('images/' + piece + '.png'), (SQ_SIZE, SQ_SIZE))
        # images can be accessed by IMAGES['wK']


def main():
    # main driver function , handles inputs and graphics update
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))  # set up the screen
    p.display.set_caption("Chess")
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    moveLogFont = p.font.Font(None, 24)

    global playerOne
    global playerTwo

    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()  # gets valid move for current state
    moveMade = False  # flag variable to check if move is made for update of valid moves
    animate = False  # flag variable to check when to animate piece movement
    gameOver = False  # keeps track of game state, if game is over or not
    loadImages()
    sqSelected = ()  # stores  last click of user as tuple (x,y)
    playerClicks = []  # keeps track of player clicks ( 2 Tuples : ex, (6,4)->(4,4))

    mode_selection = True
    selected_mode = None

    pvp_button_rect, ai_button_rect = drawModeSelection(screen)

    while mode_selection:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                return
            elif e.type == p.MOUSEBUTTONDOWN:
                x, y = p.mouse.get_pos()
                if pvp_button_rect.collidepoint(x, y):
                    selected_mode = "PvP"
                    mode_selection = False
                elif ai_button_rect.collidepoint(x, y):
                    selected_mode = "AI"
                    mode_selection = False

        drawModeSelection(screen)
        p.display.flip()
        clock.tick(MAX_FPS)

    if selected_mode == "PvP":
        playerOne = True
        playerTwo = True
    elif selected_mode == "AI":
        playerOne = True
        playerTwo = False

    drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)
    running = True
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        if gs.checkMate:  # restart the game, once check mate or stalemate
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, "Black Win by CheckMate")
            else:
                drawText(screen, "White Win by CheckMate")
        elif gs.staleMate:
            gameOver = True
            drawText(screen, "StaleMate")

        for e in p.event.get():
            if e.type == p.QUIT:  # exits the game
                running = False
                break
            elif e.type == p.MOUSEBUTTONDOWN:
                if humanTurn:
                    location = p.mouse.get_pos()  # x, y coordinate of mouse click
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    # determining which square user clicked

                    if sqSelected == (row, col) or row >= 8 or col >= 8:
                        # user clicked on same square twice, i.e. it needed to be unselected
                        sqSelected = ()
                        playerClicks = []

                    elif gs.board[row, col] != '--' or len(playerClicks) == 1:
                        # not allowing user to select empty square
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2:
                        # once 2 clicks are made to move the piece, move the piece
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)

                        for i in range(len(validMoves)):
                            if move == validMoves[i]:  # if move is valid, make a move
                                print(move.getChessNotation())  # print notation
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = ()
                                playerClicks = []  # empty both variables for next use
                                break
                        if not moveMade:
                            playerClicks = [sqSelected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    # if key entered is "z", undo moves
                    gs.undoMove()
                    animate = False
                    moveMade = True

                if e.key == p.K_r:
                    # if key entered is "r", undo moves
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

        if gameOver:  # if game is over, restart
            time.sleep(2)
            gs = ChessEngine.GameState()
            validMoves = gs.getValidMoves()
            sqSelected = ()
            playerClicks = []
            moveMade = False
            animate = False
            gameOver = False
        # AI move finder

        if not humanTurn:
            AIMove = BestMoveFinder.findBestMove(gs, validMoves)
            if AIMove is None:
                AIMove = BestMoveFinder.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = True

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False

        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)  # draw the board
        clock.tick(MAX_FPS)
        p.display.flip()


def highlightSquares(screen, gs, validMoves, sqSelected):
    # highlighting the possible moves of a piece
    if sqSelected != ():
        # empty square is not selected
        row, column = sqSelected
        if gs.board[row, column][0] == ('w' if gs.whiteToMove else 'b'):  # sq selected is a piece of current player

            # highlight the selected square
            surface = p.Surface((SQ_SIZE, SQ_SIZE))  # setting up the surface
            surface.set_alpha(150)  # setting transparency ,0 = transparent, 255=opaque
            surface.fill((106, 155, 65))
            screen.blit(surface, (column * SQ_SIZE, row * SQ_SIZE))

            # highlight potential moves
            surface.fill((250, 250, 122))
            for move in validMoves:
                if move.startRow == row and move.startCol == column:
                    # all potential moves of selected piece
                    screen.blit(surface, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))


def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont):
    # responsible for all graphics with current game state

    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, gs, moveLogFont)


def drawModeSelection(screen):
    screen.fill(p.Color("black"))  # Clear the screen

    title_font = p.font.Font(None, 48)
    title_text = title_font.render("Chess Game", True, p.Color("white"))
    title_rect = title_text.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 4))
    screen.blit(title_text, title_rect)

    button_width = 200
    button_height = 50
    button_padding = 20
    space_between_buttons = 20  # Adjust this value for the desired space

    pvp_button_rect = p.Rect(
        BOARD_WIDTH // 2 - button_width // 2,
        BOARD_HEIGHT // 2 - button_height - space_between_buttons // 2 - button_padding,
        button_width,
        button_height
    )

    ai_button_rect = p.Rect(
        BOARD_WIDTH // 2 - button_width // 2,
        BOARD_HEIGHT // 2 + space_between_buttons // 2 + button_padding,
        button_width,
        button_height
    )

    p.draw.rect(screen, p.Color("white"), pvp_button_rect, border_radius=10)
    p.draw.rect(screen, p.Color("white"), ai_button_rect, border_radius=10)

    pvp_font = p.font.Font(None, 36)
    ai_font = p.font.Font(None, 36)

    pvp_text = pvp_font.render("Player vs Player", True, p.Color("black"))
    ai_text = ai_font.render("Player vs AI", True, p.Color("black"))

    pvp_text_rect = pvp_text.get_rect(center=pvp_button_rect.center)
    ai_text_rect = ai_text.get_rect(center=ai_button_rect.center)

    screen.blit(pvp_text, pvp_text_rect)
    screen.blit(ai_text, ai_text_rect)

    return pvp_button_rect, ai_button_rect


def drawBoard(screen):
    # Draw the board, top left cell is always white

    global colors

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            # every other cell has same color, i.e. sum of row and column will be even/ odd for each color
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(screen, board):
    # draw the pieces using current gamestate

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r, c]
            if piece != '--':  # space is not empty
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawMoveLog(screen, gs, font):
    # draws the move log
    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("black"), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []

    for i in range(0, len(moveLog), 2):
        moveString = str(i // 2 + 1) + " . " + str(moveLog[i]) + " - "
        if i + 1 < len(moveLog):
            # making sure black made a move
            moveString += str(moveLog[i + 1]) + " "
        moveTexts.append(moveString)

    movesPerRow = 2
    padding = 5
    lineSpacing = 2
    textY = padding
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):  # within bounds of moves text
                text += moveTexts[i + j] + '  '
        textObject = font.render(text, True, p.Color('white'))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing
    p.display.flip()


def animateMove(move, screen, board, clock):
    global colors
    distanceRow = move.endRow - move.startRow
    distanceCol = move.endCol - move.startCol
    frameCount = 10  # frames per square

    for frame in range(frameCount + 1):
        r, c = (move.startRow + distanceRow * frame / frameCount, move.startCol + distanceCol * frame / frameCount)
        drawBoard(screen)
        drawPieces(screen, board)

        # erase piece from ending square, which is being moved, as it is already moved in makeMove function
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)

        # draw piece being captured into the square (if any)
        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enPassantRow = move.endRow + 1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                endSquare = p.Rect(move.endCol * SQ_SIZE, enPassantRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)

        # draw moving piece
        if move.pieceMoved in IMAGES:
            screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def drawText(screen, text):
    font = p.font.Font(None, 36)
    textObject = font.render(text, False, p.Color('Gray'))
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - textObject.get_width() / 2,
                                                                BOARD_HEIGHT / 2 - textObject.get_height() / 2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, False, p.Color("Black"))
    screen.blit(textObject, textLocation)
    p.display.flip()


if __name__ == "__main__":
    main()
