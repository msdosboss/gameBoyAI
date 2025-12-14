from pyboy import PyBoy
from pyboy.utils import WindowEvent

if __name__ == "__main__":
    pyboy = PyBoy('Tetris.gb')
    while (True):
        pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        # pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
        pyboy.tick(2)
        pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
        # pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
    pyboy.stop()
