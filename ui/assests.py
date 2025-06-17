import pygame
from ui.config import *

def load_piece_images(cell_size, side):
    piece_images = {}
    if side == 'white':
        for piece in PIECES:
            img = pygame.image.load(f'pieces/{piece}.png')
            piece_images[piece] = pygame.transform.scale(img, (cell_size, cell_size))
    else:
        for piece in PIECES:
            
            img = pygame.image.load(f'pieces/{piece}.png')
            piece = 'b' + piece[1] if piece.startswith('w') else 'w' + piece[1]
            piece_images[piece] = pygame.transform.scale(img, (cell_size, cell_size))
    return piece_images