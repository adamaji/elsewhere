import pygame, sys, math, random
from pygame.locals import *

WINDOWWIDTH = 800
WINDOWHEIGHT = 600
FPS = 40

TOP_SIDE = 0
BOTTOM_SIDE = 2
LEFT_SIDE = 3
RIGHT_SIDE =1

TILESIZE = 40

NUMBEROFLEVELS = 17

PLAY = 1
MENU = 2

def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def loadSlicedSprites(w,h,filepath):
    images=[]
    masterImg=pygame.image.load(filepath)
    masterImg.set_colorkey((255,255,255))
    masterw,masterh=masterImg.get_size()
    for i in range(int(masterw/w)):
        images.append(masterImg.subsurface((i*w,0,w,h)))
    for image in images:
        image.set_colorkey((255,255,255))
    return images

def terminate():
    pygame.quit()
    sys.exit()

def splitCount(s, count):
     return [''.join(x) for x in zip(*[list(s[z::count]) for z in range(count)])]

def checkSide(dx,dy):
    if abs(dx) > abs(dy):
        dy = 0
    else:
        dx = 0
    if dy < 0:
        return TOP_SIDE
    elif dy > 0:
        return BOTTOM_SIDE
    elif dx < 0:
        return LEFT_SIDE
    elif dx > 0:
        return RIGHT_SIDE
    else:
        return 0, 0

def fadeToBlack():
    for i in range(30):
        DISPLAYSURF.fill((7,7,7),None,BLEND_SUB)
        pygame.display.update()
        FPSCLOCK.tick(FPS)

class SpeechBubble(pygame.sprite.Sprite):
    def __init__(self,x,y,txt):
        pygame.sprite.Sprite.__init__(self)
        self.texts = []
        for char in txt:
            self.texts.append(SMALLFONT.render(char, True, (0,0,0)))
        self.x = x
        self.y = y

        self.count = 1

    def draw(self):
        pygame.draw.rect(DISPLAYSURF, (255,255,255), (self.x,self.y,100,55))
        pygame.draw.polygon(DISPLAYSURF, (255,255,255), ((self.x+5,self.y+55),(self.x+20,self.y+55),(self.x-5,self.y+70)))
        for i in range(self.count):
            DISPLAYSURF.blit(self.texts[i],(self.x+(i%11)*9,self.y+(i/11)*10))
        if self.count<len(self.texts):
            self.count += 1

    def next_msg(self):
        self.kill()
        
    def update(self,x,y):
        self.x = x
        self.y = y
        self.draw()
    
class Collidable(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.collision_groups = []

    def __str__(self):
        return "Objects that are collidable within the environment."
    
    def collidesWith(self, group):
        if group not in self.collision_groups:
            self.collision_groups.append(group)

    def move(self, dx, dy, collide=True):
        if collide:
            if dx!=0:
                self.rect.x += dx
                side = checkSide(dx, 0)
                for group in self.collision_groups:
                    for obj in group:
                        if obj.rect.colliderect(self.rect):
                            self.onCollision(side, obj)
            if dy!=0:
                self.rect.y += dy
                side = checkSide(0, dy)
                for group in self.collision_groups:
                    for obj in group:
                        if obj.rect.colliderect(self.rect):
                            self.onCollision(side, obj)
        else:
            self.rect.x += dx
            self.rect.y += dy

    def toSide(self, obj, side):
        if side == TOP_SIDE:
            self.rect.top = obj.rect.bottom
        if side == BOTTOM_SIDE:
            self.rect.bottom = obj.rect.top
        if side == RIGHT_SIDE:
            self.rect.right = obj.rect.left
        if side == LEFT_SIDE:
            self.rect.left = obj.rect.right

    def onCollision(self, side, obj):
        self.toSide(obj, side)

        
class Enemy(Collidable):
    def __init__(self,(x,y),key):
        Collidable.__init__(self)
        self.img = loadSlicedSprites(80,30,'img/saw.png')
        self.rect = pygame.Rect(x,y,60,30)
        self.rect.center = (x,y+5)
        self.frame = 0
        self.facingleft = False
        self.last_update = 0

        self.dx = 3

        self.min = x - int(key[0])
        self.max = x + int(key[1])

    def draw(self,t,images):
        if t-self.last_update > 3000/FPS:
            self.frame += 1
            if self.frame>=len(images):
                self.frame = 0
            self.last_update = t
        if self.frame >= len(images):
            self.frame = 0
        if not self.facingleft:
            self.image = pygame.transform.flip(images[self.frame],1,0)
            DISPLAYSURF.blit(self.image, (self.rect.x-15,self.rect.y))
        else:
            self.image = images[self.frame]
            DISPLAYSURF.blit(self.image, (self.rect.x-5,self.rect.y))
        #pygame.draw.rect(DISPLAYSURF, (255,0,0), self.rect, 1)        

    def update(self):
        self.draw(pygame.time.get_ticks(),self.img)        
        self.rect.x += self.dx
        if self.rect.x > self.max or self.rect.x < self.min:
            self.facingleft = not self.facingleft
            self.dx = -self.dx   
            
class Player(Collidable):

    def __init__(self,(x,y)):
        Collidable.__init__(self)
        self.dx = 0
        self.jump_speed = 0
        self.jump_accel = 4
        self.arm_angle = 0
        self.img_idle = loadSlicedSprites(TILESIZE,TILESIZE,'img/roxanne_idle.png')
        self.img_walk = loadSlicedSprites(TILESIZE,TILESIZE,'img/roxanne_walk.png')
        self.img_jump = loadSlicedSprites(TILESIZE,TILESIZE,'img/roxanne_jump.png')
        self.img_dead = loadSlicedSprites(TILESIZE,TILESIZE,'img/dead.png')
        self.masterimg_arm = pygame.image.load('img/roxanne_arm.png')
        self.masterimg_arm.set_colorkey((255,255,255))
        self.img_arm = self.masterimg_arm
        self.img_arm.set_colorkey((255,255,255))
        self.img_crosshair = pygame.image.load('img/crosshair.png')
        self.img_crosshair.set_colorkey((255,255,255))
        self.img = self.img_idle[0]        
        self.rect = pygame.Rect(x,y,TILESIZE,TILESIZE)
        self.rect.center = (x,y)
        self.rect = self.rect.inflate(-10,0)
        self.frame = 0
        self.facingleft = False
        self.last_update = 0

        self.shots = pygame.sprite.Group()
        
        self.walking = True
        self.jumping = True

        self.maxvelocity = 6

        self.color = (255,0,0)

        self.sound_shoot = pygame.mixer.Sound('sound/pew.wav')
        self.sound_walk = pygame.mixer.Sound('sound/walk.ogg')
        
    def __str__(self):
        return "The main player."

    def draw(self,t,images):
        if t-self.last_update > 3000/FPS:
            self.frame += 1
            if self.frame>=len(images):
                self.frame = 0
            self.last_update = t
        if self.frame >= len(images):
            self.frame = 0
        if not self.facingleft:
            self.image = pygame.transform.flip(images[self.frame],1,0)
        else:
            self.image = images[self.frame]
        DISPLAYSURF.blit(self.image, self.rect.topleft)
        DISPLAYSURF.blit(self.img_crosshair, (pygame.mouse.get_pos()[0]-20,pygame.mouse.get_pos()[1]-20))
        #pygame.draw.rect(DISPLAYSURF, self.color, self.rect, 1)

    def onCollision(self, side, sprite):
        self.toSide(sprite, side)
        if side == TOP_SIDE:
            self.jump_speed = 0
        if side == BOTTOM_SIDE:
            self.jump_speed = 0
            self.jumping = False

    def jump(self):
        if not self.jumping:
            self.jump_speed = -6
            self.jumping = True
            self.move(0, -4)

    def kill(self):
        pygame.sprite.Sprite.kill(self)
        
    def sawkill(self,m):
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 7000/FPS:
            m.update()
            self.draw(pygame.time.get_ticks(),self.img_dead)
            pygame.display.update()
            FPSCLOCK.tick(FPS)
        self.kill()

    def shoot(self):
        if len(self.shots) <= 0:
            #for shot in self.shots:
                #shot.kill()
            if self.facingleft:
                #self.shots.add(Bullet(self.rect.x,self.rect.y+20,self.arm_angle,self))
                self.shots.add(Bullet(self.rect.center[0]+math.cos(self.arm_angle)*20,self.rect.center[1]+math.sin(self.arm_angle)*20,self.arm_angle,self))                
            else:
                #self.shots.add(Bullet(self.rect.x+40,self.rect.y+20,self.arm_angle,self))
                self.shots.add(Bullet(self.rect.center[0]+math.cos(self.arm_angle)*20,self.rect.center[1]-math.sin(self.arm_angle)*20,self.arm_angle,self))                                
            self.sound_shoot.play()
            #print math.degrees(self.arm_angle)
                
    def updateArm(self):
        self.img_arm = pygame.transform.rotate(self.masterimg_arm, math.degrees(self.arm_angle)+180)
        if not self.facingleft:
            self.img_arm = pygame.transform.rotate(self.masterimg_arm, (-1)*math.degrees(self.arm_angle)+180)
            self.img_arm = pygame.transform.flip(self.img_arm,0,1)            
            
        DISPLAYSURF.blit(self.img_arm, self.rect.topleft)

    def update(self):
        self.dx = 0
        pressed = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        self.arm_angle = math.atan2((-1)*(mouse_pos[1]-self.rect.y),(mouse_pos[0]-self.rect.x))
        self.updateArm()

        if pressed[K_UP] or pressed[K_w] or pressed[K_SPACE]:
            self.jump_accel = 0.3
            self.jump()
        else:
            self.jump_accel = 1

        if pressed[K_LEFT] or pressed[K_a]:
            self.facingleft = True
            self.dx = -3
        if pressed[K_RIGHT] or pressed[K_d]:
            self.facingleft = False
            self.dx = 3
        if pressed[K_LSHIFT]:
            self.dx *= 2

        if pygame.mouse.get_pressed()[0]:
            self.shoot()
            
        if self.jump_speed < 8:
            self.jump_speed += self.jump_accel
        if self.jump_speed > 3:
            self.jumping = True

        self.move(self.dx, self.jump_speed)
        self.shots.update()

        if self.rect.y > WINDOWHEIGHT:
            self.kill()
        
        if self.jumping:
            self.draw(pygame.time.get_ticks(),self.img_jump)
        else:
            self.walking = (self.dx!=0)
            if self.walking:
                self.draw(pygame.time.get_ticks(),self.img_walk)
                #self.sound_walk.play()
            else:
                self.draw(pygame.time.get_ticks(),self.img_idle)

class Bullet(Collidable):

    def __init__(self,x,y,angle, p):
        Collidable.__init__(self)
        self.image = pygame.image.load('img/bullet.png')
        self.image.set_colorkey((255,255,255))
        self.image = pygame.transform.rotate(self.image, math.degrees(angle)+180)
        self.rect = self.image.get_rect().inflate(-30,-30)
        self.rect.center = (x,y)
        self.degree = angle
        self.env = p.collision_groups

        self.player = p

    def __str__(self):
        return "A projectile that will kill itself upon collision."

    def draw(self):
        DISPLAYSURF.blit(self.image, (self.rect.x-20,self.rect.y-15))
        #DISPLAYSURF.blit(self.image, (self.rect.x,self.rect.y))
        #pygame.draw.rect(DISPLAYSURF, (255,0,0), self.rect, 3)

    def update(self):
        self.rect.x += 20*math.cos(self.degree)
        self.rect.y -= 20*math.sin(self.degree)
        if self.rect.x > WINDOWWIDTH or self.rect.x < 0 or self.rect.y > WINDOWHEIGHT or self.rect.y < 0:
            self.kill()
        for group in self.env:
            for spr in pygame.sprite.spritecollide(self,group,False):
                if str(type(spr)) == "<class '__main__.Platform'>":
                    self.kill()
                if (str(type(spr)) == "<class '__main__.Switch'>") or (str(type(spr)) == "<class '__main__.MovingSwitch'>"):
                    self.kill()
                    spr.switch(self.player)
        self.draw()

class Platform(Collidable):
    
    def __init__(self,x,y,n):
        Collidable.__init__(self)
        self.x = x
        self.y = y
        filepath = 'img/platform' + str(n) + '.png'
        self.image = pygame.image.load(filepath)
        self.image.set_colorkey((255,255,255))
        self.rect = self.image.get_rect()
        self.rect.center = (self.x,self.y)
        
    def __str__(self):
        return "Immovable platform."

    def draw(self):
        DISPLAYSURF.blit(self.image, self.rect.topleft)
        
    def update(self):
        self.draw()

class Switch(Collidable):

    def __init__(self,x,y):
        Collidable.__init__(self)
        self.x = x
        self.y = y
        self.falseimage = pygame.image.load('img/switch1.png')
        self.falseimage.set_colorkey((255,255,255))
        self.trueimage = pygame.image.load('img/switch2.png')
        self.trueimage.set_colorkey((255,255,255))
        self.image = self.trueimage
        self.rect = self.image.get_rect()
        self.rect.center = (self.x,self.y)

        self.on = True

    def __str__(self):
        return "Toggled switch returns TRUE/FALSE"

    def switch(self,spr):
        x1 = self.rect.center[0]
        y1 = self.rect.center[1]
        x2 = spr.rect.center[0]
        y2 = spr.rect.center[1]

        x1n = x1
        y1n = y1
        x2n = x2
        y2n = y2

        dx = (x2-x1)/10
        dy = (y2-y1)/10

        for i in range(10):
            x1n += dx
            x2n -= dx
            y1n += dy
            y2n -= dy
            self.rect.center = (x1n, y1n)
            spr.rect.center = (x2n, y2n)
            self.draw()
            spr.draw(pygame.time.get_ticks(),spr.img_jump)
            pygame.display.update()
            FPSCLOCK.tick(FPS)

        self.rect.center = (x2, y2)
        spr.rect.center = (x1, y1)
        self.x = x2
        self.y = y2

    def draw(self):
        self.image = self.falseimage
        if self.on:
            self.image = self.trueimage
        DISPLAYSURF.blit(self.image,self.rect.topleft)

    def update(self):
        self.draw()

class MovingSwitch(Switch):
    def __init__(self,x,y,dx=3,dy=0,xmax=200,ymax=120):
        Switch.__init__(self,x,y)
        self.dx = dx
        self.dy = dy
        self.midx = x
        self.midy = y
        self.xmax = xmax
        self.ymax = ymax

    def move(self):
        self.x += self.dx
        self.y += self.dy
        if self.x > self.midx + self.xmax or self.x < self.midx - self.xmax:
            self.dx = -self.dx
        if self.y > self.midy + self.ymax or self.y < self.midy - self.ymax:
            self.dy = -self.dy
        self.rect.center = (self.x,self.y)

    def switch(self,spr):
        Switch.switch(self,spr)
        self.midx = self.x
        self.midy = self.y
        
    def update(self):
        self.move()
        self.draw()
        
        
class Map(object):

    def __init__(self,key,enemykey):
        self.platforms = pygame.sprite.Group()
        self.switches = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.entrance = (0,0)
        self.exit = pygame.Rect(0,0,TILESIZE,TILESIZE)
        self.img_exit = loadSlicedSprites(40, 40, 'img/exitgate.png')
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.populate(key,enemykey)

        ########

        self.img_cloud1 = pygame.image.load('img/menu_cloud1.png')
        self.img_cloud2 = pygame.image.load('img/menu_cloud2.png')
        self.img_cloud3 = pygame.image.load('img/menu_cloud3.png')

        self.img_citybg = pygame.image.load('img/city_bg.png')

        self.img_cloud1.set_colorkey((255,255,255))
        self.img_cloud2.set_colorkey((255,255,255))
        self.img_cloud3.set_colorkey((255,255,255))
        self.img_citybg.set_colorkey((255,255,255))

        self.x = 800            

    def __str__(self):
        return "The current level map."

    def populate(self,layout,enemy_params):
        #Map Key
        #Q - Entrance
        #E - Exit
        #2 - Up/Left Corner Tile
        #S - Switch
        
        x=TILESIZE/2
        y=TILESIZE/2
        e_count = 0
        for row in layout:
            x = TILESIZE/2
            for col in row:
                if isNumber(col):
                    self.platforms.add(Platform(x,y,col))
                if col == "Q":
                    self.entrance = (x,y)
                if col == "E":
                    self.exit.center = (x,y)
                if col == "S":
                    self.switches.add(Switch(x,y))
                if col == "M":
                    self.switches.add(MovingSwitch(x,y))
                if col == "V" and len(enemy_params)>e_count:
                    self.enemies.add(Enemy((x,y),enemy_params[e_count]))
                    e_count += 1
                x += TILESIZE
            y += TILESIZE

    def isExiting(self,playerRect):
        if self.exit.inflate(-40,-40).colliderect(playerRect):
            return True
        return False

    def displaybg(self):
        DISPLAYSURF.fill((46,48,151))

        DISPLAYSURF.blit(self.img_cloud1, (800-self.x,0))
        DISPLAYSURF.blit(self.img_cloud1, (0-self.x,0))
        DISPLAYSURF.blit(self.img_citybg, (0,0))
        for i in range(3):
            DISPLAYSURF.blit(self.img_cloud2, (i*800-self.x*2,0))
        
        #for i in range(6):
        #    DISPLAYSURF.blit(self.img_cloud3, (i*800-self.x*4,0))

        self.x -= 1
        if self.x < 0:
            self.x = 800          
        
    def update(self):
        self.displaybg()

        if pygame.time.get_ticks()-self.last_update > 3000/FPS:
            self.frame += 1
            if self.frame>=len(self.img_exit):
                self.frame = 0
            self.last_update = pygame.time.get_ticks()        
        DISPLAYSURF.blit(self.img_exit[self.frame], self.exit.topleft)
        self.platforms.update()
        self.switches.update()
        self.enemies.update()

      
    
def runLevel(n):
    global GAMESTATE

    maptxt = []
    mapfile = open('map/' + str(n) + '.txt', 'r')
    line = None
    while line != '':
        line = mapfile.readline().translate(None, '\n')
        maptxt.append(line)
    mapfile.close()

    enemytxt = []
    try:
        enemyfile = open('map/enemies/' + str(n) + '.txt', 'r')
        line = None
        while line != '':
            line = enemyfile.readline().translate(None, '\n')
            if line!= '':
                coords = line.split(',')
                enemytxt.append((coords[0],coords[1]))
        enemyfile.close()
    except:
        pass
    
    level_map = Map(maptxt,enemytxt)    
    player = Player(level_map.entrance)
    player_group = pygame.sprite.Group()
    text_group = pygame.sprite.Group()
    player_group.add(player)
    player.collidesWith(level_map.platforms)
    player.collidesWith(level_map.switches)
    #player.collidesWith(level_map.enemies)

    ###Tutorial Bubbles
    txt = ''
    if n == 1:
        txt = "I can use the W A and D keys to move. [Press S]"
    if n == 3:
        txt = "I can also shoot targets with the mouse."
    if n == 4:
        txt = "If I get stuck, I can press R to restart the level."
    if n == 6:
        txt = "Swapping conserves momentum."
    if n == 14:
        txt = "Better not touch those saws..."
    if txt != '':
        s = SpeechBubble(player.rect.x+50,player.rect.y-60,txt)
        text_group.add(s)
    
    while (not level_map.isExiting(player.rect)) and (player_group):
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            pressed = pygame.key.get_pressed()
            if pressed[K_ESCAPE]:
                GAMESTATE = MENU
                player_group.empty()
            if pressed[K_r]:
                player_group.empty()
            if pressed[K_s]:
                for bubble in text_group:
                    bubble.next_msg()
        level_map.update()                
        player.update()
        text_group.update(player.rect.x+50,player.rect.y-60)
        if pygame.sprite.spritecollide(player,level_map.enemies,False):
            player.sawkill(level_map)        
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        
    if (player_group):
        return True
    return False

####################
####    MENU THINGS
####################
class Button(object):
    def __init__(self, text, (x,y), xlen, ylen, fontsize):
        self.fontObj = pygame.font.Font('freesansbold.ttf', fontsize)
        self.text = self.fontObj.render(text, True, (255,255,255))
        self.rect = self.text.get_rect()
        self.rect.center = (x,y)
        self.xlen = xlen
        self.ylen = ylen
        self.color = (0,0,255)

class Menu(object):
    def __init__(self):
        global BASICFONT
        self.text = BASICFONT.render("press 's' to start", True, (255,255,255))
        
        self.image = pygame.image.load('img/menu_bg.png')
        self.img_cloud1 = pygame.image.load('img/menu_cloud1.png')
        self.img_cloud2 = pygame.image.load('img/menu_cloud2.png')
        self.img_cloud3 = pygame.image.load('img/menu_cloud3.png')

        self.image.set_colorkey((255,255,255))
        self.img_cloud1.set_colorkey((255,255,255))
        self.img_cloud2.set_colorkey((255,255,255))
        self.img_cloud3.set_colorkey((255,255,255))

        self.x = 800
        
        self.yes = 0

    def update(self):
        DISPLAYSURF.blit(self.image, (0,0))
        '''DISPLAYSURF.blit(self.img_cloud1, (800-self.x,0))
        DISPLAYSURF.blit(self.img_cloud1, (0-self.x,0))
        for i in range(3):
            DISPLAYSURF.blit(self.img_cloud2, (i*800-self.x*2,0))'''
        for i in range(6):
            DISPLAYSURF.blit(self.img_cloud3, (i*800-self.x*4,0))

        self.x -= 1
        if self.x < 0:
            self.x = 800

        if self.yes <= 10:
            DISPLAYSURF.blit(self.text, (300,350))
        elif self.yes > 20:
            self.yes = 0
        self.yes += 1


def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, SMALLFONT, GAMESTATE
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    BASICFONT = pygame.font.SysFont('monospace', 30)
    SMALLFONT = pygame.font.SysFont('monospace', 14)
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH,WINDOWHEIGHT))
    FPSCLOCK = pygame.time.Clock()
    menu = Menu()
    GAMESTATE = MENU
    currentlevel = 15
    pygame.mixer.music.load('sound/funkycruise.wav')
    pygame.mixer.music.play(-1)    
    while True:
        if GAMESTATE == MENU:
            #DISPLAYSURF.fill((0,25,100))
            menu.update()
            pygame.display.update()
            FPSCLOCK.tick(FPS)
            for event in pygame.event.get():
                if event.type == QUIT:
                    terminate()
                if pygame.key.get_pressed()[K_ESCAPE]:
                    terminate()
                if pygame.key.get_pressed()[K_s]:
                    GAMESTATE = PLAY
        if GAMESTATE == PLAY:
            fadeToBlack()
            if runLevel(currentlevel):
                currentlevel += 1
            if currentlevel>NUMBEROFLEVELS:
                fadeToBlack()
                currentlevel = 1

if __name__ == '__main__':
    main()
        
