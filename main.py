from pyboy import PyBoy
from pyboy.utils import WindowEvent


def readPieces(pyboy):
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

    # del game_map[len(game_map) - 2:]

    for row in game_map:
        rowStr = ""
        for tile in row:
            if (tile is True):
                rowStr += "#"
            else:
                rowStr += "."
        print(rowStr)


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
    if(pieceValue <= 24):
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


if __name__ == "__main__":
    pyboy = PyBoy('Tetris.gb', scale=4)
    tickCount = 0
    move_dict = {
        "rotation" : 3,
        "x_pos": 7
    }
    while (True):
        # if ((tickCount % 360) == 0):
            # actOnInstruction(pyboy, move_dict)
        # pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        # pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
        pyboy.button_press('a')
        pyboy.tick(2)
        pyboy.button_release('a')
        pyboy.tick(1)
        game_map = readBoard(pyboy)
        pieces = readPieces(pyboy)
        features = createFeatures(game_map, pieces)
        print(features)
        tickCount += 1
        # print(game_map)
        # pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        # pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
    pyboy.stop()
