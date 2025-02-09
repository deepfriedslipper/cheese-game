from math import sqrt#, cos, sin, pi
from pyglet import resource, sprite, clock, graphics
from random import randint, random, shuffle
from json import load

from logger import log


class NPC_Manager:
    def __init__(self, screen_size, player, tilemap) -> None:
        self.screen_width, self.screen_height = screen_size
        self.player = player
        self.tilemap = tilemap

        self.npc_list = []
        self.batch = graphics.Batch()

        self.initialise_children()
        self.initialise_cows()
    
    def initialise_children(self) -> None:
        x_positions = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        y_positions = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        x_velocities = [-20, -25, -15, -10, -5, 5, 10, 15, 20, 25]
        y_velocities = [-25, -20, -15, -10, -5, 5, 10, 15, 20, 25]

        shuffle(x_positions)
        shuffle(y_positions)
        shuffle(x_velocities)
        shuffle(y_velocities)

        self.child_flock = []

        for i in range(10):
            self.child_flock.append(Child(x_positions[i], y_positions[i], 
                                    x_velocities[i], y_velocities[i],
                                    self.batch, (self.screen_width, self.screen_height)))
        
        for child in self.child_flock:
            self.npc_list.append(child)
    
    def initialise_cows(self) -> None:
        self.cow = Cow(3.0, 3.0, 1, (self.screen_width, self.screen_height), self.batch, self.tilemap)

        self.npc_list.append(self.cow)
    
    def set_screen_size(self, zoom) -> None:
        self.screen_width /= zoom
        self.screen_height /= zoom

        for npc in self.npc_list:
            npc.set_screen_size(zoom)
    
    def draw(self, player_pos) -> None:
        self.batch.draw()

        for npc in self.npc_list:
            npc.update(self.child_flock, player_pos)

    def set_tilemap(self, name) -> None:
        #with open(f"assets/npc_info/{name}.json") as file:
        #    data = load(file)
        self.cow = None
        for npc in self.npc_list:
            npc.batch = None
            del npc
        self.npc_list = []
        self.batch = graphics.Batch()


class Cow:
    def __init__(self, x, y, speed: float, screen_size, batch, tilemap) -> None:
        self.position = [x, y]
        self.speed = speed
        self.screen_width, self.screen_height = screen_size
        self.batch = batch
        self.tilemap = tilemap

        self.image = resource.image(f'assets/sprites/creature/cow{randint(1,2)}.png', atlas=True)

        self.sprite = sprite.Sprite(self.image, x=self.position[0], y=self.position[1], batch=self.batch)

        clock.schedule_once(self.random_movement, randint(1, 5))
    
    def random_movement(self, _) -> None:
        #self.set_direction(random() * 2 * pi)

        clock.schedule_interval_for_duration(self.move, 1/60, randint(1, 5), direction=randint(0, 3))

        clock.schedule_once(self.random_movement, randint(5, 15))

    def set_screen_size(self, zoom) -> None:
        self.screen_width /= zoom
        self.screen_height /= zoom

    def get_pos(self) -> list:
        return self.position

    def update(self, _, player_pos) -> None:
        x, y = player_pos

        self.sprite.x = self.position[0] * 16 + self.screen_width // 2 - x * 16
        self.sprite.y = self.position[1] * 16 + self.screen_height // 2 - y * 16

    #def set_direction(self, direction) -> None:
    #    self.velocity = [cos(direction), sin(direction)]

    def move(self, dt, direction) -> None:
        if not self.tilemap.test_collisions(self.position, direction):
            match direction:
                case 0:
                    self.position[0] += self.speed * dt
                case 1:
                    self.position[0] -= self.speed * dt
                case 2:
                    self.position[1] -= self.speed * dt
                case 3:
                    self.position[1] += self.speed * dt



class Child:
    MAX_SPEED = 40.0
    PERCEPTION_RADIUS = 100.0

    SOCIAL_ANXIETY_WEIGHT = 0.1
    PEER_PRESSURE_WEIGHT = 0.01
    ATTACHMENT_ISSUES_WEIGHT = 0.01

    def __init__(self, x, y, vx, vy, batch, screen_size) -> None:
        self.position = [x, y]
        self.velocity = [vx, vy]

        self.screen_width, self.screen_height = screen_size

        self.image = resource.image('assets/sprites/player/front-default.png', atlas=True)
        self.sprite = sprite.Sprite(self.image, x=self.position[0], y=self.position[1], batch=batch)
        
    def set_screen_size(self, zoom) -> None:
        self.screen_width /= zoom
        self.screen_height /= zoom

    def get_pos(self) -> list:
        return self.position

    def adjust_position(self, player_pos) -> None:
        x, y = player_pos

        self.sprite.x = self.screen_width // 2 - x * 16 + self.position[0]
        self.sprite.y = self.screen_height // 2 - y * 16 + self.position[1]

    def update(self, flock, player_pos) -> None:
        socialAnxiety = self.social_anxiety(flock)
        attachmentIssues = self.attachment_issues(flock)
        peerPressure = self.peer_pressure(flock)

        self.velocity[0] = (socialAnxiety[0] * Child.SOCIAL_ANXIETY_WEIGHT +
                            attachmentIssues[0] * Child.ATTACHMENT_ISSUES_WEIGHT +
                            peerPressure[0] * Child.PEER_PRESSURE_WEIGHT)

        self.velocity[1] = (socialAnxiety[1] * Child.SOCIAL_ANXIETY_WEIGHT +
                            attachmentIssues[1] * Child.ATTACHMENT_ISSUES_WEIGHT +
                            peerPressure[1] * Child.PEER_PRESSURE_WEIGHT)

        speed = sqrt(self.velocity[0]**2 + self.velocity[1]**2)

        if speed > Child.MAX_SPEED:
            self.velocity[0] = (self.velocity[0] / speed) * Child.MAX_SPEED
            self.velocity[1] = (self.velocity[1] / speed) * Child.MAX_SPEED

        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        
        self.adjust_position(player_pos)

    def social_anxiety(self, flock) -> list:
        steering = [0.0, 0.0]
        total = 0

        for child in flock:
            distance = sqrt((self.position[0] - child.position[0])**2 + (self.position[1] - child.position[1])**2)
            if 0 < distance < Child.PERCEPTION_RADIUS:
                steering[0] += child.velocity[0]
                steering[1] += child.velocity[1]
                total += 1

        if total > 0:
            steering[0] /= total
            steering[1] /= total

            speed = sqrt(steering[0]**2 + steering[1]**2)

            try:
                steering[0] = steering[0] / speed * Child.MAX_SPEED
            except ZeroDivisionError:
                steering[0] = 0

            try:
                steering[1] = steering[1] / speed * Child.MAX_SPEED
            except ZeroDivisionError:
                steering[1] = 0

            steering[0] -= self.velocity[0]
            steering[1] -= self.velocity[1]

        return steering

    def attachment_issues(self, flock) -> list:
        steering = [0.0, 0.0]
        total = 0

        for child in flock:
            distance = sqrt((self.position[0] - child.position[0])**2 + (self.position[1] - child.position[1])**2)
            if 0 < distance < Child.PERCEPTION_RADIUS:
                steering[0] += child.position[0]
                steering[1] += child.position[1]
                total += 1

        if total > 0:
            steering[0] /= total
            steering[1] /= total

            steering[0] -= self.position[0]
            steering[1] -= self.position[1]

            speed = sqrt(steering[0]**2 + steering[1]**2)

            try:
                steering[0] = steering[0] / speed * Child.MAX_SPEED
            except ZeroDivisionError:
                steering[0] = 0

            try:
                steering[1] = steering[1] / speed * Child.MAX_SPEED
            except ZeroDivisionError:
                steering[1] = 0

            steering[0] -= self.velocity[0]
            steering[1] -= self.velocity[1]

        return steering
    
    def peer_pressure(self, flock) -> list:
        steering = [0.0, 0.0]
        total = 0

        for child in flock:
            diff = [self.position[0] - child.position[0], self.position[1] - child.position[1]]
            distance = sqrt(diff[0]**2 + diff[1]**2)
            if 0 < distance < Child.PERCEPTION_RADIUS:
                steering[0] += diff[0] / distance
                steering[1] += diff[1] / distance
                total += 1

        if total > 0:
            steering[0] /= total
            steering[1] /= total

            speed = sqrt(steering[0]**2 + steering[1]**2)

            try:
                steering[0] = steering[0] / speed * Child.MAX_SPEED
            except ZeroDivisionError:
                steering[0] = 0

            try:
                steering[1] = steering[1] / speed * Child.MAX_SPEED
            except ZeroDivisionError:
                steering[1] = 0

            steering[0] -= self.velocity[0]
            steering[1] -= self.velocity[1]

        return steering

    