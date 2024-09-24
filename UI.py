
import os
try:
    import pygame
except ModuleNotFoundError:
    print("failed import, performing re-install")
    os.system('cmd /c "python -m pip install pygame"')
    import pygame
from pygame.locals import *

pygame.init()

FPSCLOCK = pygame.time.Clock()
screen = pygame.display.set_mode((1000, 600), RESIZABLE | DOUBLEBUF, 8)
screen.set_alpha(None)
pygame.event.set_allowed([QUIT, KEYDOWN, MOUSEBUTTONDOWN])
pygame.display.set_caption("Menu")

pygame.quit()