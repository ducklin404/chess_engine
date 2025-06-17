import pygame
from pygame import Surface
from engine.chess_logic import *
import threading
from engine.game import Game
import sys
from ui.widgets import *
from ui.assests import load_piece_images
game = Game()

       
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
 
def opponent_play(chess: ChessLogic, board_state: list) -> None:
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
                            threading.Thread(target=(opponent_play), args=(game.chess, game.board_state)).start()

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
                                threading.Thread(target=(opponent_play), args=(game.chess, game.board_state)).start()
                            
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

