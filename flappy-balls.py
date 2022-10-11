# change username below to something appropriate

from scene import *
from random import randint
from enum import Enum
import random
import math
import time
import sound
import json

USE_WORLD_RANK = False
if USE_WORLD_RANK == True:
    import pwa


class Config:
    username = "petter"
    version = "1.6"
    debug = True
    background_color = '#424254'
    player_color = '#668284'
    enemy_color = '#f07241'
    levels = [ 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, \
               0, 1, 1, 0, 1, 0, 1, 1, 0, 0, \
               1, 0, 0, 1, 0, 0, 1, 1, 0, 1, \
               0, 1, 0, 1, 1, 0, 1, 0, 1, 0 ]
    global USE_WORLD_RANK
    use_world_rank = USE_WORLD_RANK


# game state
class gstate(Enum):
    idle = 0
    running = 1
    dead = 2


# statistics data
class Stats:
    file_name = 'saggy_balls.json'
    score = 0
    hiscore = 0
    prevscore = 0
    crashes = 0
    text = ""

    def __init__(self):
        self.hiscore = self.load('hiscore')

    def save(self, key, value):
        d = { key : value }
        with open(self.file_name, 'w') as out_file:
            json.dump(d, out_file)

    def load(self, value):
        try:
            with open(self.file_name) as in_file:
                d = json.load(in_file)
                return d[value]
        except:
            return 0


# player/ball data:
class Player:
    def __init__(self, screen):
        self.startpos = screen.h / 2
        self.y = self.startpos
        self.x = screen.w / 10
        self.w = screen.w / 8
        self.h = self.w
        self.jump_height = screen.h / 4

        self.y = 0
        self.startpos = 0

        self.animation = []
        for i in range(0, 180):
            self.animation.append(math.sin(math.radians(i)) * self.jump_height)

        # start by falling down (the last frame of the jump)
        self.animation_frame = len(self.animation)
        self.color = 0


# obstacle:
class Enemy:
    def __init__(self, screen):
        self.x = screen.w
        self.y = screen.h
        # initial height
        self.ih = screen.h / 4
        self.h = self.ih
        self.w = screen.w / 25
        self.ontop = False
        self.speed = 3.0
        self.speed_increment = 0.3
        self.color = 0


class Scene(Scene):

    # initalize class veriables:
    def setup(self):
        global screen
        screen = self.size

        self.config = Config()
        self.stats = Stats()

        self.player = Player(screen)
        self.player.color = self.config.player_color

        self.enemy = Enemy(screen)
        self.enemy.color = self.config.enemy_color

        self.gstate = gstate.idle
        self.hiscore_shown = False
        self.frames = 0

    # check ball/obstacle detection: (simple bounding box)
    def detect_collision(self):
        enemy_xcrash = False
        if (self.player.x <= (self.enemy.x + self.enemy.w)) and (self.player.x + self.player.w >= self.enemy.x):
            enemy_xcrash = True

        enemy_ycrash = False
        if self.enemy.ontop:
            if ((self.player.y + self.player.h) >= screen.h - self.enemy.h):
                enemy_ycrash = True
        else:
            if self.player.y <= self.enemy.h:
                enemy_ycrash = True

        roof_crash = False
        if (self.player.y > screen.h - self.player.h):
            roof_crash = True;

        floor_crash = False
        if self.player.y < 0:
            floor_crash = True

        if (enemy_xcrash and enemy_ycrash) or roof_crash or floor_crash:
            self.stats.crashes += 1
            return True
        return False

    # print text to screen:
    def msg(self, txt, ypos = -1, xpos = -1, size = 40):
        if ypos == -1:
            ypos = (screen.h / 10)
        if xpos == -1:
            xpos = screen.w / 2
        text(txt, 'GillSans', size, xpos, ypos)

    # lookup world records in global database:
    def show_world_ranking(self):
        if not self.config.use_world_rank:
            return
        if not self.hiscore_shown:
            remote_record = pwa.get_user_hiscore(self.config.username)
            if remote_record != None:
                if remote_record > self.stats.hiscore:
                    self.stats.save('hiscore', remote_record)
                    self.stats.hiscore = remote_record
                else:
                    pwa.set_user_hiscore(self.config.username, self.stats.hiscore)

                top = pwa.get_hiscore()
                row = 0
                font_height = 60
                if top and len(top):
                    textpos = screen.h - (screen.h / 4)
                    self.msg("version: {}".format(self.config.version), screen.h - 40, screen.w - 80, 20)
                    self.msg("WORLD RANKING:", screen.h - (screen.h / 5))
                    row += 1

                    for elt in top:
                        self.msg("{}: {}".format(elt['username'].capitalize(), elt['score']), \
                                textpos - (font_height * row ))
                        row += 1

    # render the scene:
    def draw(self):
        self.frames += 1
        background(self.config.background_color)

        if self.gstate == gstate.idle:
            if self.config.use_world_rank:
                self.show_world_ranking()
            else:
                row = 0
                font_height = 60
                textpos = screen.h - (screen.h / 4)
                self.msg("HI SCORE: {}".format(self.stats.hiscore),  screen.h - (screen.h / 5))

                if self.stats.prevscore:
                    self.msg("SCORE: {}".format(self.stats.prevscore), textpos - (row * font_height))
                    row += 1

                # use local database:
                if self.stats.hiscore:
                    self.stats.save('hiscore', self.stats.hiscore)

            self.stats.score = 0
            self.player.startpos = screen.h / 2
            self.player.y = self.player.startpos

            self.enemy.x = screen.w
            self.frames = 0
            self.enemy.ontop = bool(self.config.levels[self.stats.score % len(self.config.levels)])
            self.enemy.speed_increment = 1.0

            self.msg("TAP TO PLAY")
            return

        # render player
        fill(self.player.color)
        ellipse(self.player.x, self.player.y, self.player.w, self.player.h)

        # render enemy
        fill(self.enemy.color)
        if self.enemy.ontop:
            rect(self.enemy.x, screen.h - self.enemy.h, self.enemy.w, self.enemy.h)
        else:
            rect(self.enemy.x, 0, self.enemy.w, self.enemy.h)


        # display score in the top right corner:
        self.stats.text = "{}".format(self.stats.score)
        text_size = screen.w / 10
        text(self.stats.text, 'GillSans', text_size, screen.w - 40 - (len(str(self.stats.score)) * (text_size / 4)), screen.h - 60)

        # wait for keypress if dead
        if self.gstate == gstate.dead:
            if self.config.debug == True:
                text("pos: {}x{} sz: {}x{}, enemy: {}x{}, sz: {}x{}, speed: {:.1f}, res: {}x{}".format(\
                    int(self.player.x), int(self.player.y), \
                    int(self.player.w), int(self.player.h),
                    int(self.enemy.x), int(self.enemy.y), \
                    int(self.enemy.w), int(self.enemy.h),
                    self.enemy.speed_increment, \
                    screen.x, screen.y),
                    'GillSans', 10, screen.w / 2, 40)
            else:
                self.gstate == gstate.idle
            return

        # move enemy/wall to the left:
        self.enemy.x -= self.enemy.speed + self.enemy.speed_increment
        self.enemy.h = self.enemy.ih + (self.player.animation[self.frames % len(self.player.animation)] * 1.3)

        # did the self.player crash?
        if self.detect_collision():
            self.gstate = gstate.dead
            return

        # did the self.player pass an obstable:
        if (self.enemy.x + self.enemy.w) < 1:
            self.stats.score += 1
            self.stats.prevscore = self.stats.score
            if self.stats.score > self.stats.hiscore:
                self.stats.save('hiscore', self.stats.score)
                self.stats.hiscore = self.stats.score

            self.enemy.ontop = bool(self.config.levels[self.stats.score % len(self.config.levels)])
            self.enemy.ih = screen.h / 5
            self.enemy.x = screen.w
            # increase difficulty:
            if self.enemy.speed_increment < 3.5:
                self.enemy.speed_increment += 0.4
            else:
                self.enemy.speed_increment += 0.1

        # jump animation
        jump_speed = 3
        if self.player.animation_frame < len(self.player.animation):
            self.player.y = self.player.startpos + self.player.animation[self.player.animation_frame-1]
            self.player.animation_frame += jump_speed
        else:
            # jump is finished, so continue falling (last jump post):
            self.player.y -= self.player.animation[len(self.player.animation)-1] * 3

    def touch_began(self, touch):
        self.hiscore_shown = True
        if self.gstate == gstate.idle:
            self.gstate = gstate.running
        elif self.gstate == gstate.dead:
            self.gstate = gstate.idle
        else:
            sound.play_effect('game:Boing_1')
            self.player.startpos = self.player.y
            self.player.animation_frame = 0

run(Scene())
