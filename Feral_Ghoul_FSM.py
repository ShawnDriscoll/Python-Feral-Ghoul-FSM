#
#   Feral Ghoul FSM
#
#   The Traveller game in all forms is owned by Far Future Enterprises.
#   Copyright 1977 - 2023 Far Future Enterprises. Traveller is a
#   registered trademark of Far Future Enterprises.
#
#####################################################################

from pygame.surface import Surface

SCREEN_SIZE = (1280, 720)
GHOUL_COUNT = 25
DRUM_COUNT = 5
GLOWING_ONE_COUNT = 10

import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2
from random import randint
import time
import program
from program.pydice import roll

def update_dm(characteristic_mod):
    for i in range(7):
        characteristic_mod[i] = char_dm[characteristic[i]]
        
characteristic = [0, 0, 0, 0, 0, 0, -1]
characteristic_mod = [0, 0, 0, 0, 0, 0, 0]
char_dm = [-3, -2, -2, -1, -1, -1, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
for i in range(6):
    characteristic[i] = roll('2D6')
update_dm(characteristic_mod)

char_dm = [-3, -2, -2, -1, -1, -1, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]

c_Str = 0
c_Dex = 1
c_End = 2
c_Int = 3
c_Edu = 4
c_Soc = 5
c_Psi = 6
        

class State:
    def __init__(self, name):        
        self.name = name
        
    def do_actions(self):
        pass
        
    def check_conditions(self):        
        pass    
    
    def entry_actions(self):        
        pass    
    
    def exit_actions(self):        
        pass
    

class StateMachine:
    def __init__(self):
        self.states = {} # stores the states
        self.active_state = None # the currently active state
        
    def add_state(self, state):
        # add a state to the dictionary
        self.states[state.name] = state
        
    def think(self):
        # perform only if there is an active state
        if self.active_state == None:
            return
        
        # perform the actions of the active state, and check conditions
        self.active_state.do_actions()        
        new_state_name = self.active_state.check_conditions()
        if new_state_name != None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        # change states and perform any exit/entry actions
        if self.active_state != None:
            self.active_state.exit_actions()
        self.active_state = self.states[new_state_name]        
        self.active_state.entry_actions()
        
        
class World:
    def __init__(self):
        self.entities = {} # all entities will be stored here
        self.entity_id = 0 # current id to assign
        
        self.background = Surface(SCREEN_SIZE).convert()
        self.background.fill((200, 200, 200)) #gray-ish background color
        
    def add_entity(self, entity):
        # store entity id and advance the id number
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        #print entity, entity.id
        self.entity_id += 1
        
    def get(self, entity_id):
        # find an entity by its id, none if none
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None
        
    def process(self, time_passed):
        # process all entities in our world
        time_passed_seconds = time_passed / 1000.0
        #print(iter(self.entities.values()))
        #print(self.entities.values())
        #print(list(self.entities.values()))
        for entity in list(self.entities.values()):
            entity.process(time_passed_seconds)
        
    def render(self, surface):
        # render the background and all the entities
        surface.blit(self.background, (0, 0))
        for entity in self.entities.values():
            entity.render(surface)
            
    def spot_close_entity(self, name, location, visual_range = 100):
        # find an entity within range of a location
        location = Vector2(*location)        
        for entity in self.entities.values():            
            if entity.name == name:                
                distance = location.get_distance_to(entity.location)
                if distance < visual_range:
                    return entity        
        return None


class GameEntity:
    def __init__(self, world, name, image):
        self.world = world
        self.name = name
        self.image = image
        self.location = Vector2(0, 0)
        self.destination = Vector2(0, 0)
        self.speed = 0
        
        self.brain = StateMachine()
        
        self.id = 0

    def render(self, surface):
        x, y = self.location
        w, h = self.image.get_size()
        surface.blit(self.image, (x-w/2, y-h/2))   
        
    def process(self, time_passed):
        self.brain.think()
        if self.speed > 0 and self.location != self.destination:
            vec_to_destination = self.destination - self.location        
            distance_to_destination = vec_to_destination.get_length()
            heading = vec_to_destination.get_normalized()
            travel_distance = min(distance_to_destination, time_passed * self.speed)
            self.location += travel_distance * heading
        

class Drum(GameEntity):
    def __init__(self, world, image):
        GameEntity.__init__(self, world, "drum", image)
        
        
class Ghoul(GameEntity):
    def __init__(self, world, image):
        # initialize the base constructor for this class
        GameEntity.__init__(self, world, "ghoul", image)
        self.dead_image = pygame.transform.rotate(image, 90)
        
        self.ghoul_characteristic = [10, 10, 10, 2, 2, 2, -1]
        self.ghoul_mod = [0, 0, 0, 0, 0, 0, 0]
        
        def update_ghoul_dm(ghoul_mod):
            for i in range(7):
                ghoul_mod[i] = char_dm[self.ghoul_characteristic[i]]
                
        self.ghoul_characteristic[c_Str] = roll('1d6') + 6
        self.ghoul_characteristic[c_Dex] = roll('1d6') + 6
        self.ghoul_characteristic[c_End] = roll('1d6') + 6
        #print self.ghoul_characteristic
        update_ghoul_dm(self.ghoul_mod)
        #print self.ghoul_mod
        #print
        self.initial_health = sum(self.ghoul_characteristic[:3])
        self.current_health = randint(1, self.initial_health - 5)
        
        # create instances for each state
        exploring_state = GhoulStateExploring(self)
        seeking_state = GhoulStateSeeking(self)
        healing_state = GhoulStateHealing(self)
#         delivering_state = GhoulStateDelivering(self)
#         hunting_state = GhoulStateHunting(self)
        
        # add the states to the state machine (self.brain)
        self.brain.add_state(exploring_state)
        self.brain.add_state(seeking_state)
        self.brain.add_state(healing_state)
        #self.brain.add_state(delivering_state)
        #self.brain.add_state(hunting_state)

    def wounded(self):
        self.current_health += -1
        if self.current_health <= 0:
            self.speed = 0
            self.image = self.dead_image
        self.speed = 140
        
    def render(self, surface):
        GameEntity.render(self, surface)      
        x, y = self.location
        w, h = self.image.get_size()
        #pygame.draw.circle(surface, (0, 0, 255), (int(x), int(y)), 24, 1)
        bar_x = x - 12
        bar_y = y - h/2 - 6
        red_bar_length = 25
        green_bar_length = 25 * self.current_health / self.initial_health
        #print green_bar, 'pixels'
        surface.fill((255, 0, 0), (bar_x, bar_y, red_bar_length, 4))
        surface.fill((0, 255, 0), (bar_x, bar_y, green_bar_length, 4))
        

class GhoulStateExploring(State):
    def __init__(self, ghoul):
        # use the base class to init the state 
        State.__init__(self, "exploring")
        # set the ghoul that this state will manipulate
        self.ghoul = ghoul
        
    def random_destination(self):
        # pick a random spot on the screen
        w, h = SCREEN_SIZE
        self.ghoul.destination = Vector2(randint(24, w - 24), randint(24, h - 24))
        
    def do_actions(self):
        # 1 in 20 chance of changing directions
        if roll('d100') == 1:
            self.random_destination()

    def check_conditions(self):
        # if drum is spotted, and the ghoul is injured, set ghoul state to seeking
        drum = self.ghoul.world.spot_close_entity("drum", self.ghoul.location)        
        if drum != None:
            if self.ghoul.current_health < self.ghoul.initial_health * .5:
                self.ghoul.drum_id = drum.id
                return "seeking"
        return None
                
    def entry_actions(self):
        # give ghoul random speed and heading
        self.ghoul.speed = 20 + roll('FLUX') * 3
        self.random_destination()


class GhoulStateSeeking(State):
    def __init__(self, ghoul):
        State.__init__(self, "seeking")
        self.ghoul = ghoul
        #self.drum_id = None
    
    def check_conditions(self):
        # if drum is gone, go to explore state
        drum = self.ghoul.world.get(self.ghoul.drum_id)
        if drum == None:
            return "exploring"
        if self.ghoul.location.get_distance_to(drum.location) < 5:
            if self.ghoul.current_health < self.ghoul.initial_health * .5:
                return "healing"
            else:
                return 'exploring'
        return None
    
    def entry_actions(self):
        # set the ghoul's destination to the drum's location
        drum = self.ghoul.world.get(self.ghoul.drum_id)
        if drum != None:                        
            self.ghoul.destination = drum.location
            self.ghoul.speed = 160 + randint(-20, 20)
            

class GhoulStateHealing(State):
    def __init__(self, ghoul):
        State.__init__(self, 'healing')
        self.ghoul = ghoul

    def check_conditions(self):
        if roll('3d6') == 18:
            self.ghoul.current_health += 1
        # if healed, continue exploring
        if self.ghoul.current_health < self.ghoul.initial_health * .5:
            return None
        return "exploring"


class Glowing_One(GameEntity):
    def __init__(self, world, image):
        # initialize the base constructor for this class
        GameEntity.__init__(self, world, "glowing_one", image)
        self.dead_image = pygame.transform.rotate(image, 90)
        
        self.glowing_one_characteristic = [10, 10, 10, 2, 2, 2, -1]
        self.glowing_one_mod = [0, 0, 0, 0, 0, 0, 0]
        
        def update_glowing_one_dm(glowing_one_mod):
            for i in range(7):
                glowing_one_mod[i] = char_dm[self.glowing_one_characteristic[i]]
                
        self.glowing_one_characteristic[c_Str] = roll('2d6') + 6
        self.glowing_one_characteristic[c_Dex] = roll('2d6') + 6
        self.glowing_one_characteristic[c_End] = roll('2d6') + 6
        #print self.glowing_one_characteristic[0:3]
        update_glowing_one_dm(self.glowing_one_mod)
        #print self.glowing_one_mod[0:3]
        #print
        self.initial_health = sum(self.glowing_one_characteristic[:3])
        self.current_health = randint(5, self.initial_health)
        
        # create instances for each state
        exploring_state = Glowing_One_StateExploring(self)
        seeking_state = Glowing_One_StateSeeking(self)
        healing_state = Glowing_One_StateHealing(self)
#         delivering_state = GhoulStateDelivering(self)
#         hunting_state = GhoulStateHunting(self)
        
        # add the states to the state machine (self.brain)
        self.brain.add_state(exploring_state)
        self.brain.add_state(seeking_state)
        self.brain.add_state(healing_state)
        #self.brain.add_state(delivering_state)
        #self.brain.add_state(hunting_state)

    def wounded(self):
        self.current_health += -1
        if self.current_health <= 0:
            self.speed = 0
            self.image = self.dead_image
        self.speed = 140
        
    def render(self, surface):
        GameEntity.render(self, surface)      
        x, y = self.location
        w, h = self.image.get_size()
        #pygame.draw.circle(surface, (0, 0, 255), (int(x), int(y)), 24, 1)
        bar_x = x - 12
        bar_y = y - h/2 - 6
        red_bar_length = 25
        green_bar_length = 25 * self.current_health / self.initial_health
        #print green_bar, 'pixels'
        surface.fill((255, 0, 0), (bar_x, bar_y, red_bar_length, 4))
        surface.fill((0, 255, 0), (bar_x, bar_y, green_bar_length, 4))
        

class Glowing_One_StateExploring(State):
    def __init__(self, glowing_one):
        # use the base class to init the state 
        State.__init__(self, "exploring")
        # set the glowing one that this state will manipulate
        self.glowing_one = glowing_one
        
    def random_destination(self):
        # pick a random spot on the screen
        w, h = SCREEN_SIZE
        self.glowing_one.destination = Vector2(randint(24, w - 24), randint(24, h - 24))
        
    def do_actions(self):
        # 1 in 20 chance of changing directions
        if roll('d100') == 1:
            self.random_destination()

    def check_conditions(self):
        # if drum is spotted, and the glowing one is injured, set glowing one state to seeking
        drum = self.glowing_one.world.spot_close_entity("drum", self.glowing_one.location)        
        if drum != None:
            if self.glowing_one.current_health < self.glowing_one.initial_health:
                self.glowing_one.drum_id = drum.id
                return "seeking"
        # check if wounded ghoul is near a glowing one, and heal it if possible
        ghoul = self.glowing_one.world.spot_close_entity('ghoul', self.glowing_one.location, 58)
        if ghoul != None:
            if self.glowing_one.current_health == self.glowing_one.initial_health:
                if ghoul.current_health < ghoul.initial_health:
                    ghoul.current_health += 1
                    #print ghoul.initial_health, ghoul.current_health
        return None
                
    def entry_actions(self):
        # give glowing one random speed and heading
        self.glowing_one.speed = 20 + roll('FLUX') * 3
        self.random_destination()


class Glowing_One_StateSeeking(State):
    def __init__(self, glowing_one):
        State.__init__(self, "seeking")
        self.glowing_one = glowing_one
        #self.drum_id = None
    
    def check_conditions(self):
        # if drum is gone, go to explore state
        drum = self.glowing_one.world.get(self.glowing_one.drum_id)
        if drum == None:
            return "exploring"
        if self.glowing_one.location.get_distance_to(drum.location) < 5:
            if self.glowing_one.current_health < self.glowing_one.initial_health:
                return "healing"
            else:
                return 'exploring'
        return None
    
    def entry_actions(self):
        # set the glowing one's destination to the drum's location
        drum = self.glowing_one.world.get(self.glowing_one.drum_id)
        if drum != None:                        
            self.glowing_one.destination = drum.location
            self.glowing_one.speed = 160 + randint(-20, 20)
            

class Glowing_One_StateHealing(State):
    def __init__(self, glowing_one):
        State.__init__(self, 'healing')
        self.glowing_one = glowing_one

    def check_conditions(self):
        self.glowing_one.current_health += 1
        # if healed, continue exploring
        if self.glowing_one.current_health < self.glowing_one.initial_health:
            return None
        return "exploring"
        
        
def main():
    pygame.init()
    
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    window_title = program.app
    pygame.display.set_caption(window_title)
    window_icon = pygame.image.load('images/fg_fsm_icon_32x32.jpg')
    pygame.display.set_icon(window_icon)
    
    world = World()
    
    w, h = SCREEN_SIZE 
    
    clock = pygame.time.Clock()
    
    ghoul_image = pygame.image.load("images/ghoul.png").convert_alpha()
    drum_image = pygame.image.load("images/drum.png").convert_alpha()
    glowing_one_image = pygame.image.load("images/glowing_one.png").convert_alpha()
    
    #add the drum entities
    for i in range(DRUM_COUNT):
        drum = Drum(world, drum_image)
        drum.location = Vector2(randint(24, w - 24), randint(24, h - 24))
        world.add_entity(drum)

    # add all our glowing one entities
    for i in range(GLOWING_ONE_COUNT):
        glowing_one = Glowing_One(world, glowing_one_image)
        glowing_one.location = Vector2(randint(24, w - 24), randint(24, h - 24))
        glowing_one.brain.set_state("exploring")
        world.add_entity(glowing_one)

    # add all our ghoul entities
    for i in range(GHOUL_COUNT):
        ghoul = Ghoul(world, ghoul_image)
        ghoul.location = Vector2(randint(24, w - 24), randint(24, h - 24))
        ghoul.brain.set_state("exploring")
        world.add_entity(ghoul)
        
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            
        time_passed = clock.tick(30)
        
        world.process(time_passed)
        world.render(screen)
        
        pygame.display.update()


if __name__ == '__main__':
    trange = time.localtime()
    if trange[0] > 2023 or trange[1] > 4:
        print()
        print(program.app, 'EXPIRED.')
        print()
        print(program.author)
        print(program.author_email)
        print(program.url)
        print()
        s = input('Press ENTER: ')
        print('OK')
    else:
        print()
        print('Thank you for giving', program.app, 'a try.')
        vernum, release = roll('info')
        print()
        print('This program uses:')
        print(release)
        print('Pygame 2.1.3.dev8')
        print('SDL 2.0.22')
        print()
        if vernum != '3.12':
            print('WARNING! Different version of roll() installed:', vernum)
        if pygame.version.vernum != (2, 1, 3):
            print('WARNING! Different version of Pygame installed:', pygame.version.ver)
        if pygame.get_sdl_version() != (2, 0, 22):
            print('WARNING! Different version of SDL installed:', pygame.get_sdl_version())
        print('----------------------------')
        print(program.author)
        print(program.author_email)
        print(program.url)
        print()
        
        main()

