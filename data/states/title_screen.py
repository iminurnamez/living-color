import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Button, ButtonGroup
from ..components.entity import World


class TitleScreen(tools._State):
    def __init__(self):
        super(TitleScreen, self).__init__()
        self.world = World(prepare.SCREEN_SIZE, prepare.CELL_SIZE)
        self.title = Label("Living Color",
                               {"midtop": prepare.SCREEN_RECT.midtop},
                               font_size=32)
        b_size = (120, 40)
        topleft = (prepare.SCREEN_RECT.centerx - (b_size[0] // 2),
                      prepare.SCREEN_RECT.bottom - (b_size[1] + 10))
        self.buttons = ButtonGroup()
        self.start_button = Button(topleft, self.buttons, text="START SIM",
                                              font_size=24, button_size=b_size,
                                              text_color="gray80", fill_color="gray20",
                                              call=self.start_sim)

    def start_sim(self, *args):
        self.done = True
        self.next = "GAMEPLAY"
        settings = self.world.settings
        world = World(prepare.SCREEN_SIZE,
                             prepare.CELL_SIZE, settings)
        self.persist["world"] = world

    def startup(self, persistent):
        self.persist = persistent
        self.world = World(prepare.SCREEN_SIZE,
                                   prepare.CELL_SIZE)

    def get_event(self,event):
        self.buttons.get_event(event)
        for a in self.world.adjusters:
            a.get_event(event)
        if event.type == pg.QUIT:
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit = True

    def update(self, dt):
        mouse_pos = pg.mouse.get_pos()
        self.buttons.update(mouse_pos)
        for a in self.world.adjusters:
            a.update(mouse_pos)

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        self.title.draw(surface)
        self.buttons.draw(surface)
        for a in self.world.adjusters:
            a.draw(surface)
        return prepare.SCREEN_RECT