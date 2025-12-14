from pyboy import PyBoy
from pyboy.utils import WindowEvent


def readPieces(pyboy):
    BASE = 0xC800
    TILEMAP_WIDTH = 32

    PLAYFIELD_X = 2
    PLAYFIELD_Y = 2
    WIDTH = 10
    HEIGHT = 18

    for y in range(HEIGHT):
        addr = BASE + (PLAYFIELD_Y + y) * TILEMAP_WIDTH + PLAYFIELD_X
        row = pyboy.memory[addr : addr + WIDTH]

        # 0x2F / 0x30-ish are empty tiles in GB Tetris
        print("".join("#" if tile not in (0x2F, 0x30) else "." for tile in row))


if __name__ == "__main__":
    pyboy = PyBoy('Tetris.gb', scale=4)
    while (True):
        # pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        # pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
        pyboy.tick(4)
        readPieces(pyboy)
        # pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        # pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
    pyboy.stop()
