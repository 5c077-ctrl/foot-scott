from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Player:
    name: str
    team: int
    x: float
    y: float
    speed: float
    stamina: float
    is_ai: bool = False
    role: str = "midfielder"


@dataclass
class MatchState:
    home_score: int = 0
    away_score: int = 0
    possession: int = 0
    match_time: int = 90
    ball_x: float = 0.0
    ball_y: float = 0.0
    ball_vx: float = 0.0
    ball_vy: float = 0.0
    players: List[Player] = field(default_factory=list)
    last_event: str = "Kickoff"


def create_initial_match() -> MatchState:
    players: List[Player] = []
    for team, base_y in [(0, 180), (1, 420)]:
        for idx in range(5):
            x = 120 + idx * 80
            y = base_y + (20 if idx % 2 else -20)
            players.append(
                Player(
                    name=f"{('Home' if team == 0 else 'Away')} {idx + 1}",
                    team=team,
                    x=float(x),
                    y=float(y),
                    speed=140.0 + (idx % 3) * 10,
                    stamina=100.0,
                    is_ai=team == 1,
                    role="striker" if idx == 2 else "midfielder",
                )
            )
    state = MatchState(players=players)
    state.ball_x = 320.0
    state.ball_y = 300.0
    state.possession = 0
    return state


def attempt_shot(state: MatchState, team: int) -> bool:
    if state.possession != team:
        return False
    if team == 0 and state.ball_x > 600:
        state.home_score += 1
        state.last_event = "Goal for Home"
        return True
    if team == 1 and state.ball_x < 40:
        state.away_score += 1
        state.last_event = "Goal for Away"
        return True
    state.last_event = "Shot saved"
    return False


def update_match(state: MatchState, dt: float) -> None:
    state.match_time = max(0, state.match_time - int(dt))
    if state.match_time == 0:
        state.last_event = "Full time"
    if state.ball_vx or state.ball_vy:
        state.ball_x += state.ball_vx * dt
        state.ball_y += state.ball_vy * dt
        state.ball_vx *= 0.96
        state.ball_vy *= 0.96
    for player in state.players:
        if player.is_ai:
            if player.team == 1:
                player.x += 20 * dt
            else:
                player.x -= 15 * dt
        player.stamina = max(0.0, player.stamina - 0.15 * dt)
