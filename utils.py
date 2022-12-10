import pygame, random

def outcome(dist):
    r = random.random()
    cum_prob = 0
    for value, prob in dist.items():
        cum_prob += prob
        if r < cum_prob: return value

def normalize(weights):
    tot = 0
    new_dist = {}
    for prob in weights.values():
        tot += prob

    for value in weights:
        new_dist[value] = weights[value]/tot

    return new_dist

def load_animation(filename, frame_height):
    frames = []

    frames_img = pygame.image.load(filename)
    frame_width, total_height = frames_img.get_rect().size
    
    n_rows = total_height // frame_height

    currenty = 0
    for i in range(n_rows): 
        rect = pygame.Rect(0, currenty, frame_width, frame_height)
        frames.append(frames_img.subsurface(rect))
        
        currenty += frame_height

    return frames



class Animation:
    def __init__(self, frames, frame_speed):
        self.frames = frames
        self.frame_speed = frame_speed
        self.frame_index = 0
        self.current_frame = self.frames[int(self.frame_index)]

    def next_frame(self):
        self.frame_index += self.frame_speed
        if self.frame_index > len(self.frames): self.frame_index -= len(self.frames)
        self.current_frame = self.frames[int(self.frame_index)]
        return self.current_frame


class EventSystem:
    def __init__(self):

        self.subscribers = {
            pygame.QUIT : [],
            pygame.MOUSEBUTTONDOWN: [],
            pygame.KEYDOWN : []
        }
        EventSystem.TIMEOUT_EVENT =  self.add_event()

    def add_event(self):
        event = pygame.event.custom_type()
        self.subscribers[event] = []
        return event
    
    def post(self, event_type, **args):
        pygame.event.post(pygame.event.Event(event_type, **args))


    def subscribe(self, handler, eventype):
        if not eventype in self.subscribers: raise KeyError()
        self.subscribers[eventype].append(handler)

    def unsubscribe(self, handler, eventype):
        if not eventype in self.subscribers: raise KeyError()
        self.subscribers[eventype].remove(handler)

    def dispatch(self):
        for event in pygame.event.get():
            if event.type in self.subscribers:
                for handler in self.subscribers[event.type]:
                    handler(event)    


class Engine:
    def __init__(self, size):
        pygame.init()
        self.screen = pygame.display.set_mode(size)
        self.clk = pygame.time.Clock()
        self.event_system = EventSystem()
        self.scene = None
        self.running = True
        self.window_rect = pygame.display.get_surface().get_rect()

        self.event_system.subscribe(self.on_quit, pygame.QUIT)

        self.frame_rate = 60

        self.dt = 1/self.frame_rate

    def on_quit(self, event):
        self.running = False

    def mainloop(self):
        while self.running:
            self.event_system.dispatch()
            self.scene.update(self.dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
            self.clk.tick(60)
        pygame.quit()

def saturate(val, max, min):
    if val > max: return max
    if val < min: return min
    return val