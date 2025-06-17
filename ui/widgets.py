"""Helper rendering primitives used by the main UI loop."""

import pygame
from ui.config import *
from ui.assests import load_piece_images

def draw_board(surface, cell_size):
    """Draw the chess board grid onto ``surface``."""
    for x in range(8):
        for y in range(8):
            color = LIGHT if (x + y) % 2 == 0 else DARK
            pygame.draw.rect(surface, color, (x * cell_size, y * cell_size, cell_size, cell_size))
            
def draw_hovered(surface, cell_size, x, y):
    """Highlight the square under the mouse cursor."""
    hovered_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    hovered_surface.fill(hovered_color)
    surface.blit(hovered_surface, (x * cell_size , y * cell_size))
    
def draw_start_square(surface, cell_size, x, y):
    """Show the square where the piece originated during a drag."""
    hovered_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    hovered_surface.fill(start_square_color)
    surface.blit(hovered_surface, (x * cell_size , y * cell_size))
    
class Button:
    """Simple clickable UI element."""
    def __init__(self, rect, text, base_color, hover_color, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color
        self.action = action
        self.hovered = False

    def draw(self, surface, font):
        """Render the button using ``font`` on ``surface``."""
        color = self.hover_color if self.hovered else self.base_color
        pygame.draw.rect(surface, color, self.rect)
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        """Process mouse events and trigger the action when clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.action()

def draw_can_move_square(surface, cell_size, x, y):
    """Draw an indicator for a legal non-capturing move."""
    RADIUS = int(cell_size*0.15)
    centre = (cell_size // 2, cell_size // 2)
    circle_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(circle_surf, movable_color, centre, RADIUS)
    surface.blit(circle_surf, (x * cell_size , y * cell_size))

def draw_can_capture_square(surface, cell_size, x, y):
    """Draw an indicator for a legal capturing move."""
    RADIUS = int(cell_size*0.5)
    centre = (cell_size // 2, cell_size // 2)
    circle_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(circle_surf, movable_color, centre, RADIUS)
    pygame.draw.circle(circle_surf, (0, 0, 0, 0), centre, RADIUS*0.8)
    surface.blit(circle_surf, (x * cell_size , y * cell_size))

def show_promotion_options(surface, cell_size, col, side ='white'):
    """Overlay promotion choices when a pawn reaches the back rank."""
    images = load_piece_images(CELL_SIZE * 0.8, side)
    image_offset = cell_size * 0.1
    mask = pygame.Surface((cell_size * 8, cell_size*8), pygame.SRCALPHA)
    mask.fill((0,0,0,200))
    promotion_list = pygame.Surface((cell_size, cell_size*4), pygame.SRCALPHA)
    RADIUS = int(cell_size*0.5)
    if side =='white':
        queen = 'wq'
        rook ='wr'
        knight = 'wn'
        bishop = 'wb'
    else:
        queen = 'bq'
        rook = 'br'
        knight = 'bn'
        bishop = 'bb'
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size // 2), RADIUS)
    promotion_list.blit(images[queen], (0 * cell_size + image_offset, image_offset))
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size + cell_size // 2), RADIUS)
    promotion_list.blit(images[rook], (0 * cell_size + image_offset, cell_size + image_offset))
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size*2 + cell_size // 2), RADIUS)
    promotion_list.blit(images[knight], (0 * cell_size + image_offset, 2 * cell_size + image_offset))
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size*3 + cell_size // 2), RADIUS)
    promotion_list.blit(images[bishop], (0 * cell_size + image_offset, 3 * cell_size + image_offset))
    surface.blit(mask, (0,0))
    surface.blit(promotion_list, (cell_size * col , 0))

def bit_indices(n: int):
    """Yield positions of set bits, least-significant bit = position 0."""
    idx = 0
    while n:
        if n & 1:          # check LSB
            yield idx
        n >>= 1            # drop LSB
        idx += 1

def draw_movable_squares(surface, board, cell_size, moves):
    """Visualise possible destination squares for the selected piece."""
    for i in bit_indices(moves):
        row, col = divmod(i, 8)
        if board[7-row][col] == '--':
            draw_can_move_square(surface, cell_size, col, 7-row)
        else:
            draw_can_capture_square(surface, cell_size, col, 7-row)
            
def draw_labels(surface, font, side, cell_size, label_offset):
    """Render file and rank labels around the board edges."""
    for i in range(8):
        file_color = DARK if i % 2 == 0 else LIGHT
        rank_color = LIGHT if file_color == DARK else DARK

        # File labels (a-h)
        text = font.render(LETTERS[i] if side == 'white' else LETTERS[7-i], True, rank_color)
        x = i * cell_size + int(cell_size * label_offset) - text.get_width() // 2
        y = BOARD_SIZE - text.get_height()
        surface.blit(text, (x, y))

        # Rank labels (1-8)
        rank = str(8 - i) if side == 'white' else str(i + 1)
        text = font.render(rank, True, file_color)
        x = text.get_width() // 2
        y = i * cell_size + int(cell_size * (1-label_offset)) - text.get_height() // 2
        surface.blit(text, (x, y))

def draw_pieces(surface, board_pos, images, side, cell_size):
    """Draw all chess pieces at their current positions."""
    for i in range(8):
        for j in range(8):
            if side == 'white':
                piece = board_pos[i][j]
                y, x = i, j
            else:
                piece = board_pos[7-i][j]
                y, x = i, j
            if piece != '--':
                surface.blit(images[piece], (x * cell_size, y * cell_size))
                
def display_end_scene(surface: pygame.Surface, win_side):
    """Show a simple end-of-game message overlay."""
    end_board = pygame.Surface((CELL_SIZE *5, CELL_SIZE*3))
    end_board.fill(END_SCENE_COLOR)
    font = pygame.font.Font(None, 100)
    
    # put a label for who won
    notify_label = font.render(f"{win_side} won!", True, TEXT_COLOR)
    end_board.blit(notify_label, (end_board.get_width()//2 - notify_label.get_width()//2, end_board.get_height()*0.2))    
    
    surface.blit(end_board, (surface.get_width()//2 - end_board.get_width()//2, surface.get_height()//2 - end_board.get_height()//2))