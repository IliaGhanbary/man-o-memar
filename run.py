import pygame
import os
from os.path import join

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 10
BULLET_COOLDOWN = 15

class Entity(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, color, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill(color)
        self.mask = pygame.mask.from_surface(self.image)
        self.name = name
        self.hit = False

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))

class NPC(Entity):
    COLOR = (0, 0, 0)
    
    def __init__(self, x, y, width, height, name=None):
        super().__init__(x, y, width, height, self.COLOR, name)
        self.hp = 100

    def draw(self, window):
        if self.hp > 0:
            super().draw(window)
        else:
            self.kill()

class Gun(Entity):
    COLOR = (0, 0, 0)
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, self.COLOR)

class Bullet(Entity):
    COLOR = (255, 255, 0)
    
    def __init__(self, x, y, width, height, direction):
        super().__init__(x, y, width, height, self.COLOR)
        self.direction = direction
        self.speed = BULLET_SPEED
        self.lifetime = FPS * 3

    def update(self):
        self.rect.x += -self.speed if self.direction == "left" else self.speed
        self.lifetime -= 1
        
        if self.lifetime <= 0:
            self.kill()

class Player(Entity):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    MAX_JUMP_COUNT = 1

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, self.COLOR)
        self.hp = 200
        self.x_speed = 0
        self.y_speed = 0
        self.direction = "left"
        self.fall_count = 0
        self.jump_count = 0
        self.hit_count = 0
        self.bullets = pygame.sprite.Group()
        self.shoot_cooldown = 0

    def shoot(self):
        if self.shoot_cooldown <= 0:
            offset_x = self.rect.left - 10 if self.direction == "left" else self.rect.right
            bullet = Bullet(offset_x, self.rect.centery, 10, 5, self.direction)
            self.bullets.add(bullet)
            self.shoot_cooldown = BULLET_COOLDOWN
            return bullet
        return None

    def jump(self):
        if self.jump_count < self.MAX_JUMP_COUNT:
            self.y_speed = -self.GRAVITY * 8
            self.jump_count += 1
            if self.jump_count == 1:
                self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, speed):
        self.x_speed = -speed
        if self.direction != "left":
            self.direction = "left"

    def move_right(self, speed):
        self.x_speed = speed    
        if self.direction != "right":
            self.direction = "right"

    def landed(self):
        self.fall_count = 0
        self.y_speed = 0
        self.jump_count = 0

    def hit_head(self):
        self.fall_count = 0
        self.y_speed *= -1

    def loop(self, fps):
        self.y_speed += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_speed, self.y_speed)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        self.bullets.update()

    def draw(self, window):
        super().draw(window)
        for bullet in self.bullets:
            bullet.draw(window)

class Object(Entity):

    def __init__(self, x, y, width, height, name=None):
        super().__init__(x, y, width, height, (0, 0, 255), name)

class Platform(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = Game().get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("brawlforge")
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        
    def get_block(self, size):
        path = join("assets", "Terrain", "Terrain.jpg")
        image = pygame.image.load(path).convert_alpha()
        surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
        rect = pygame.Rect(96, 0, size, size)
        surface.blit(image, (0, 0), rect)
        return pygame.transform.scale2x(surface)

    def get_background(self, name):
        image = pygame.image.load(join("assets", "background", name))
        _, _, width, height = image.get_rect()
        tiles = []

        for i in range(SCREEN_WIDTH // width + 1):
            for j in range(SCREEN_HEIGHT // height + 1):
                pos = (i * width, j * height)
                tiles.append(pos)

        return tiles, image

    def draw(self, background, background_image, player, objects, platforms, npcs):
        for tile in background:
            self.window.blit(background_image, tile)

        for obj in platforms:
            obj.draw(self.window)

        for obj in objects:
            obj.draw(self.window)

        for npc in npcs:
            if npc.hp > 0:
                npc.draw(self.window)

        player.draw(self.window)

        pygame.display.update()

    def handle_vertical_collision(self, player, objects, platforms, npcs, dy):
        collided_objects = []
        for obj in objects:
            if pygame.sprite.collide_mask(player, obj):
                if dy > 0:
                    player.rect.bottom = obj.rect.top
                    player.landed()
                elif dy < 0:
                    player.rect.top = obj.rect.bottom
                    player.hit_head()
                collided_objects.append(obj)
        
        for obj in platforms:
            if pygame.sprite.collide_mask(player, obj):
                if dy > 0:
                    player.rect.bottom = obj.rect.top
                    player.landed()
                elif dy < 0:
                    player.rect.top = obj.rect.bottom
                    player.hit_head()
                collided_objects.append(obj)    

        for obj in npcs:
            if obj.hp > 0 and pygame.sprite.collide_mask(player, obj):
                if dy > 0:
                    player.rect.bottom = obj.rect.top
                    player.landed()
                elif dy < 0:
                    player.rect.top = obj.rect.bottom
                    player.hit_head()
                collided_objects.append(obj)            

        return collided_objects

    def collide(self, player, objects, platforms, npcs, dx):
        player.move(dx, 0)
        collided_object = None
        for obj in objects:
            if pygame.sprite.collide_mask(player, obj):
                collided_object = obj
                break
        for obj in platforms:
            if pygame.sprite.collide_mask(player, obj):
                collided_object = obj
                break
        for obj in npcs:
            if obj.hp > 0 and pygame.sprite.collide_mask(player, obj):
                collided_object = obj
                break    
        
        player.move(-dx, 0)
        return collided_object

    def handle_bullet_collisions(self, player, objects, platforms, npcs):
        for bullet in player.bullets:
            if bullet.rect.right < 0 or bullet.rect.left > SCREEN_WIDTH:
                bullet.kill()
                continue
                
            for platform in platforms:
                if pygame.sprite.collide_mask(bullet, platform):
                    bullet.kill()
                    break
                    
            for obj in objects:
                if pygame.sprite.collide_mask(bullet, obj):
                    bullet.kill()
                    break
                    
            for npc in npcs:
                if npc.hp > 0 and pygame.sprite.collide_mask(bullet, npc):
                    npc.hp -= 10
                    bullet.kill()
        
                    if npc.hp <= 0:
                        npc.kill()
                    break

    def handle_movement(self, player, objects, platforms, npcs):
        keys = pygame.key.get_pressed()

        player.x_speed = 0
        collide_left = self.collide(player, objects, platforms, npcs, -PLAYER_SPEED * 2)
        collide_right = self.collide(player, objects, platforms, npcs, PLAYER_SPEED * 2)
        
        if keys[pygame.K_a] and not collide_left:
            player.move_left(PLAYER_SPEED) 
        if keys[pygame.K_d] and not collide_right:
            player.move_right(PLAYER_SPEED)

        if pygame.mouse.get_pressed()[0]: 
            player.shoot()

        self.handle_vertical_collision(player, objects, platforms, npcs, player.y_speed)

    def main(self):
        background, background_image = self.get_background("bg.jpg")

        player = Player(100, 100, 50, 50)
        block_size = 96
        platforms = [
            Platform(300, 400, block_size),
            Platform(500, 300, block_size),
            Platform(200, 200, block_size),
            Platform(600, 400, block_size),
            Platform(100, 300, block_size)
        ]
        enemies = [NPC(500, 450, 50, 50, "demon")]
        floor = [Platform(i * block_size, SCREEN_HEIGHT - block_size, block_size) 
                 for i in range(-SCREEN_WIDTH // block_size, (SCREEN_WIDTH * 2) // block_size)]

        run = True
        while run:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and player.jump_count < 1:
                        player.jump()

            player.loop(FPS)
            self.handle_movement(player, floor, platforms, enemies)
            self.handle_bullet_collisions(player, floor, platforms, enemies)
            
            enemies = [npc for npc in enemies if npc.hp > 0]
            
            self.draw(background, background_image, player, floor, platforms, enemies)
        
        pygame.quit()
        quit()

if __name__ == "__main__":
    game = Game()
    game.main()
