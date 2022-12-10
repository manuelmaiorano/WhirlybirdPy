import pygame, random
from utils import *

WINDOW_SIZE = 400, 600

PLAYER_SIZE = (10, 20)
PLATFORM_SIZE = (50, 5)

GRAVITY = 0.5
SPEED_INCREASE = 5
JUMP_IMPULSE = 15
BOOST_TIMEOUT = 150

MIN_PLAYER_Y = 200
MAX_PLAYER_Y = 550

OFFSET = 5
N_PLATFORMS = 20
PLATFORM_SPACING = 50
PLATFORM_SPEED = 1

SCORE_UPDATE = 1

#loading animations
still_platform = pygame.image.load('./assets/still.png')
moving_platform = load_animation('./assets/moving.png', 7)
breckable_platform = load_animation('./assets/break.png', PLATFORM_SIZE[1])
spike_moving_platform = load_animation('./assets/spike.png', 20)
cloud_platform = load_animation('./assets/cloud.png', PLATFORM_SIZE[1])
bounce_platform = load_animation('./assets/bounce.png', 7)

#player
player_img = pygame.image.load('./assets/player.png')
pl_front_img = pygame.image.load('./assets/pl_front.png')

#hat
hat_animation = load_animation('./assets/hat.png', 7)


class Player(pygame.sprite.Sprite):

    def __init__(self, area_rect, *groups):
        super().__init__(*groups)       
        
        self.area_rect = area_rect

        self.image = player_img
        self.facing_left = self.image
        self.facing_right = pygame.transform.flip(self.image, True, False)
        self.facing_front = pl_front_img
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(self.area_rect.center)
        self.speed = pygame.math.Vector2((0,0))
        
        self.rect.center  = self.pos

        self.is_boosting = False
        self.time_boosting = 0 
        self.hat = Hat((0,0))

        self.falling_time = 0

    def update(self):
        self.process_input()

        if self.is_boosting:
            self.hat.rect.centerx = self.rect.centerx
            self.hat.rect.centery = self.rect.centery-12

            self.speed.y = -JUMP_IMPULSE
            if self.time_boosting > BOOST_TIMEOUT:
                self.is_boosting = False
                self.time_boosting = 0
                self.speed.y = 0
                self.image = self.facing_right
                self.hat.kill()
            else : self.time_boosting += 1
        else:    
            self.speed.y += GRAVITY 

        self.speed.y = min(self.speed.y, 10)

        self.pos += self.speed 
        self.rect.center  = self.pos

        if self.speed.y > 0: self.falling_time += 1
        else: self.falling_time = 0

        self.keep_in_area()

    def boost(self):
        if not self.is_boosting:
            self.is_boosting = True
            self.image = self.facing_front

    def jump(self):
        self.speed.y = -JUMP_IMPULSE

    def big_jump(self):
        self.speed.y = -JUMP_IMPULSE * 2


    def keep_in_area(self):
        if self.pos.x < 0: 
            self.pos.x = self.area_rect.right
        elif self.pos.x > self.area_rect.right:
            self.pos.x = 0

        self.rect.center = self.pos
            
    def process_input(self):
        key = pygame.key.get_pressed()
        if key[pygame.K_d]:
            self.pos.x += SPEED_INCREASE
            if not self.is_boosting: self.image = self.facing_right
        elif key[pygame.K_a]:
            self.pos.x -= SPEED_INCREASE
            if not self.is_boosting: self.image = self.facing_left

        

class Platform(pygame.sprite.Sprite):
    def __init__(self,  *groups):
        super().__init__(*groups)

        self.callbacks = []
    
    def handle_collision(self):
        for callback in self.callbacks: callback()

class StillPlatform(Platform):
     def __init__(self, initial_pos,*groups):
        super().__init__(*groups)

        self.image = still_platform
        self.rect = self.image.get_rect()

        self.rect.bottomleft = initial_pos

class MovingPlatform(Platform):
    def __init__(self, area_rect, initial_pos, *groups):
        super().__init__( *groups)

        self.animation = Animation(moving_platform, 0.05)

        self.image = self.animation.current_frame
        self.rect = self.image.get_rect()
        self.rect.bottomleft = initial_pos
        
        self.area_rect = area_rect
        self.speedx = PLATFORM_SPEED

        self.hat = None
    
    def update(self):

        self.rect.centerx += self.speedx
        if self.hat: self.hat.rect.centerx = self.rect.centerx
        self.collide_with_walls()

        self.image = self.animation.next_frame()

    def collide_with_walls(self):
        if self.rect.right > self.area_rect.right:
            self.rect.right = self.area_rect.right
            self.speedx *= -1

        elif self.rect.left < self.area_rect.left:
            self.rect.left = self.area_rect.left
            self.speedx *= -1

class BreakablePlatform(Platform):
    def __init__(self, initial_pos,*groups):
        super().__init__( *groups)
        self.animation = Animation(breckable_platform, 0.08)

        self.image = self.animation.current_frame
        self.rect = self.image.get_rect()

        self.rect.bottomleft = initial_pos

        self.collided = False

    def handle_collision(self):
        if not self.collided:
            super().handle_collision()
            self.collided = True

    def update(self):
        if self.collided:
            if self.animation.frame_index < len(self.animation.frames)-1: 
                self.image = self.animation.next_frame()
            else: self.kill()

class SpikeMovingPlatform(MovingPlatform):
    def __init__(self, area_rect, initial_pos, *groups):
        super().__init__(area_rect, initial_pos, *groups)

        self.animation = Animation(spike_moving_platform, 0.08)

        self.image = self.animation.current_frame
        self.rect = self.image.get_rect()
        self.rect.bottomleft = initial_pos

        self.speedy = 0
        self.callbacks = {'spike_out': None, 'spike_in': None}
        self.collided = False

    def handle_collision(self):
        r = random.random()
        if r > 0.9 and self.callbacks['spike_out']:
            self.callbacks['spike_out']()
        else:
            self.callbacks['spike_in']()
        self.collided = True

    def update(self):
        if not self.collided:
            self.rect.centerx += self.speedx
            super().collide_with_walls()
            self.image = self.animation.next_frame()
        else:
            self.speedy += GRAVITY
            self.rect.centerx += self.speedx
            self.rect.centery += self.speedy

class CloudPlatorm(Platform):
    def __init__(self, initial_pos, listener=None, *groups):
        super().__init__(listener, *groups)

        self.animation = Animation(cloud_platform, 0.08)

        self.image = self.animation.current_frame
        self.rect = self.image.get_rect()

        self.rect.bottomleft = initial_pos

        self.collided = False

    def handle_collision(self):
        if not self.collided:
            self.collided = True

    def update(self):
        
        if self.collided:
            if self.animation.frame_index < len(self.animation.frames)-1: 
                self.image = self.animation.next_frame()
            else: self.kill()

class BoucePlatform(Platform):
    def __init__(self, initial_pos,*groups):
        super().__init__( *groups)

        self.animation = Animation(bounce_platform, 0.02)

        self.image = self.animation.current_frame
        self.rect = self.image.get_rect()

        self.rect.bottomleft = initial_pos

        self.collided = False

    def handle_collision(self):
        super().handle_collision()
        self.collided = True

    def update(self):
        if self.collided:
            self.image = self.animation.next_frame()
            if self.animation.frame_index > len(self.animation.frames):
                self.collided = False

class Hat(Platform):

    def __init__(self, pos, *groups):
        super().__init__(*groups)  
        self.animation = Animation(hat_animation, 0.05)
        self.image = self.animation.current_frame
        self.rect = self.image.get_rect()
        self.rect.center = pos
    
    def update(self):
        self.image = self.animation.next_frame()

    def handle_collision(self):
        super().handle_collision()
        self.kill()

class PlatformGroup(pygame.sprite.Group):


    def move(self, offset):
        for sprite in self.sprites():
            sprite.rect.y += offset



class Game:

    def __init__(self, window_rect):

        self.window_rect = window_rect

        self.visible_sprites = pygame.sprite.Group()
        self.platforms = PlatformGroup()
        self.player = pygame.sprite.GroupSingle()

        self.dist = {0: 0.4, 1: 0.3, 2: 0.1, 3:0.05, 4: 0.025, 5: 0.025}
        self.weights = {0: 20, 1: 15, 2: 10, 3:5, 4: 4, 5: 1}

        self.callback = None

        self.add_sprites()

        self.update_high_score_callback = None
        self.score = 0

    def add_sprites(self):
        Player(self.window_rect, [self.player, self.visible_sprites])

        self.end_pos = pygame.math.Vector2((random.randrange(0, self.window_rect.width-PLATFORM_SIZE[0]), 
                                            self.window_rect.bottom))

        for i in range(N_PLATFORMS):
            self.add_single_platform()

    def add_single_platform(self):
        self.create_new_platform()
        self.end_pos.x = random.randrange(0, self.window_rect.width-PLATFORM_SIZE[0])
        self.end_pos.y -= PLATFORM_SPACING

    def create_new_platform(self):
        o = outcome(self.dist)
        r = random.random()

        if  o == 1:
            p = StillPlatform(self.end_pos, [self.platforms, self.visible_sprites])
            p.callbacks.append(self.player.sprite.jump)
            if r > 0.9:
                posx, posy = p.rect.center
                posy  -= 10
                p = Hat((posx, posy), [self.platforms, self.visible_sprites])
                p.callbacks.append(self.add_player_hat)
                p.callbacks.append(self.player.sprite.boost)

        elif o == 5:
            p = SpikeMovingPlatform(self.window_rect, self.end_pos, [self.platforms, self.visible_sprites])
            p.callbacks['spike_in'] = self.player.sprite.jump
            p.callbacks['spike_out'] = self.callback
        elif o == 3:
            p = BreakablePlatform(self.end_pos, [self.platforms, self.visible_sprites])
            p.callbacks.append(self.player.sprite.jump)
            p.callbacks.append(self.add_single_platform)
        elif o == 4:
            p = CloudPlatorm(self.end_pos, [self.platforms, self.visible_sprites])
            p.callbacks.append(self.add_single_platform)
        elif o == 0:
            p = BoucePlatform(self.end_pos,  [self.platforms, self.visible_sprites])
            p.callbacks.append(self.player.sprite.big_jump)
        else:
            p = MovingPlatform(self.window_rect, self.end_pos,  [self.platforms, self.visible_sprites])
            p.callbacks.append(self.player.sprite.jump)
            if r > 0.9:
                posx, posy = p.rect.center
                posy  -= 10
                h = Hat((posx, posy), [self.platforms, self.visible_sprites])
                h.callbacks.append(self.add_player_hat)
                h.callbacks.append(self.player.sprite.boost)
                p.hat = h

    def handle_click(self, event):pass

    def update(self, dt):
        self.visible_sprites.update()

        self.check_collision()

        self.check_vertical_scroll()

        self.manage_platforms()

        self.update_distribution()

        self.check_player_death()

    def check_collision(self):
        collided = pygame.sprite.spritecollideany(self.player.sprite, self.platforms)
        if collided and self.player.sprite.speed.y > 0:
            #self.player.sprite.rect.bottom = collided.rect.top
            collided.handle_collision()
    
    def reposition_player(self, platform):
        self.player.sprite.rect.bottom = platform.rect.top


    def check_vertical_scroll(self):
        player_pos = self.player.sprite.pos
        offset = -self.player.sprite.speed.y
        if player_pos.y < MIN_PLAYER_Y:
            self.player.sprite.pos.y = MIN_PLAYER_Y
            self.platforms.move(offset)
            self.end_pos.y += offset
            self.score += SCORE_UPDATE
            self.update_high_score_callback(self.score)
        elif player_pos.y > MAX_PLAYER_Y:
            self.player.sprite.pos.y = MAX_PLAYER_Y
            self.platforms.move(offset)
            self.end_pos.y += offset

    def check_player_death(self):
        if self.player.sprite.falling_time > 150  and self.callback:
            self.callback()

    def manage_platforms(self):
        for platform in self.platforms.sprites():
            if platform.rect.y >= self.window_rect.bottom:
                platform.kill()
                self.add_single_platform()

    def update_distribution(self):
        if not self.score % 500:
            for difficulty in self.weights:
                increase = self.score/500 * difficulty
                self.weights[difficulty] += increase

            self.dist = normalize(self.weights)

    def add_player_hat(self):
        self.player.sprite.hat = Hat((0,0), [self.visible_sprites])

    def draw(self, screen):
        screen.fill('white')
        self.visible_sprites.draw(screen)

class InitialMenu:
    def __init__(self, window_rect):
        self.window_rect = window_rect
        self.player = Player(self.window_rect)
        self.banner = pygame.Surface((self.window_rect.width, 35))
        self.banner_rect = self.banner.get_rect()
        self.banner.fill('black')
        self.text = pygame.font.SysFont('Arial', 30, True).render('START', True, 'white')

        self.player.pos = self.window_rect.center

        self.callback = None

    def draw_banner(self, screen):
        self.banner_rect.bottomleft = self.window_rect.bottomleft
        screen.blit(self.banner, self.banner_rect)

        text_rect = self.text.get_rect()
        text_rect.center = self.banner_rect.center
        screen.blit(self.text, text_rect)

    def update(self, dt):
        self.player.update()
        if self.player.rect.colliderect(self.banner_rect): self.player.jump()

    def draw(self, screen):
        screen.fill('white')
        self.draw_banner(screen)
        screen.blit(screen, self.player.rect, self.player.rect)
        screen.blit(self.player.image, self.player.rect)

    def handle_click(self, event):
        
        if self.banner_rect.collidepoint(pygame.mouse.get_pos()) and self.callback:
            self.callback()


class GameOverMenu:
    def __init__(self, window_rect):
        self.window_rect = window_rect
        self.text = pygame.font.SysFont('Arial', 30, True).render('GAME OVER', True, 'black')
        self.text_rect = self.text.get_rect()
        self.text_rect.center = window_rect.center
        self.text_rect.centery -= 100

        self.restart_button = pygame.Surface((20,20))
        self.restart_rect = self.restart_button.get_rect()
        self.restart_rect.center = self.window_rect.center
        self.restart_rect.centery += 200
        self.restart_button.fill('black')

        self.callback = None

    def update(self, dt):pass

    def draw(self, screen):
        screen.fill('white')
        screen.blit(self.text, self.text_rect)
        screen.blit(self.restart_button, self.restart_rect)

    def handle_click(self, event):
        
        if self.restart_rect.collidepoint(pygame.mouse.get_pos()) and self.callback:
            self.callback()


        
class GameManager:
    def __init__(self, window_rect):
        self.window_rect = window_rect
        self.current_scene = InitialMenu(self.window_rect)
        self.current_scene.callback = self.on_start

        self.top_banner = pygame.Surface((self.window_rect.width, 30))
        self.top_banner.fill('white')
        self.top_banner_rect = self.top_banner.get_rect()

        self.is_playing = False

        f = open('./assets/high_score.txt', 'r')
        self.high_score = int(f.readline())
        f.close()

    def update_high_score(self, new_score):
        if new_score > self.high_score: self.high_score = new_score

    def on_press(self, event):
        if event.key == pygame.K_r:
            self.on_start()
        elif event.key == pygame.K_i and self.is_playing:
            print(self.current_scene.dist)

    def on_start(self):
        self.current_scene = Game(self.window_rect)
        self.current_scene.callback = self.on_player_death
        self.current_scene.update_high_score_callback = self.update_high_score
        self.is_playing = True

    def on_player_death(self):
        self.current_scene = GameOverMenu(self.window_rect)
        self.current_scene.callback = self.on_start
        self.is_playing = False

        f = open('./assets/high_score.txt', 'w')
        f.write(str(self.high_score))
        f.close()

    def update(self, dt):
        self.current_scene.update(dt)

    def draw(self, screen):
        self.current_scene.draw(screen)
        if self.is_playing:
            text_surf = pygame.font.SysFont('Arial', 30, True)\
                            .render('%s HI: %s'%(self.current_scene.score, self.high_score), True, 'black')
            
            screen.blit(self.top_banner, (0,0))
            screen.blit(text_surf, (0,0))

    def handle_click(self, event):
        self.current_scene.handle_click(event)


if __name__ == '__main__':
    engine = Engine(WINDOW_SIZE)
    # engine.scene = Game(engine.window_rect)
    engine.scene = GameManager(engine.window_rect)

    engine.event_system.subscribe(engine.scene.handle_click, pygame.MOUSEBUTTONDOWN)
    engine.event_system.subscribe(engine.scene.on_press, pygame.KEYDOWN)


    engine.mainloop()