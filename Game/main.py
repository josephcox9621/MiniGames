import asyncio
import pygame

pygame.init()

WIDTH = 400
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My First Pygbag Game")

clock = pygame.time.Clock()

blue = (50, 100, 255)
red = (255, 70, 70)

colour = blue


async def main():
    global colour

    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    colour = red if colour == blue else blue

            if event.type == pygame.MOUSEBUTTONDOWN:
                colour = red if colour == blue else blue

        screen.fill((30, 30, 30))

        pygame.draw.rect(
            screen,
            colour,
            (150, 250, 100, 100)
        )

        pygame.display.flip()

        clock.tick(60)

        # Required for pygbag
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())