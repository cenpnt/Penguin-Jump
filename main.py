import pygame
import random
from lowPlatform import *
from settings import *
from platforms import *
from enemies import *
from Clouds import *
vec = pygame.math.Vector2
from os import path
from mpu6050 import mpu6050
import time

class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.image = pygame.image.load('pikachu.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.pos = vec(display_width - 100, display_height)
        self.rect.topleft = [self.pos.x, self.pos.y]
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)

    def update(self):
        self.acc = vec(0, gravity)  # Gravity applied to player

        # Handle gyro movement
        self.acc.x += self.game.get_gyro_movement()  # Get gyro input from the game class
        self.acc.x += self.vel.x * player_Fric
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        # Horizontal crossing of screen (wrapping)
        if self.pos.x > display_width:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = display_width

        self.rect.midbottom = [self.pos.x, self.pos.y]  # Update sprite position

        # Handle collisions with platforms
        if self.vel.y > 0:
            hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
            if hits:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.bottom:
                        lowest = hit

                if self.pos.x < lowest.rect.right + 30 and self.pos.x > lowest.rect.left - 30:
                    if self.pos.y < lowest.rect.centery:
                        self.pos.y = lowest.rect.top
                        self.vel.y = 0

    def jump(self):
        # Check if the player sprite is on a platform
        if self.vel.y > 0:
            self.rect.y += 1
            hits = pygame.sprite.spritecollide(self, self.game.platforms, False)
            self.rect.y -= 1
            if hits:
                self.game.jump_sound.play()
                self.vel.y = -10


class Game:
    def __init__(self):
        pygame.init()
        self.gameDisplay = pygame.display.set_mode((display_width, display_height))
        self.gameDisplay.fill(white)
        pygame.display.set_caption("Penguin Jump!")
        self.clock = pygame.time.Clock()
        self.background = pygame.image.load('blue_back.jpg').convert()
        self.font = pygame.font.SysFont(None, 25)
        self.gameExit = False

        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()

        # Create player object and add it to the all_sprites group
        self.player = Player(self)
        self.all_sprites.add(self.player)

        p1 = lowPlatform(0, display_height - 40, display_width, 40)
        platform_obj = Platform(self)
        self.platform_images = platform_obj.getImages()
        p2 = Platform(self)
        p2.getPlatform(display_width / 2 - 50, display_height - 150, self.platform_images)
        p3 = Platform(self)
        p3.getPlatform(display_width / 2 - 100, display_height - 300, self.platform_images)
        p4 = Platform(self)
        p4.getPlatform(display_width / 2, display_height - 450, self.platform_images)
        p5 = Platform(self)
        p5.getPlatform(0, display_height - 600, self.platform_images)
        self.platforms.add(p1, p2, p3, p4, p5)

        self.score = 0
        self.font_name = pygame.font.match_font(Font_Name)
        self.load_data()
        self.enemies_timer = 0
        self.mpu = mpu6050(0x68)
        self.gyro_sensitivity = 0.1

        for i in range(8):
            c = Cloud(self)
            c.rect.y += 600

    def load_data(self):
        # Loading high score from file
        self.dir = path.dirname(__file__)
        with open(path.join(self.dir, hs_file), 'r+') as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0

        # Load cloud images
        cloud_dir = path.join(self.dir, 'clouds_img')
        self.cloud_images = []
        for i in range(1, 4):
            self.cloud_images.append(pygame.image.load(path.join(cloud_dir, 'cloud{}.png'.format(i))).convert())

        # Load sounds
        self.sound_dir = path.join(self.dir, 'sound')
        self.jump_sound = pygame.mixer.Sound(path.join(self.sound_dir, 'jump.ogg'))
        self.jump_sound.set_volume(0.1)
        self.pow_sound = pygame.mixer.Sound(path.join(self.sound_dir, 'pow.wav'))

    def get_gyro_movement(self):
        try:
            gyro_data = self.mpu.get_gyro_data()
            tilt = gyro_data['y']
            return -tilt * self.gyro_sensitivity
        except:
            return 0

    def updateScreen(self):
        now_time = pygame.time.get_ticks()
        if now_time - self.enemies_timer > 5000 + random.choice([-1000, -500, 0, 500, 1000]):
            self.enemies_timer = now_time
            Enemies(self)

        # Check if player collides with enemies
        enemies_hits = pygame.sprite.spritecollide(self.player, self.enemies, False, pygame.sprite.collide_mask)
        if enemies_hits:
            self.gameOver = True

        # Update and draw all sprites
        self.gameDisplay.fill(black)
        self.all_sprites.update()
        self.clouds.update()
        self.platforms.update()
        self.powerups.update()
        self.enemies.update()

        # Drawing all elements
        self.gameDisplay.blit(self.background, (0, 0))
        self.clouds.draw(self.gameDisplay)
        self.platforms.draw(self.gameDisplay)
        self.powerups.draw(self.gameDisplay)
        self.enemies.draw(self.gameDisplay)
        self.all_sprites.draw(self.gameDisplay)

        self.messageToScreen("SCORE: " + str(self.score), 25, white, display_width / 2, 15)
        pygame.display.update()

    def run(self):
        self.score = 0
        self.gameOver = False
        while not self.gameExit:
            self.checkEvent()
            self.updateScreen()
            self.clock.tick(fps)
            if self.gameOver:
                self.gameOverScreen()
        pygame.quit()
        quit()

    def checkEvent(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.gameExit = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.jump()

    def messageToScreen(self, msg, size, color, x, y):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(msg, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.gameDisplay.blit(text_surface, text_rect)

g = Game()
g.run()
