"""
fx.py
-----
เอฟเฟกต์ภาพที่ทำให้เกมดูทันสมัยและมีชีวิตชีวาขึ้น โดยไม่ต้องพึ่งภาพภายนอกเลย:
- พื้นหลังไล่เฉดสี + วง "แสงนุ่ม" ลอยช้า ๆ (ambient blobs) แบบแอปยุคใหม่
- การ์ดพาเนลพร้อมเงานุ่ม (soft drop shadow)
- คอนเฟตตี้ระเบิดและข้อความ "+XP" ลอยขึ้นตอนตอบถูก
"""

import math
import random

import pygame

from . import config


def draw_gradient_background(surface: pygame.Surface, top_color=None, bottom_color=None):
    # ถ้าส่งสีมา (หน้า lesson/summary ส่งสีพาสเทลของบทเรียนมา) จะใช้สีนั้น
    # ถ้าไม่ส่ง (หน้าอื่น ๆ) จะใช้พื้นหลังเขียวมาตรฐานของเกม
    top_color = top_color or config.COLOR_BG_TOP
    bottom_color = bottom_color or config.COLOR_BG_BOTTOM
    h = surface.get_height()
    w = surface.get_width()
    step = 4  # วาดเป็นแถบ ๆ แทนทีละเส้น ให้เร็วขึ้นโดยที่ยังดูเนียนตา
    for y in range(0, h, step):
        t = y / max(1, h - 1)
        color = config.lerp_color(top_color, bottom_color, t)
        pygame.draw.rect(surface, color, (0, y, w, step))


def draw_ambient_blobs(surface: pygame.Surface, t: float, tint=None):
    """วงแสงสีนุ่ม ๆ ลอยช้า ๆ อยู่หลังฉาก ให้ความรู้สึกเป็นแอปยุคใหม่ (ไม่ใช่แค่พื้นเรียบทึบ)"""
    w, h = surface.get_width(), surface.get_height()
    blobs = [  # วงแสงสีขาว/เขียวอ่อน บนพื้นเขียว
        (config.COLOR_WHITE, 0.16, 200, 0.16, 0.20, 0.30),
        (config.COLOR_WHITE, 0.12, 230, 0.82, 0.28, 0.24),
        (tint or (190, 245, 130), 0.18, 150, 0.5, 0.88, 0.40),
    ]
    for color, alpha, radius, bx, by, speed in blobs:
        ox = math.sin(t * speed + bx * 6) * 26
        oy = math.cos(t * speed * 0.8 + by * 6) * 18
        cx, cy = int(w * bx + ox), int(h * by + oy)
        blob_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(blob_surf, (*color, int(255 * alpha)), (radius, radius), radius)
        surface.blit(blob_surf, (cx - radius, cy - radius))


def draw_soft_shadow(surface: pygame.Surface, rect: pygame.Rect, radius: int = 18, offset: int = 6, alpha: int = 90):
    """เงานุ่ม ๆ ลอยใต้ปุ่ม/การ์ด ให้ความรู้สึกกดได้แบบ UI สมัยใหม่ (แยกจาก draw_card เพื่อใช้กับปุ่มโดยเฉพาะ)"""
    shadow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, alpha), (10, 10 + offset, rect.width, rect.height), border_radius=radius)
    surface.blit(shadow, (rect.x - 10, rect.y - 10))


def draw_card(surface: pygame.Surface, rect: pygame.Rect, radius: int = 18, color=None, shadow: bool = True):
    """การ์ดพาเนลพื้นหลังโค้งมนพร้อมเงานุ่ม ๆ ใช้ครอบกลุ่มข้อมูลให้ดูเป็นระเบียบแบบ UI สมัยใหม่"""
    color = color or config.COLOR_BG_LIGHT
    if shadow:
        pad = 14
        shadow_surf = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80), (pad, pad + 4, rect.width, rect.height), border_radius=radius)
        surface.blit(shadow_surf, (rect.x - pad, rect.y - pad))
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    pygame.draw.rect(surface, (255, 255, 255, 30), rect, width=1, border_radius=radius)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "rotation", "spin")

    def __init__(self, x, y, vx, vy, life, color, size):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.rotation = random.uniform(0, 360)
        self.spin = random.uniform(-260, 260)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 320 * dt  # แรงโน้มถ่วงเบา ๆ ให้คอนเฟตตี้ตกลงมา
        self.rotation += self.spin * dt
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        ratio = max(0.0, self.life / self.max_life)
        alpha = int(255 * ratio)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, self.size * 1.6, self.size)
        rect.center = (self.size, self.size)
        shape = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.rect(shape, (*self.color, alpha), rect, border_radius=2)
        rotated = pygame.transform.rotate(shape, self.rotation) if hasattr(pygame, "transform") else shape
        surface.blit(rotated, rotated.get_rect(center=(self.x, self.y)))


class FloatingText:
    def __init__(self, text, pos, color, life=1.1):
        self.text = text
        self.x, self.y = pos
        self.color = color
        self.life = life
        self.max_life = life

    def update(self, dt):
        self.y -= 42 * dt
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        ratio = max(0.0, self.life / self.max_life)
        font = config.get_font(24, bold=True)
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(int(255 * min(1.0, ratio * 1.6)))
        scale = 1.0 + (1 - ratio) * 0.15
        if scale != 1.0 and hasattr(pygame, "transform"):
            w, h = surf.get_width(), surf.get_height()
            surf = pygame.transform.smoothscale(surf, (int(w * scale), int(h * scale)))
        surface.blit(surf, surf.get_rect(center=(self.x, self.y)))


_CONFETTI_COLORS = [config.COLOR_PRIMARY, config.COLOR_SECONDARY, config.COLOR_ACCENT, config.COLOR_SUCCESS]


class ParticleSystem:
    """ระบบคอนเฟตตี้ + ข้อความลอย ใช้ร่วมกันได้ทุกหน้าจอที่ต้องการเอฟเฟกต์ฉลอง"""

    def __init__(self):
        self.particles = []
        self.texts = []

    def spawn_confetti(self, pos, count: int = 28):
        x, y = pos
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(90, 280)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 140
            color = random.choice(_CONFETTI_COLORS)
            size = random.randint(3, 6)
            life = random.uniform(0.6, 1.15)
            self.particles.append(Particle(x, y, vx, vy, life, color, size))

    def spawn_floating_text(self, text, pos, color=None):
        color = color or config.COLOR_SECONDARY
        self.texts.append(FloatingText(text, pos, color))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.alive]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
        for t in self.texts:
            t.draw(surface)
