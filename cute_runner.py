"""
Cute Garden Runner  -  an endless runner made with pygame
Run:   pip install pygame
       python cute_runner.py
Controls: SPACE / UP = jump (hold for a higher jump)   ESC = quit
"""
import math
import random
import array
import sys
import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
try:
    pygame.mixer.init(44100, -16, 1, 512)
    AUDIO = pygame.mixer.get_init() is not None
except Exception:
    AUDIO = False


class SilentSound:
    def play(self, *a, **k): pass
    def set_volume(self, *a, **k): pass

W, H = 900, 450
GROUND = 370
SR = 44100
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cute Garden Runner")
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("comicsansms", 54, bold=True)
font = pygame.font.SysFont("comicsansms", 26, bold=True)
font_small = pygame.font.SysFont("comicsansms", 20)

# ---------- colors ----------
SKY_TOP = (150, 215, 255)
SKY_BOT = (255, 238, 225)
GRASS = (120, 210, 120)
GRASS_DARK = (90, 185, 100)
DIRT = (190, 145, 105)
SKIN = (255, 224, 196)
HAIR = (120, 75, 55)
DRESS = (130, 190, 255)
SHOE = (255, 130, 150)
WHITE = (255, 255, 255)
PINK = (255, 150, 185)
YELLOW = (255, 220, 90)
RED = (240, 90, 100)
GREEN = (80, 170, 90)


# ---------- cute sounds (made from sine waves) ----------
def make_sound(parts, vol=0.45):
    """parts = list of (start_freq, end_freq, seconds, wobble). freq 0 = rest."""
    if not AUDIO:
        return SilentSound()
    buf = array.array("h")
    phase = 0.0
    for f0, f1, dur, vib in parts:
        n = int(SR * dur)
        for i in range(n):
            if f0 == 0:
                buf.append(0)
                continue
            p = i / n
            f = f0 + (f1 - f0) * p
            f *= 1 + vib * 0.04 * math.sin(2 * math.pi * 9 * i / SR)
            phase += 2 * math.pi * f / SR
            env = min(1.0, i / 300) * min(1.0, (n - i) / 1500)
            v = (math.sin(phase) + 0.3 * math.sin(2 * phase)) * env * vol
            buf.append(int(v * 32767 * 0.7))
    try:
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return SilentSound()


snd_jump = make_sound([(520, 950, 0.13, 1)])                       # "hup!"
snd_collect = make_sound([(988, 988, 0.07, 0), (1319, 1319, 0.14, 0)])  # "ding-ding"
snd_hit = make_sound([(480, 160, 0.5, 4)])                          # "oopsie..."
snd_yay = make_sound([(660, 660, 0.08, 1), (880, 880, 0.08, 1), (1100, 1100, 0.16, 2)])

# gentle music box loop (C major pentatonic)
N = {"C": 523, "D": 587, "E": 659, "G": 784, "A": 880, "_": 0}
tune = "E G A G E D C _ D E G E D C D _ E G A C A G E G A G E D C _ _".split()
music = make_sound([(N[n], N[n], 0.22, 0) for n in tune], vol=0.25)
music.set_volume(0.35)
music.play(loops=-1)


# ---------- drawing helpers ----------
def sky():
    for y in range(0, GROUND, 6):
        t = y / GROUND
        c = tuple(int(SKY_TOP[i] + (SKY_BOT[i] - SKY_TOP[i]) * t) for i in range(3))
        pygame.draw.rect(screen, c, (0, y, W, 6))


def cloud(x, y, s=1.0):
    for dx, dy, r in [(0, 0, 26), (28, -10, 32), (60, 0, 26), (30, 8, 26)]:
        pygame.draw.circle(screen, WHITE, (int(x + dx * s), int(y + dy * s)), int(r * s))


def flower(x, y, r=6, color=PINK):
    for k in range(5):
        a = k * 2 * math.pi / 5
        pygame.draw.circle(screen, color, (int(x + math.cos(a) * r), int(y + math.sin(a) * r)), int(r * 0.9))
    pygame.draw.circle(screen, YELLOW, (int(x), int(y)), max(2, int(r * 0.7)))


def heart(x, y, size=12, color=RED):
    pygame.draw.circle(screen, color, (int(x - size * 0.5), int(y - size * 0.3)), int(size * 0.6))
    pygame.draw.circle(screen, color, (int(x + size * 0.5), int(y - size * 0.3)), int(size * 0.6))
    pygame.draw.polygon(screen, color, [(x - size * 1.05, y - size * 0.1), (x + size * 1.05, y - size * 0.1), (x, y + size * 1.1)])


def draw_hero(x, y, t, in_air, blink, happy=False):
    """x = center, y = feet on the ground."""
    swing = 0 if in_air else math.sin(t * 0.35)
    bob = 0 if in_air else abs(math.sin(t * 0.35)) * 4
    y = int(y - bob)
    x = int(x)

    # back arm
    pygame.draw.line(screen, SKIN, (x - 8, y - 44), (x - 18, int(y - 36 - swing * 6)), 5)

    # legs + shoes
    for sgn in (-1, 1):
        if in_air:
            lx, lift = x + sgn * 10, (8 if sgn > 0 else 0)
        else:
            lx, lift = int(x + sgn * swing * 12), int(max(0, -sgn * swing) * 8)
        pygame.draw.line(screen, SKIN, (x + sgn * 6, y - 24), (lx, y - 8 - lift), 6)
        pygame.draw.ellipse(screen, SHOE, (lx - 7, y - 12 - lift, 18, 11))

    # dress with polka dots
    pygame.draw.polygon(screen, DRESS, [(x - 12, y - 50), (x + 12, y - 50), (x + 21, y - 20), (x - 21, y - 20)])
    for dx, dy in [(-8, -28), (6, -32), (0, -42), (12, -24), (-14, -22)]:
        pygame.draw.circle(screen, WHITE, (x + dx, y + dy), 3)
    pygame.draw.rect(screen, PINK, (x - 12, y - 52, 24, 5), border_radius=3)  # belt

    # head
    cx, cy = x + 2, y - 74
    # bunny-ear hat
    for ex in (-12, 8):
        pygame.draw.ellipse(screen, (255, 250, 240), (cx + ex, cy - 58, 14, 36))
        pygame.draw.ellipse(screen, PINK, (cx + ex + 3, cy - 52, 8, 24))
    pygame.draw.circle(screen, HAIR, (cx - 3, cy - 2), 26)      # hair
    pygame.draw.circle(screen, SKIN, (cx, cy), 23)               # face
    pygame.draw.ellipse(screen, (255, 250, 240), (cx - 25, cy - 30, 50, 22))  # hat band
    pygame.draw.circle(screen, PINK, (cx + 14, cy - 22), 4)      # tiny bow
    pygame.draw.circle(screen, PINK, (cx + 20, cy - 22), 4)
    # eyes
    for ex in (cx + 3, cx + 15):
        if blink:
            pygame.draw.line(screen, (60, 40, 40), (ex - 4, cy), (ex + 4, cy), 2)
        else:
            pygame.draw.ellipse(screen, (50, 35, 45), (ex - 4, cy - 7, 8, 13))
            pygame.draw.circle(screen, WHITE, (ex - 1, cy - 4), 2)
    # blush + smile
    pygame.draw.circle(screen, (255, 170, 190), (cx - 1, cy + 8), 5)
    pygame.draw.circle(screen, (255, 170, 190), (cx + 20, cy + 8), 5)
    if happy:
        pygame.draw.ellipse(screen, (200, 70, 90), (cx + 6, cy + 5, 10, 9))
    else:
        pygame.draw.arc(screen, (200, 70, 90), (cx + 5, cy + 2, 11, 9), math.pi, 2 * math.pi, 2)

    # front arm holding a flower
    hx, hy = x + 26, int(y - 40 + swing * 3)
    pygame.draw.line(screen, SKIN, (x + 8, y - 46), (hx, hy), 5)
    pygame.draw.line(screen, GREEN, (hx, hy), (hx + 2, hy - 26), 3)
    pygame.draw.ellipse(screen, GREEN, (hx + 2, hy - 18, 12, 6))
    flower(hx + 2, hy - 30, 6, (255, 120, 170))
    pygame.draw.circle(screen, SKIN, (hx, hy), 4)


# ---------- world pieces ----------
def draw_bush(x, w, h):
    base = GROUND
    for k in range(3):
        pygame.draw.circle(screen, GREEN, (int(x + w * (0.2 + 0.3 * k)), base - h // 2), h // 2 + 4)
    pygame.draw.rect(screen, GREEN, (x + 6, base - h // 2, w - 12, h // 2))
    for k in range(3):
        flower(x + w * (0.2 + 0.3 * k), base - h * 0.7, 4, (255, 255, 255))


def draw_snail(x, w, h):
    pygame.draw.ellipse(screen, (255, 210, 170), (x, GROUND - 16, w, 16))
    pygame.draw.circle(screen, (255, 170, 120), (int(x + w * 0.4), GROUND - h // 2 - 4), h // 2)
    pygame.draw.circle(screen, (255, 210, 170), (int(x + w * 0.4), GROUND - h // 2 - 4), h // 4, 2)
    pygame.draw.line(screen, (255, 210, 170), (x + w - 4, GROUND - 14), (x + w + 2, GROUND - 28), 2)
    pygame.draw.circle(screen, (50, 35, 45), (x + w + 2, GROUND - 29), 3)


def draw_mushroom(x, w, h):
    pygame.draw.rect(screen, (255, 245, 230), (x + w * 0.3, GROUND - h * 0.5, w * 0.4, h * 0.5), border_radius=6)
    pygame.draw.ellipse(screen, RED, (x, GROUND - h, w, h * 0.7))
    for dx, dy in [(0.25, 0.3), (0.55, 0.2), (0.7, 0.45)]:
        pygame.draw.circle(screen, WHITE, (int(x + w * dx), int(GROUND - h + h * dy)), 4)


def make_obstacle(x):
    kind = random.choice(["bush", "snail", "mushroom"])
    if kind == "bush":
        w, h = random.randint(60, 85), random.randint(40, 55)
    elif kind == "snail":
        w, h = 52, 40
    else:
        w, h = 46, 50
    return {"kind": kind, "x": x, "w": w, "h": h}


def draw_obstacle(o):
    {"bush": draw_bush, "snail": draw_snail, "mushroom": draw_mushroom}[o["kind"]](o["x"], o["w"], o["h"])


# ---------- game ----------
class Game:
    def __init__(self, best=0):
        self.best = best
        self.reset()

    def reset(self):
        self.px, self.py, self.vy = 160, GROUND, 0.0
        self.on_ground = True
        self.speed = 6.0
        self.t = 0
        self.score = 0.0
        self.hearts = 0
        self.obstacles = []
        self.collect = []
        self.sparkles = []
        self.next_obstacle = 60
        self.next_heart = 40
        self.alive = True
        self.cloud_x = [100, 380, 650, 850]
        self.hill_off = 0.0
        self.deco = [(random.randint(0, W), random.randint(GROUND + 12, H - 12),
                      random.choice([(255, 130, 170), (255, 255, 255), (255, 220, 90), (190, 150, 255)]))
                     for _ in range(30)]
        self.fence_off = 0.0

    def jump(self):
        if self.on_ground and self.alive:
            self.vy = -16.5
            self.on_ground = False
            snd_jump.play()

    def update(self, jump_held):
        self.t += 1
        if not self.alive:
            return
        self.speed = min(14, 6 + self.score / 900)
        self.score += self.speed * 0.1

        # physics (hold the button = higher jump)
        self.vy += 0.85
        if not jump_held and self.vy < -6:
            self.vy = -6
        self.py += self.vy
        if self.py >= GROUND:
            self.py, self.vy, self.on_ground = GROUND, 0, True

        # spawn obstacles
        self.next_obstacle -= 1
        if self.next_obstacle <= 0:
            self.obstacles.append(make_obstacle(W + 40))
            self.next_obstacle = int(random.randint(55, 100) * 6 / self.speed) + 25
        # spawn hearts
        self.next_heart -= 1
        if self.next_heart <= 0:
            self.collect.append({"x": W + 30, "y": random.choice([GROUND - 45, GROUND - 110, GROUND - 160]), "p": random.random() * 6})
            self.next_heart = random.randint(40, 90)

        # move things
        for o in self.obstacles:
            o["x"] -= self.speed
        for c in self.collect:
            c["x"] -= self.speed
        self.obstacles = [o for o in self.obstacles if o["x"] > -120]
        self.collect = [c for c in self.collect if c["x"] > -40]
        self.hill_off += self.speed * 0.25
        self.fence_off = (self.fence_off + self.speed * 0.6) % 60
        self.cloud_x = [(c - self.speed * 0.15) if c > -120 else W + 60 for c in self.cloud_x]
        self.deco = [((x - self.speed) if x > -10 else W + 10, y, c) for x, y, c in self.deco]

        # collisions
        me = pygame.Rect(self.px - 14, self.py - 85, 28, 83)
        for o in self.obstacles:
            r = pygame.Rect(o["x"] + 6, GROUND - o["h"] + 6, o["w"] - 12, o["h"] - 6)
            if me.colliderect(r):
                self.alive = False
                self.best = max(self.best, int(self.score) + self.hearts * 10)
                snd_hit.play()
                return
        for c in self.collect[:]:
            if me.inflate(20, 20).collidepoint(c["x"], c["y"]):
                self.collect.remove(c)
                self.hearts += 1
                snd_collect.play()
                if self.hearts % 10 == 0:
                    snd_yay.play()
                for _ in range(8):
                    a = random.random() * 6.28
                    self.sparkles.append([c["x"], c["y"], math.cos(a) * 3, math.sin(a) * 3, 25])

        for s in self.sparkles:
            s[0] += s[2]; s[1] += s[3]; s[4] -= 1
        self.sparkles = [s for s in self.sparkles if s[4] > 0]

    def draw(self):
        sky()
        for cx, cy, s in zip(self.cloud_x, [70, 120, 60, 100], [1.0, 0.8, 1.2, 0.9]):
            cloud(cx, cy, s)
        # soft hills
        for layer, (col, amp, base, k) in enumerate([((185, 235, 190), 30, 300, 0.012), ((150, 220, 160), 24, 330, 0.02)]):
            pts = [(0, GROUND)]
            for x in range(0, W + 20, 20):
                pts.append((x, base + math.sin((x + self.hill_off * (layer + 1)) * k) * amp))
            pts.append((W, GROUND))
            pygame.draw.polygon(screen, col, pts)
        # white picket fence
        for x in range(-60, W + 60, 60):
            fx = x - self.fence_off
            pygame.draw.rect(screen, WHITE, (fx, GROUND - 62, 14, 62), border_radius=6)
            pygame.draw.rect(screen, (255, 240, 245), (fx - 4, GROUND - 48, 62, 7))
        # ground
        pygame.draw.rect(screen, GRASS, (0, GROUND, W, H - GROUND))
        pygame.draw.rect(screen, GRASS_DARK, (0, GROUND, W, 8))
        for x, y, c in self.deco:
            flower(x, y, 4, c)

        for o in self.obstacles:
            draw_obstacle(o)
        for c in self.collect:
            heart(c["x"], c["y"] + math.sin((self.t + c["p"] * 10) * 0.1) * 5, 11, (255, 100, 140))
        for x, y, _, _, life in self.sparkles:
            pygame.draw.circle(screen, YELLOW, (int(x), int(y)), max(1, life // 8))

        blink = (self.t % 150) < 6
        if self.alive:
            draw_hero(self.px, self.py, self.t, not self.on_ground, blink, happy=not self.on_ground)
        else:
            draw_hero(self.px, self.py, 0, False, True)
            txt = font.render("Oopsie!", True, (200, 70, 90))
            screen.blit(txt, (self.px - 40, self.py - 150))

        # HUD
        heart(30, 28, 10, (255, 100, 140))
        screen.blit(font.render(f"x {self.hearts}", True, (120, 70, 100)), (48, 10))
        sc = font.render(f"Distance: {int(self.score)} m", True, (120, 70, 100))
        screen.blit(sc, (W - sc.get_width() - 20, 10))
        bs = font_small.render(f"Best: {self.best}", True, (120, 70, 100))
        screen.blit(bs, (W - bs.get_width() - 20, 44))


def center_text(text, f, y, color=(150, 70, 110)):
    img = f.render(text, True, color)
    screen.blit(img, (W // 2 - img.get_width() // 2, y))


def main():
    game = Game()
    started = False
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_UP):
                if not started:
                    started = True
                elif game.alive:
                    game.jump()
                else:
                    game = Game(game.best)
            if e.type == pygame.MOUSEBUTTONDOWN:
                if not started:
                    started = True
                elif game.alive:
                    game.jump()
                else:
                    game = Game(game.best)

        keys = pygame.key.get_pressed()
        held = keys[pygame.K_SPACE] or keys[pygame.K_UP] or pygame.mouse.get_pressed()[0]
        if started:
            game.update(held)
        else:
            game.t += 1
        game.draw()

        if not started:
            center_text("Cute Garden Runner", font_big, 70)
            center_text("Press SPACE to run!", font, 150)
        elif not game.alive:
            center_text("Press SPACE to try again", font, 150)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
