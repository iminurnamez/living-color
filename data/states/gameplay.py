from random import randint

import pygame as pg

from .. import tools, prepare
from ..components.entity import World, Plant, Critter


class Gameplay(tools._State):
    def __init__(self):
        super(Gameplay, self).__init__()
        self.world = World(prepare.SCREEN_SIZE, prepare.CELL_SIZE)
        self.tick_length = 20

    def startup(self, persistent):
        self.persist = persistent
        self.timer = 0
        self.paused = True
        self.manual = True
        self.drawing = True

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit = True
            elif event.key == pg.K_SPACE:
                self.paused = not self.paused
            elif event.key == pg.K_a:
                self.manual = True
            elif event.key == pg.K_d:
                self.drawing = not self.drawing
        elif event.type == pg.MOUSEBUTTONUP:
            for cell in self.world.grid.values():
                if cell.rect.collidepoint(event.pos):
                    if event.button == 1:
                        h = randint(0, 360) % 360
                        s = randint(0, 100)
                        Plant(cell, (h, s, 100, 100), 1, self.world.settings,
                                self.world.plants, self.world.all_sprites)
                    elif event.button == 3:
                        h = randint(0, 360) % 360
                        s = randint(0, 100)
                        c = Critter(cell, (h, s, 100, 100), 5, self.world.settings,
                                        self.world.critters, self.world.all_sprites)
                        self.placed_critter = c
                    break

    def update(self, dt):
        tick = False
        if not self.paused:
            self.timer += dt
            if self.timer >= self.tick_length:
                self.timer -= self.tick_length
                tick = True
        if tick or self.manual:
            self.world.update()
        self.manual = False

    def draw(self, surface):
        if self.drawing:
            dirty = self.world.draw(surface)
        else:
            dirty = []
        return dirty
