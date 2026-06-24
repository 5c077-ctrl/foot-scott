import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game_core import attempt_shot, create_initial_match, update_match


def test_initial_match_sets_scores_and_players():
    state = create_initial_match()
    assert state.home_score == 0
    assert state.away_score == 0
    assert len(state.players) == 10
    assert state.players[0].team == 0


def test_attempt_shot_scores_when_in_opposition_box():
    state = create_initial_match()
    state.possession = 0
    state.ball_x = 650
    state.ball_y = 300
    assert attempt_shot(state, 0) is True
    assert state.home_score == 1


def test_update_match_counts_down_time():
    state = create_initial_match()
    update_match(state, 5.0)
    assert state.match_time == 85
