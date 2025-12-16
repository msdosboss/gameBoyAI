import random
from pyboy import PyBoy
from pyboy.utils import WindowEvent


def printBoard(game_map):
    for row in game_map:
        rowStr = ""
        for tile in row:
            if (tile is True):
                rowStr += "#"
            else:
                rowStr += "."
        print(rowStr)
    print("")


def readPieces(pyboy):
    # next_piece, current_piece
    return pyboy.memory[0xC213], pyboy.memory[0xC203]


def readBoard(pyboy):
    BASE = 0xC800
    TILEMAP_WIDTH = 32

    PLAYFIELD_X = 2
    PLAYFIELD_Y = 2
    WIDTH = 10
    HEIGHT = 16

    game_map = []

    for y in range(HEIGHT):
        addr = BASE + (PLAYFIELD_Y + y) * TILEMAP_WIDTH + PLAYFIELD_X
        row = pyboy.memory[addr:addr + WIDTH]
        game_row = []
        for tile in row:
            # 0x2F and 0x30 represent black space
            if (tile not in (0x2F, 0x30)):
                game_row.append(True)
            else:
                game_row.append(False)
        game_map.append(game_row)

    return game_map


def column_heights(game_map):
    height = len(game_map)
    width = len(game_map[0])

    heights = [0] * width

    for x in range(width):
        for y in range(height):  # bottom → top
            if game_map[y][x]:
                heights[x] = y + 1

    return heights


def count_holes(game_map, column_heights):
    width = len(game_map[0])
    holes = 0

    for x in range(width):
        for y in range(column_heights[x]):
            if not game_map[y][x]:
                holes += 1

    return holes


def genPieceVector(pieceValue):
    total_pieces = 7
    piece_vector = [0] * total_pieces
    if (pieceValue <= 24):
        piece_vector[pieceValue // 4] = 1
    return piece_vector


def createFeatures(game_map, pieces):
    # Bottom row should be index 0
    game_map = list(reversed(game_map))

    heights = column_heights(game_map)
    totalHeight = sum(heights)

    bumpiness = sum(
        abs(heights[i] - heights[i + 1])
        for i in range(len(heights) - 1)
    )

    holes = count_holes(game_map, heights)

    wellDepthTotal = 0
    for i in range(len(heights)):
        left = heights[i - 1] if i > 0 else float('inf')
        right = heights[i + 1] if i < len(heights) - 1 else float('inf')

        if heights[i] < left and heights[i] < right:
            wellDepthTotal += min(left, right) - heights[i]

    return {
        "column_heights": heights,
        "aggregate_height": totalHeight,
        "holes": holes,
        "bumpiness": bumpiness,
        "well_depth": wellDepthTotal,
        "current_piece": genPieceVector(pieces[0]),
        "next_piece": genPieceVector(pieces[1]),
    }


def actOnInstruction(pyboy: PyBoy, move_dict: dict):
    rotation = move_dict["rotation"]
    x_pos = move_dict["x_pos"]
    for _ in range(rotation):
        pyboy.button_press('a')
        pyboy.tick(2)
        pyboy.button_release('a')
        pyboy.tick(1)
    center_anchor = 4
    if (x_pos > center_anchor):
        right_click_count = x_pos - center_anchor
        for _ in range(right_click_count):
            pyboy.button_press('right')
            pyboy.tick(2)
            pyboy.button_release('right')
            pyboy.tick(1)
    elif (x_pos < center_anchor):
        left_click_count = center_anchor - x_pos
        for _ in range(left_click_count):
            pyboy.button_press('left')
            pyboy.tick(2)
            pyboy.button_release('left')
            pyboy.tick(1)


def isCollided(game_map, piece_offsets, x_pos, y_pos):
    for offset in piece_offsets:
        if (offset[1] + y_pos > 15 or offset[0] + x_pos > 9):
            continue
        if (game_map[offset[1] + y_pos][offset[0] + x_pos] is True):
            # right now it is just assuming the lowest Y It needs change the y based on which block collided
            return True

    return False


def simulateMove(game_map, piece, rotations, x_pos):
    if (piece > 6):
        print("Not a valid piece passed to simulateMove")
        return None

    # boards was upside down
    game_map.reverse()

    PIECES = [
        # L block 0x0 (0)
        [
            [(0, 0), (0, 1), (1, 1), (2, 1)],
            [(0, 0), (1, 0), (1, 1), (1, 2)],
            [(0, 0), (1, 0), (2, 0), (2, 1)],
            [(0, 0), (0, 1), (0, 2), (1, 0)]
        ],
        # J blcok 0x4 (4)
        [
            [(0, 1), (1, 1), (2, 1), (2, 0)],
            [(0, 0), (1, 0), (1, 1), (1, 2)],
            [(0, 0), (0, 1), (1, 0), (2, 0)],
            [(0, 0), (0, 1), (0, 2), (1, 2)]
        ],
        # I block 0x8 (8)
        [
            [(0, 0), (1, 0), (2, 0), (3, 0)],
            [(1, 0), (1, 1), (1, 2), (1, 3)]
        ],
        # O block 0xc (12)
        [
            [(0, 0), (1, 0), (0, 1), (1, 1)]
        ],
        # Z block 0x10 (16)
        [
            [(0, 1), (1, 1), (1, 0), (2, 0)],
            [(0, 0), (0, 1), (1, 1), (1, 2)]
        ],
        # S blcok 0x14 (20)
        [
            [(0, 0), (1, 0), (1, 1), (2, 1)],
            [(0, 2), (0, 1), (1, 1), (1, 0)]
        ],
        # T block 0x18 (24)
        [
            [(0, 1), (1, 1), (1, 0), (2, 1)],
            [(1, 0), (1, 1), (0, 1), (1, 2)],
            [(0, 0), (1, 0), (2, 0), (1, 1)],
            [(0, 0), (0, 1), (0, 2), (1, 1)]
        ]
    ]
    # printBoard(game_map)
    # this assumes that the pieces memory has already been divided by 4
    # mods is to prevent out of bounds read if to many rotations were given
    piece_offsets = PIECES[piece][rotations % len(PIECES[piece])]
    max_height = 16
    # +4 for the upwards I block
    y = max_height + 4
    while (isCollided(game_map, piece_offsets, x_pos, y) is False):
        y -= 1

    for offset in piece_offsets:
        print(y + 1 + offset[1])
        # this means your moves loses the game
        if (y + 1 + offset[1] > 15):
            break
        game_map[y + 1 + offset[1]][x_pos - 1 + offset[0]] = True

    game_map.reverse()
    printBoard(game_map)

    return game_map


if __name__ == "__main__":
    pyboy = PyBoy('Tetris.gb', scale=4)
    with open("ingame.state", "rb") as f:
        pyboy.load_state(f)

    tickCount = 1
    while (True):
        # pyboy.button_press('a')
        # pyboy.tick(2)
        # pyboy.button_release('a')
        prev_pieces = readPieces(pyboy)
        pyboy.tick(1)
        game_map = readBoard(pyboy)
        pieces = readPieces(pyboy)
        features = createFeatures(game_map, pieces)
        # print(features)
        # printBoard(game_map)
        if (pieces != prev_pieces):
            '''move_dict = {
                "rotation": random.randint(0, 3),
                "x_pos": random.randint(0, 9)
            }'''
            move_dict = {
                "rotation": 1,
                "x_pos": 4
            }
            actOnInstruction(pyboy, move_dict)
            simulateMove(game_map, pieces[1] // 4, 1, 4)
        tickCount += 1
    pyboy.stop()
