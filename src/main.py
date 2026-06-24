import math
import sys
from pathlib import Path

import pygame

from game_core import MatchState, attempt_shot, create_initial_match, update_match


WIDTH, HEIGHT = 960, 640
FIELD_W, FIELD_H = 760, 520
FIELD_X, FIELD_Y = 100, 60
GOAL_W, GOAL_H = 24, 140
BALL_RADIUS = 8
PLAYER_RADIUS = 12


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Arena FC Prototype")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 20)
        self.big_font = pygame.font.SysFont("Segoe UI", 40, bold=True)
        self.small_font = pygame.font.SysFont("Segoe UI", 16)
        self.state = create_initial_match()
        self.menu = True
        self.paused = False
        self.controlled_player = 0
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.shake = 0.0
        self.match_started = False
        self.running = True
        self.message_timer = 0.0
        self.message = "Welcome to Arena FC"
        self.score_flash = 0.0
        self.reset_ball()

    def reset_ball(self) -> None:
        self.state.ball_x = WIDTH // 2
        self.state.ball_y = HEIGHT // 2
        self.state.ball_vx = 0.0
        self.state.ball_vy = 0.0

    def draw_background(self) -> None:
        gradient = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            color = (20 + int(ratio * 20), 70 + int(ratio * 30), 50 + int(ratio * 20))
            pygame.draw.line(gradient, color, (0, y), (WIDTH, y))
        self.screen.blit(gradient, (0, 0))

        pygame.draw.rect(self.screen, (12, 55, 24), (FIELD_X - 20, FIELD_Y - 20, FIELD_W + 40, FIELD_H + 40))
        pygame.draw.rect(self.screen, (0, 0, 0), (FIELD_X - 10, FIELD_Y - 10, FIELD_W + 20, FIELD_H + 20), 2)
        pygame.draw.rect(self.screen, (18, 120, 70), (FIELD_X, FIELD_Y, FIELD_W, FIELD_H))
        pygame.draw.rect(self.screen, (255, 255, 255), (FIELD_X, FIELD_Y, FIELD_W, FIELD_H), 2)
        for x in (FIELD_X + FIELD_W // 2 - 1,):
            pygame.draw.line(self.screen, (255, 255, 255), (x, FIELD_Y), (x, FIELD_Y + FIELD_H), 2)
        pygame.draw.rect(self.screen, (255, 255, 255), (FIELD_X + FIELD_W // 2 - 35, FIELD_Y + FIELD_H // 2 - 35, 70, 70), 2)
        pygame.draw.circle(self.screen, (255, 255, 255), (FIELD_X + FIELD_W // 2, FIELD_Y + FIELD_H // 2), 50, 2)
        pygame.draw.rect(self.screen, (220, 220, 220), (FIELD_X - 60, FIELD_Y + FIELD_H // 2 - 70, 40, 140))
        pygame.draw.rect(self.screen, (220, 220, 220), (FIELD_X + FIELD_W + 20, FIELD_Y + FIELD_H // 2 - 70, 40, 140))
        pygame.draw.rect(self.screen, (255, 255, 255), (FIELD_X - 1, FIELD_Y + FIELD_H // 2 - 70, 2, 140))
        pygame.draw.rect(self.screen, (255, 255, 255), (FIELD_X + FIELD_W + 1, FIELD_Y + FIELD_H // 2 - 70, 2, 140))
        pygame.draw.rect(self.screen, (255, 255, 255), (FIELD_X, FIELD_Y, GOAL_W, FIELD_H), 2)
        pygame.draw.rect(self.screen, (255, 255, 255), (FIELD_X + FIELD_W - GOAL_W, FIELD_Y, GOAL_W, FIELD_H), 2)

        for row in range(4):
            y = FIELD_Y + 40 + row * 120
            pygame.draw.line(self.screen, (255, 255, 255), (FIELD_X + 20, y), (FIELD_X + FIELD_W - 20, y), 1)

        for i in range(20):
            crowd_x = 60 + (i % 5) * 160
            crowd_y = 20 + (i // 5) * 80
            color = (30 + (i % 3) * 20, 20 + (i % 4) * 20, 30)
            pygame.draw.rect(self.screen, color, (crowd_x, crowd_y, 90, 20))
            pygame.draw.rect(self.screen, (255, 255, 255), (crowd_x, crowd_y, 90, 20), 1)

        for i in range(20):
            crowd_x = 760 + (i % 5) * 150
            crowd_y = 580 - (i // 5) * 80
            color = (40 + (i % 3) * 20, 25 + (i % 4) * 20, 30)
            pygame.draw.rect(self.screen, color, (crowd_x, crowd_y, 90, 20))
            pygame.draw.rect(self.screen, (255, 255, 255), (crowd_x, crowd_y, 90, 20), 1)

    def draw_hud(self) -> None:
        pygame.draw.rect(self.screen, (8, 14, 18), (0, 0, WIDTH, 48), border_radius=0)
        pygame.draw.rect(self.screen, (40, 50, 60), (0, 0, WIDTH, 48), 1)
        home = self.font.render("Home 0", True, (255, 255, 255))
        away = self.font.render("Away 0", True, (255, 255, 255))
        self.screen.blit(home, (80, 14))
        self.screen.blit(away, (WIDTH - 160, 14))
        clock_text = self.font.render(f"{self.state.match_time:02d}'", True, (255, 255, 255))
        self.screen.blit(clock_text, (WIDTH // 2 - 20, 14))
        possession_text = self.font.render(f"Possession: {'Home' if self.state.possession == 0 else 'Away'}", True, (255, 255, 255))
        self.screen.blit(possession_text, (WIDTH // 2 - 120, 40))
        if self.message_timer > 0:
            message = self.small_font.render(self.message, True, (255, 255, 255))
            self.screen.blit(message, (WIDTH // 2 - 100, 58))

        for idx, player in enumerate(self.state.players):
            if idx == self.controlled_player:
                pygame.draw.circle(self.screen, (255, 220, 80), (int(player.x), int(player.y)), PLAYER_RADIUS + 4, 2)

    def draw_players(self) -> None:
        for player in self.state.players:
            color = (255, 120, 80) if player.team == 0 else (70, 100, 240)
            pygame.draw.circle(self.screen, color, (int(player.x), int(player.y)), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(player.x), int(player.y)), PLAYER_RADIUS, 2)
            self.screen.blit(self.small_font.render(player.name.split()[1], True, (255, 255, 255)), (int(player.x) - 18, int(player.y) - 28))
        pygame.draw.circle(self.screen, (255, 255, 255), (int(self.state.ball_x), int(self.state.ball_y)), BALL_RADIUS)
        pygame.draw.circle(self.screen, (20, 20, 20), (int(self.state.ball_x), int(self.state.ball_y)), BALL_RADIUS, 2)

    def draw_menu(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        title = self.big_font.render("ARENA FC", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - 120, 140))
        subtitle = self.small_font.render("Immersive football prototype with polished presentation", True, (220, 220, 220))
        self.screen.blit(subtitle, (WIDTH // 2 - 180, 205))

        buttons = [
            ("Start Match", 320),
            ("Controls", 380),
            ("Quit", 440),
        ]
        for label, y in buttons:
            rect = pygame.Rect(WIDTH // 2 - 90, y, 180, 44)
            pygame.draw.rect(self.screen, (30, 100, 60), rect)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
            text = self.font.render(label, True, (255, 255, 255))
            self.screen.blit(text, (WIDTH // 2 - 40, y + 10))

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.menu:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if WIDTH // 2 - 90 <= x <= WIDTH // 2 + 90:
                        if 320 <= y <= 364:
                            self.menu = False
                            self.match_started = True
                            self.message = "Match started"
                            self.message_timer = 2.0
                        elif 380 <= y <= 424:
                            self.message = "Move with WASD or arrows, press Space to shoot"
                            self.message_timer = 2.5
                        elif 440 <= y <= 484:
                            self.running = False
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.menu = True
                    elif event.key == pygame.K_SPACE:
                        if attempt_shot(self.state, 0):
                            self.message = "Goal!"
                            self.message_timer = 2.0
                            self.score_flash = 1.0
                            self.reset_ball()
                        else:
                            self.message = "Shot away"
                            self.message_timer = 1.0
                            self.reset_ball()

    def handle_player_movement(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        player = self.state.players[self.controlled_player]
        speed = player.speed * dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.x += speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player.y -= speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player.y += speed
        player.x = max(FIELD_X + 25, min(FIELD_X + FIELD_W - 25, player.x))
        player.y = max(FIELD_Y + 25, min(FIELD_Y + FIELD_H - 25, player.y))

    def update(self, dt: float) -> None:
        if self.menu:
            return
        self.state.ball_x = max(FIELD_X + 10, min(FIELD_X + FIELD_W - 10, self.state.ball_x))
        self.state.ball_y = max(FIELD_Y + 10, min(FIELD_Y + FIELD_H - 10, self.state.ball_y))
        self.handle_player_movement(dt)
        update_match(self.state, dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        self.score_flash = max(0.0, self.score_flash - dt)
        for player in self.state.players:
            if player.team == 0 and self.state.possession == 0:
                player.x = min(player.x + 20 * dt, self.state.ball_x)
                player.y = min(player.y + 20 * dt, self.state.ball_y)
            if player.team == 1 and self.state.possession == 1:
                player.x = min(player.x + 20 * dt, self.state.ball_x)
                player.y = min(player.y + 20 * dt, self.state.ball_y)
        self.camera_x = self.state.ball_x - WIDTH // 2
        self.camera_y = self.state.ball_y - HEIGHT // 2
        self.shake = max(0.0, self.shake - dt)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.screen.fill((0, 0, 0))
            self.draw_background()
            self.draw_players()
            self.draw_hud()
            if self.menu:
                self.draw_menu()
            if self.score_flash > 0:
                flash = self.big_font.render("GOAL!", True, (255, 240, 100))
                self.screen.blit(flash, (WIDTH // 2 - 60, 100))
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Game().run()
