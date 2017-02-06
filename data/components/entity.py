from random import uniform, randint, shuffle, choice, random
from collections import OrderedDict

import pygame as pg

from .. import prepare
from ..components.labels import Label, Button, ButtonGroup
 

def compare_color(hsva1, hsva2):
    """
    Returns a float from 0 to 1. A result of 0 is the same color,
    1 is the complete opposite color."""
    h1, s1 = hsva1[:2]
    h2, s2 = hsva2[:2]
    hue_diff = min(360 - abs(h1 - h2), abs(h1 - h2))  / 180.
    sat_diff = abs(s1 - s2) / 100.
    return hue_diff, sat_diff


class SettingsAdjuster(object):
    def __init__(self, world, midtop, setting, initial_value, increment):
        self.world = world
        self.setting = setting
        self.value = initial_value
        self.increment = increment
        self.labels = pg.sprite.Group()
        self.name_label = Label(self.setting, {"midtop": midtop}, self.labels)
        self.value_label = Label("{}".format(self.value),
                                           {"midtop": self.name_label.rect.midbottom},
                                           self.labels, font_size=24)
        self.buttons = ButtonGroup()
        b_size = 32, 32
        space = 32
        left = midtop[0] - (space + b_size[0])
        top = self.name_label.rect.bottom + 5
        style = {"fill_color": "gray20", "text_color": "gray80", "button_size": b_size}
        Button((left, top), self.buttons, text="-",
                   call=self.adjust, args=-self.increment, **style)
        left = midtop[0] + space
        Button((left, top), self.buttons, text="+",
                   call=self.adjust, args=self.increment, **style)

    def adjust(self, increment):
        self.value += increment
        self.value_label.set_text("{}".format(self.value))
        self.world.settings[self.setting] = self.value
        
    def get_event(self, event):
        self.buttons.get_event(event)

    def update(self, mouse_pos):
        self.buttons.update(mouse_pos)

    def draw(self, surface):
        self.labels.draw(surface)
        self.buttons.draw(surface)


class Cell(object):
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))
    def __init__(self, index, cell_size):
        self.index = x, y = index
        self.size = w, h = cell_size
        self.rect = pg.Rect(x * w, y * h, w, h)
        self.occupant = None

    def get_neighbors(self, grid):
        self.neighbors = []
        x, y = self.index
        for nx, ny in self.offsets:
            indx = x + nx, y + ny
            try:
                self.neighbors.append(grid[indx])
            except KeyError:
                pass


class World(object):
    def __init__(self, size, cell_size, settings=None):
        w, h = size
        num_columns = w // cell_size[0]
        num_rows = h // cell_size[1]
        indices = [(x, y) for x in range(num_columns)
                       for y in range(num_rows)]
        self.grid = {index: Cell(index, cell_size) for index in indices}
        for cell in self.grid.values():
            cell.get_neighbors(self.grid)
        if settings is not None:
            self.settings = settings
        else:
            self.settings = OrderedDict([
                    ("Plant Mutate Chance", .3),
                    ("Plant Hue Mutate Range", 36),
                    ("Plant Saturation Mutate Range", 10),
                    ("Critter Mutate Chance", .3),
                    ("Critter Hue Mutate Range", 36),
                    ("Critter Saturation Mutate Range", 10),
                    ("Critter Feeding Difficulty", 2.)])
        self.plants = pg.sprite.Group()
        self.critters = pg.sprite.Group()
        self.all_sprites = pg.sprite.LayeredDirty()
        self.bg = pg.Surface(prepare.SCREEN_SIZE)
        self.bg.fill(pg.Color(prepare.BG_COLOR))
        self.all_sprites.clear(pg.display.get_surface(), self.bg)
        self.sun_hsva = (240, 100, 100, 100)
        self.make_adjusters()
        
    def make_adjusters(self):
        self.adjusters = []
        centerx, top = prepare.SCREEN_RECT.centerx, 50
        for s in self.settings:
            if s in ("Plant Mutate Chance", "Critter Mutate Chance",
                      "Critter Feeding Difficulty"):
                increment = .05
            else:
                increment = 1
                
            adjuster = SettingsAdjuster(self, (centerx, top), s, self.settings[s], increment)
            self.adjusters.append(adjuster)
            top += 80
            
    def update(self):
        sprites = list(self.all_sprites.sprites())
        shuffle(sprites)
        for s in sprites:
            s.update(self)

    def draw(self, surface):
        return self.all_sprites.draw(surface)


class Entity(pg.sprite.DirtySprite):
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    def __init__(self, cell, species_name, hsva, age, energy, *groups):
        super(Entity, self).__init__(*groups)
        self.cell = cell
        self.name = species_name
        self.color = pg.Color(0,0,0)
        self.color.hsva = hsva
        self.age = age
        self.energy = energy
        cell.occupant = self
        self.rect = self.cell.rect
        self.dirty = 1

    def randomize_color(self):
        h, s, v, a = self.color.hsva
        h_mod = randint(*self.hue_mutate_range)
        s_mod = randint(*self.light_mutate_range)
        hue = (h + h_mod) % 360
        if hue == 360:
            hue = 0
        sat = max(min(s + s_mod, 100), 0)
        return (hue, sat, 100, 100)

    def move_to_cell(self, cell, world):
        self.cell.occupant = None
        self.cell = cell
        self.rect = self.cell.rect
        cell.occupant = self
        self.dirty = 1

    def die(self):
        self.cell.occupant = None
        self.kill()


class Plant(Entity):
    """Plants gain energy and reproduce into adjacent empty spaces."""
    def __init__(self, cell, hsva, energy, settings, *groups):
        s = settings
        super(Plant, self).__init__(cell, "Plant", hsva, 0, energy, *groups)
        self.image = pg.Surface(self.rect.size)
        self.image.fill(self.color)
        self.mutate_chance = s["Plant Mutate Chance"]
        self.hue_mutate_range = (-s["Plant Hue Mutate Range"],
                                               s["Plant Hue Mutate Range"])
        self.light_mutate_range = (-s["Plant Saturation Mutate Range"],
                                                s["Plant Saturation Mutate Range"]) 
        self.reproduction_energy = 15
        self.max_energy = 50

    def update(self, world):
        grid = world.grid
        if self.energy <= 0:
            self.die()
            return
        self.energy += 1
        if self.energy > self.max_energy:
            self.energy = self.max_energy
        if self.energy >= self.reproduction_energy:
            if self.cell.neighbors:
                cell = choice(self.cell.neighbors)
                if cell.occupant is None:
                    self.reproduce(cell, world)

    def reproduce(self, cell, world):
        mutate = random() <= self.mutate_chance
        hsva = self.randomize_color() if mutate else self.color.hsva
        offspring = Plant(cell, hsva, 1, world.settings, world.plants, world.all_sprites)
        self.energy = 1


class Critter(Entity):
    def __init__(self, cell, hsva, energy, settings, *groups):
        s = settings
        super(Critter, self).__init__(cell, "Critter", hsva, 0, energy, *groups)
        self.image = pg.Surface(self.rect.size)
        pg.draw.circle(self.image, self.color,
                             (self.rect.w // 2, self.rect.h // 2), self.rect.w // 2)
        self.mutate_chance = s["Critter Mutate Chance"]
        self.hue_mutate_range = (-s["Critter Hue Mutate Range"],
                                               s["Critter Hue Mutate Range"])
        self.light_mutate_range = (-s["Critter Saturation Mutate Range"],
                                                s["Critter Saturation Mutate Range"])
        self.reproduction_energy = 10
        self.max_energy = 20
        self.energy_consumption = 1
        self.death_age = randint(700, 1000)

    def update(self, world):
        grid = world.grid
        self.age += 1
        if self.energy <= 0:
            self.die()
            return
        cell = choice(self.cell.neighbors)
        fertile = self.energy >= self.reproduction_energy
        occupied = cell.occupant is not None
        if occupied:
            if cell.occupant.name == "Plant":
                self.eat(cell, world)
        else:
            if fertile:
                self.reproduce(cell, world)
            else:
                self.move_to_cell(cell, world)
        self.energy -= self.energy_consumption

    def eat(self, cell, world):
        plant = cell.occupant
        hue_diff, sat_diff = compare_color(self.color.hsva, plant.color.hsva)
        color_diff = (hue_diff + sat_diff) / 2.
        chance = random()
        success = chance > (color_diff * world.settings["Critter Feeding Difficulty"])
        if success:
            self.energy += plant.energy
            if self.energy > self.max_energy:
                self.energy = self.max_energy
            plant.kill()
            self.move_to_cell(cell, world)

    def reproduce(self, cell, world):
        mutate = random() >= self.mutate_chance
        hsva = self.randomize_color() if mutate else self.color.hsva
        offspring = Critter(cell, hsva, self.energy / 2., world.settings,
                                   world.critters, world.all_sprites)
        self.energy *= .5
