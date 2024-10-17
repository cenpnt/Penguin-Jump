import pygame
import random
from settings import *
from pygame.locals import*
import smbus3
import time

# MPU6050 I2C address
MPU6050_ADDR = 0x68

# Initialize I2C bus
bus = smbus3.SMBus(1)

# Initialize MPU6050
def init_MPU6050():
    bus.write_byte_data(MPU6050_ADDR, 0x6B, 0)  # Wake the sensor

def read_gyro_x():
    # Read high and low byte of gyro x-axis
    high = bus.read_byte_data(MPU6050_ADDR, 0x43)
    low = bus.read_byte_data(MPU6050_ADDR, 0x44)
    value = (high << 8) | low

    # Convert to signed value
    if value > 32768:
        value -= 65536
    return value / 131  # Sensitivity scale factor

init_MPU6050()

pygame.init()
font = pygame.font.SysFont(None,25)

def messageToScreen(msg,color,x,y):
    screen_text=font.render(msg,True,color)
    gameDisplay.blit(screen_text,[x,y])
    pygame.display.update()


clock=pygame.time.Clock()

gameDisplay=pygame.display.set_mode((display_width,display_height))
gameDisplay.fill(white)
pygame.display.set_caption("Penguin Jump!")
img_pikachu=pygame.image.load('pikachu.png').convert_alpha()
background=pygame.image.load('background.jpg').convert()


def gameLoop():
    gameExit = False
    lead_x = display_width / 2
    lead_y = display_height - 100
    lead_y_change = 0
    g = 1  # Gravity
    randObjectX = random.randrange(0, display_width)
    randObjectY = random.randrange(0, display_height)
    gameOver = False

    while not gameExit:
        while gameOver:
            gameDisplay.fill(white)
            messageToScreen(
                "Game Over! Press A to Play Again. Press Q to quit!",
                red, display_width / 2 - 220, display_height / 2)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        gameLoop()
                    if event.key == pygame.K_q:
                        gameExit = True
                        gameOver = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gameExit = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    lead_y_change -= 10
                if event.key == pygame.K_DOWN:
                    lead_y_change += 10

        # Adjust x-coordinate based on gyro data
        gyro_x = read_gyro_x()
        lead_x += gyro_x * 0.05  # Adjust multiplier to control speed

        lead_y += lead_y_change

        # Wrap-around effect
        if lead_x > display_width:
            lead_x = 0
        elif lead_x < 0:
            lead_x = display_width

        if lead_y > display_height:
            gameOver = True
        elif lead_y < 0:
            lead_y = display_height

        gameDisplay.fill(black)
        gameDisplay.blit(background, (0, 0))
        pygame.draw.rect(gameDisplay, red, [randObjectX, randObjectY, 100, 10])
        gameDisplay.blit(img_pikachu, (lead_x, lead_y))

        messageToScreen(
            "Welcome to DOODLE JUMP", red,
            display_width / 2 - 100, display_height - 50)

        pygame.display.update()
        clock.tick(fps)

    pygame.quit()
    quit()

gameLoop()