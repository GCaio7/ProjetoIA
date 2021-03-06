import pygame
import sys
import os
import copy
from settings import *
from player_class import *
from enemy_class import *

pygame.init()
pygame.display.set_caption('Projeto I IA - A*')
mixer = pygame.mixer
vec = pygame.math.Vector2


class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'start'
        self.cell_width = MAZE_WIDTH//COLS
        self.cell_height = MAZE_HEIGHT//ROWS
        self.walls = []
        self.coins = []
        self.enemies = []
        self.e_pos = []
        self.p_pos = None
        self.music_state = 'playing'
        self.load()

        self.player = Player(self, vec(self.p_pos))
        self.make_enemies()

    def run(self):
        while self.running:
            if self.state == 'start':
                self.start_events()
                self.start_update()
                self.start_draw()
            elif self.state == 'playing':
                self.playing_events()
                self.playing_update()
                self.playing_draw()
            elif self.state == 'game over':
                self.game_over_events()
                self.game_over_update()
                self.game_over_draw()
            else:
                self.running = False

            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    # ################## # FUNCOES AUXILIARES # ################## #

    def draw_text(self, words, screen, pos, size, color, font_name, centered=False):
        font = pygame.font.SysFont(font_name, size)
        text = font.render(words, False, color)
        text_size = text.get_size()
        if centered:
            pos[0] = pos[0] - text_size[0] // 2
            pos[1] = pos[1] - text_size[1] // 2
        screen.blit(text, pos)

    def load(self):
        self.background = pygame.image.load('maze.png')
        self.background = pygame.transform.scale(self.background, (MAZE_WIDTH, MAZE_HEIGHT))

        mixer.music.load('bg_sound.ogg')
        mixer.music.play(-1)

        # Abrindo arquivo walls
        # Criando lista de muros com as coordenadas dos muros
        with open("walls.txt", 'r') as file:
            for yidx, line in enumerate(file):
                for xidx, char in enumerate(line):
                    if char == "1":
                        self.walls.append(vec(xidx, yidx))
                    elif char == "C":
                        self.coins.append(vec(xidx, yidx))
                    elif char == "P":
                        self.p_pos = [xidx, yidx]
                    elif char in ["2", "3", "4", "5"]:
                        self.e_pos.append([xidx, yidx])
                    elif char == "B":
                        pygame.draw.rect(self.background, BLACK, (xidx*self.cell_width, yidx*self.cell_height,
                                                                  self.cell_width, self.cell_height))

    def make_enemies(self):
        for idx, pos in enumerate(self.e_pos):
             self.enemies.append(Enemy(self, vec(pos), 0))

    def draw_grid(self):
        for x in range(WIDTH // self.cell_width):
            pygame.draw.line(self.background, GREY, (x * self.cell_width, 0),
                             (x * self.cell_width, HEIGHT))
        for x in range(HEIGHT // self.cell_height):
            pygame.draw.line(self.background, GREY, (0, x * self.cell_height),
                             (WIDTH, x * self.cell_height))

        # for coin in self.coins:
        #    pygame.draw.rect(self.background, (167, 179, 34), (coin.x*self.cell_width,
        #                                                         coin.y*self.cell_height, self.cell_width, self.cell_height))

    def draw_coins(self):
        for coin in self.coins:
            pygame.draw.circle(self.screen, (255, 255, 77),
                               (int(coin.x * self.cell_width) + self.cell_width // 2 + TOP_BOTTOM_BUFFER // 2
                                , int(coin.y * self.cell_height) + self.cell_height // 2 + TOP_BOTTOM_BUFFER // 2)
                               , 5)

    def reset(self):
        self.player.lives = 3
        self.player.current_score = 0
        self.player.grid_pos = vec(self.player.starting_pos)
        self.player.pix_pos = self.player.get_pix_pos()
        self.player.direction *= 0
        for enemy in self.enemies:
            enemy.grid_pos = vec(enemy.starting_pos)
            enemy.pix_pos =  enemy.get_pix_pos()
            enemy.direction *= 0
        self.coins = [] 
        with open("walls.txt", 'r') as file:
            for yidx, line in enumerate(file):
                for xidx, char in enumerate(line):
                    if char == 'C':
                        self.coins.append(vec(xidx, yidx))

        self.state = "playing"

    #####  # FUNCOES DE INICIO # #####

    def start_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = 'playing'

            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                if self.music_state == 'playing':
                    mixer.music.pause()
                    self.music_state = 'paused'
                elif self.music_state == 'paused':
                    mixer.music.unpause()
                    self.music_state = 'playing'

    def start_update(self):
        pass

    def start_draw(self):
        self.screen.fill(BLACK)
        self.draw_text('APERTE A BARRA DE ESPACO', self.screen, [WIDTH // 2, HEIGHT // 2 - 50], START_TEXT_SIZE,
                       (170, 132, 58), START_FONT, centered=True)
        self.draw_text('APENAS 1 JOGADOR', self.screen, [WIDTH // 2, HEIGHT // 2 + 50], START_TEXT_SIZE, (44, 167, 198),
                       START_FONT, centered=True)
        self.draw_text('PONTUACAO', self.screen, [4, 0], 14, (255, 255, 255), START_FONT)
        self.draw_text('APERTE S PARA DESATIVAR/ATIVAR A MÚSICA', self.screen, [WIDTH -220, HEIGHT -20], START_TEXT_SIZE,
                       (255, 255, 255), START_FONT, centered=True)
        pygame.display.update()

    # ################## # FUNCOES DE JOGAR # ################## #

    def playing_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                angle = 0
                # IR P/ ESQUERDA
                if event.key == pygame.K_LEFT:
                    if self.player.last_direction == 'right':
                        angle = -180
                    if self.player.last_direction == 'down':
                        angle = -90
                    if self.player.last_direction == 'up':
                        angle = 90

                    self.player.move(vec(-1, 0), angle)

                    self.player.last_direction = 'left'

                # IR P/ DIREITA
                if event.key == pygame.K_RIGHT:
                    if self.player.last_direction == 'left':
                        angle = 180
                    if self.player.last_direction == 'down':
                        angle = 90
                    if self.player.last_direction == 'up':
                        angle = -90

                    self.player.move(vec(1, 0), angle)

                    self.player.last_direction = 'right'

                # IR P/ CIMA
                if event.key == pygame.K_UP:
                    if self.player.last_direction == 'left':
                        angle = -90
                    if self.player.last_direction == 'right':
                        angle = 90
                    if self.player.last_direction == 'down':
                        angle = 180

                    self.player.move(vec(0, -1), angle)

                    self.player.last_direction = 'up'

                # IR P/ BAIXO
                if event.key == pygame.K_DOWN:
                    if self.player.last_direction == 'left':
                        angle = 90
                    if self.player.last_direction == 'right':
                        angle = -90
                    if self.player.last_direction == 'up':
                        angle = 180

                    self.player.move(vec(0, 1), angle)

                    self.player.last_direction = 'down'

    def playing_update(self):
        self.player.update()
        for enemy in self.enemies:
            enemy.update()

        for enemy in self.enemies:
            if enemy.grid_pos == self.player.grid_pos:
                self.remove_live()

    def playing_draw(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.background, (TOP_BOTTOM_BUFFER // 2, TOP_BOTTOM_BUFFER // 2))
        self.draw_coins()
        # self.draw_grid()
        self.draw_text('PONTUACAO ATUAL: {}'.format(self.player.current_score),
                       self.screen, [60, 0], 18, WHITE, START_FONT)
        self.draw_text('PONTUACAO MAXIMA: 0',
                       self.screen, [WIDTH // 2 + 60, 0], 18, WHITE, START_FONT)
        self.player.draw(self)
        for enemy in self.enemies:
            enemy.draw(self)
        pygame.display.update()

    def remove_live(self):
        self.player.lives -= 1

        if self.player.lives == 0:
            self.state = "game over"
        else:
            self.player.grid_pos = vec(self.player.starting_pos)
            self.player.pix_pos = self.player.get_pix_pos()
            self.player.direction*= 0
            for enemy in self.enemies:
                enemy.grid_pos = vec(enemy.starting_pos)
                enemy.pix_pos = enemy.get_pix_pos()
                enemy.direction *= 0

    #####  # FUNCOES DE FIM DE JOGO # #####

    def game_over_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.reset()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def game_over_update(self):
        pass

    def game_over_draw(self):
        self.screen.fill(BLACK)
        quit_text = "Aperte esc para sair"
        again_text = "Aperte espaço para recomeçar"
        self.draw_text("Você está preso", self.screen, [WIDTH//2, 100], 52, RED, "arial", centered=True)
        self.draw_text(again_text, self.screen, [WIDTH//2, HEIGHT//2], 36, (190,190,190), "arial", centered=True)
        self.draw_text(quit_text, self.screen, [WIDTH//2, HEIGHT-50], 36, RED, "arial", centered=True)
        pygame.display.update()