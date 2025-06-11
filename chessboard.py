import pygame
from pygame import Surface
from chess_logic import *
import threading
from game import Game
import sys
game = Game()


# CHoose your side here
side = 'black'  # or 'black'


# --- Config and Constants ---
CELL_SIZE = 100
LABEL_OFFSET = 0.88
BOARD_SIZE = CELL_SIZE * 8
DARK = (118, 150,  86)
LIGHT = (238, 238, 210)
hovered_color = (144, 238, 144, 128)
start_square_color = (120, 200, 100, 128)
movable_color = (120, 200, 144, 100)
LETTERS = 'abcdefgh'
PIECES = ['wp', 'bp', 'wn', 'bn', 'wb', 'bb', 'wr', 'br', 'wq', 'bq', 'wk', 'bk']
END_SCENE_COLOR = (40,40,40) 
TEXT_COLOR = (152, 255, 152)

PIECE_TO_INDEX = {
            'wp': 0, 'wn': 1, 'wb': 2, 'wr': 3, 'wq': 4, 'wk': 5,
            'bp': 6, 'bn': 7, 'bb': 8, 'br': 9, 'bq': 10, 'bk': 11
        }


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

def draw_board(surface, cell_size):
    for x in range(8):
        for y in range(8):
            color = LIGHT if (x + y) % 2 == 0 else DARK
            pygame.draw.rect(surface, color, (x * cell_size, y * cell_size, cell_size, cell_size))
            
def draw_hovered(surface, cell_size, x, y):
    hovered_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    hovered_surface.fill(hovered_color)
    surface.blit(hovered_surface, (x * cell_size , y * cell_size))
    
def draw_start_square(surface, cell_size, x, y):
    hovered_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    hovered_surface.fill(start_square_color)
    surface.blit(hovered_surface, (x * cell_size , y * cell_size))
    


def draw_can_move_square(surface, cell_size, x, y):
    RADIUS = int(cell_size*0.15)
    centre = (cell_size // 2, cell_size // 2)
    circle_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(circle_surf, movable_color, centre, RADIUS)
    surface.blit(circle_surf, (x * cell_size , y * cell_size))

def draw_can_capture_square(surface, cell_size, x, y):
    RADIUS = int(cell_size*0.5)
    centre = (cell_size // 2, cell_size // 2)
    circle_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(circle_surf, movable_color, centre, RADIUS)
    pygame.draw.circle(circle_surf, (0, 0, 0, 0), centre, RADIUS*0.8)
    surface.blit(circle_surf, (x * cell_size , y * cell_size))

def show_promotion_options(surface, cell_size, col, side ='white'):
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
    for i in bit_indices(moves):
        row, col = divmod(i, 8)
        if board[7-row][col] == '--':
            draw_can_move_square(surface, cell_size, col, 7-row)
        else:
            draw_can_capture_square(surface, cell_size, col, 7-row)
def draw_labels(surface, font, side, cell_size, label_offset):
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
       
def quit_game():
    pygame.quit()
    sys.exit()
    
    
def play_again():
    game.reset()
    threading.Thread(target=game.start, args=(side, )).start()

class Button:
    def __init__(self, rect, text, base_color, hover_color, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color
        self.action = action
        self.hovered = False

    def draw(self, surface, font):
        color = self.hover_color if self.hovered else self.base_color
        pygame.draw.rect(surface, color, self.rect)
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.action()
        
def display_end_scene(surface: Surface, win_side):
    end_board = Surface((CELL_SIZE *5, CELL_SIZE*3))
    end_board.fill(END_SCENE_COLOR)
    font = pygame.font.Font(None, 100)
    
    # put a label for who won
    notify_label = font.render(f"{win_side} won!", True, TEXT_COLOR)
    end_board.blit(notify_label, (end_board.get_width()//2 - notify_label.get_width()//2, end_board.get_height()*0.2))
    
    
    # end scene, let you choose between rage quit or try again
    
    
    surface.blit(end_board, (surface.get_width()//2 - end_board.get_width()//2, surface.get_height()//2 - end_board.get_height()//2))
                
 
def opponent_play(chess: ChessLogic, board_state: list, moves: list) -> None:
    move = chess.get_best_move()
    if not move:
        game.moves = [0] * 64
        game.end = True
        return
    chess.push(move)
    board_state[:] = chess.get_chess_board()
    encoded_moves = chess.find_available_moves()
    if not encoded_moves:
        game.end = True
        game.moves = [0] * 64
        return
    game.moves[:] = chess.moves_to_data(encoded_moves)

def main():
    pygame.init()
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("chess engine hehehe")
    font = pygame.font.SysFont(None, 24, bold=True)
    
    piece_images = load_piece_images(CELL_SIZE, side )
    
    running = True
    
    end_buttons = []
    button_width, button_height = 200, 60
    spacing = 20
    end_w, end_h = (CELL_SIZE *5, CELL_SIZE*3)
    board_x = (screen.get_width() ) // 2
    board_y = (screen.get_height()) // 2 - 10

    quit_btn = Button(
        (board_x - button_width - spacing//2,
         board_y + 50,
         button_width,
         button_height),
        "Quit", (180, 50, 50), (255, 100, 100), quit_game)
    play_btn = Button(
        (board_x + spacing//2,
         board_y + 50,
         button_width,
         button_height),
        "Play Again", (50, 180, 50), (100, 255, 100), play_again)
    end_buttons = [quit_btn, play_btn]
    
    promotion = None
    dragging = False
    dragging_piece = None
    drag_start = (None, None)
    

    # Prepare the board surface
    board = Surface((BOARD_SIZE, BOARD_SIZE))
    board.fill((255, 255, 255))
    threading.Thread(target=game.start, args=(side, )).start()
    # Main loop
    while running:
        board.fill((255, 255, 255))
        draw_board(board, CELL_SIZE)
        draw_labels(board, font, side, CELL_SIZE, LABEL_OFFSET)
        draw_pieces(board, game.board_state, piece_images, 'white', CELL_SIZE)
        # game.start(side)
        
        if game.end:
            display_end_scene(board, side)
            for button in end_buttons:
                button.draw(board, pygame.font.Font(None, 40))
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.end:
                    for button in end_buttons:
                        button.handle_event(event)
                elif promotion is not None:
                    pass
                else:
                    mx, my = pygame.mouse.get_pos()
                    row = (my // CELL_SIZE)
                    col = (mx // CELL_SIZE)
                    if row < 0 or row > 7 or col < 0 or col > 7:
                        continue
                    if game.board_state[row][col] == '--':
                        continue
                    if not game.moves[(7-row)*8 + col]:
                        continue
                    
                    dragging_piece = game.board_state[row][col]
                    dragging = True
                    drag_start = (row, col)
                
            elif event.type == pygame.MOUSEBUTTONUP:
                if game.end:
                    pass
                elif promotion is not None:
                    mx, my = pygame.mouse.get_pos()
                    row = (my // CELL_SIZE)
                    col = (mx // CELL_SIZE)
                    row_promo, col_prommo = divmod(promotion, 8)
                    promote_piece = None
                    
                    if col == col_prommo:
                        if row == 0:
                            promote_piece = PROMO_Q 
                        elif row == 1:
                            promote_piece = PROMO_R
                        elif row == 2:
                            promote_piece = PROMO_N 
                        elif row == 3:
                            promote_piece = PROMO_B 
                        
                        if promote_piece is not None:
                           
                            
                            game.board_state[drag_start[0]][drag_start[1]] = '--'
                            move_to_push = encode_move((7-drag_start[0])*8 + drag_start[1], (row_promo)*8 + col_prommo, flag = game.chess.get_flag((7-drag_start[0])*8 + drag_start[1], (row_promo)*8 + col_prommo, promote_piece))
                            game.chess.push(move_to_push)
                            promotion = None
                            drag_start = (None, None)
                            dragging_piece = None
                            # moves_bb = chess.find_available_moves()
                            # moves = chess.moves_to_data(moves_bb)
                            game.moves = [0] * 64
                            game.board_state = game.chess.get_chess_board()
                            threading.Thread(target=(opponent_play), args=(game.chess, game.board_state, game.moves)).start()

                elif dragging:
                    mx, my = pygame.mouse.get_pos()
                    dragging = False
                    row = (my // CELL_SIZE)
                    col = (mx // CELL_SIZE)
                    if 0 <= row <= 7 and 0 <= col <= 7:
                        if (1 << (7-row) * 8 + col) & game.moves[(7-drag_start[0])*8 + drag_start[1]]:
                            if row == 0 and dragging_piece in ('wp', 'bp'):
                                promotion = (7-row)*8 + col
                                
                            if not promotion:
                                game.board_state[row][col] = dragging_piece
                                game.board_state[drag_start[0]][drag_start[1]] = '--'
                                current_flag = game.chess.get_flag(from_sq = (7-drag_start[0])*8 + drag_start[1], to_sq = (7-row)*8 + col)
                                move_to_push = encode_move(from_sq = (7-drag_start[0])*8 + drag_start[1], to_sq = (7-row)*8 + col, flag=current_flag)
                                game.chess.push(move_to_push)
                                
                                game.moves = [0] * 64
                                game.board_state = game.chess.get_chess_board()
                                threading.Thread(target=(opponent_play), args=(game.chess, game.board_state, game.moves)).start()
                            
                        else:
                            game.board_state[drag_start[0]][drag_start[1]] = dragging_piece
                    else:
                        game.board_state[drag_start[0]][drag_start[1]] = dragging_piece
                    if not promotion:
                        drag_start = (None, None)
                        dragging_piece = None
            elif event.type == pygame.MOUSEMOTION:
                if game.end:
                    for button in end_buttons:
                        button.handle_event(event)

        if promotion is not None:
            row, col = divmod(promotion, 8)
            show_promotion_options(board, CELL_SIZE, col, side)

        
        if dragging:
            mx, my = pygame.mouse.get_pos()
            row = (my // CELL_SIZE)
            col = (mx // CELL_SIZE)
            draw_movable_squares(board, game.board_state,CELL_SIZE, game.moves[(7-drag_start[0])*8 + drag_start[1]])
            draw_start_square(board, CELL_SIZE, drag_start[1], drag_start[0])
            if 0 <= row <= 7 and 0 <= col <= 7:
                if (1 << (7-row)*8 + col) & (game.moves[(7-drag_start[0])*8 + drag_start[1]]):
                    draw_hovered(board, CELL_SIZE, col, row)
            board.blit(piece_images[dragging_piece], (mx - piece_images[dragging_piece].get_width() // 2, my - piece_images[dragging_piece].get_height() // 2))
                
        screen.blit(board, board.get_rect())
                    
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()

