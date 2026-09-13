import os
import time
import pygame
from config import get_resource_path

class SoundManager:
    def __init__(self):
        self.enabled = False
        self.tick_sound = None
        self.win_sound = None
        self.gold_sound = None
        self.respin_channel = None
        self._last_respin_sound_time = 0.0

        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self.enabled = True

            tick_path = get_resource_path(os.path.join("sounds", "tick.wav"))
            win_path = get_resource_path(os.path.join("sounds", "win.wav"))
            gold_path = get_resource_path(os.path.join("sounds", "gold.wav"))

            if os.path.exists(tick_path):
                self.tick_sound = pygame.mixer.Sound(tick_path)
                self.tick_sound.set_volume(0.3)
            if os.path.exists(win_path):
                self.win_sound = pygame.mixer.Sound(win_path)
                self.win_sound.set_volume(0.5)
            if os.path.exists(gold_path):
                self.gold_sound = pygame.mixer.Sound(gold_path)
                self.gold_sound.set_volume(0.6)

            # Dedicated audio channel for bonus re-spin wheel ticks
            self.respin_channel = pygame.mixer.Channel(1)
        except Exception as e:
            print(f"Warning: Audio could not be initialized: {e}")
            self.enabled = False

    def play_tick(self):
        """Standard tick sound with a 35ms debounce threshold to prevent clipping."""
        if not self.enabled or not self.tick_sound:
            return

        now = time.monotonic()
        if (now - self._last_respin_sound_time) < 0.035:
            return

        try:
            self.tick_sound.play()
            self._last_respin_sound_time = now
        except Exception:
            pass

    def play_win(self):
        if self.enabled and self.win_sound:
            try:
                self.win_sound.play()
            except Exception:
                pass

    def play_gold(self):
        if self.enabled and self.gold_sound:
            try:
                self.gold_sound.play()
            except Exception:
                pass

    def play_respin(self):
        """Deprecated alias redirecting to consolidated play_tick."""
        self.play_tick()

    def play_sell(self):
        """Play sell confirmation sound."""
        if self.enabled and self.tick_sound:
            try:
                self.tick_sound.play()
            except Exception:
                pass


