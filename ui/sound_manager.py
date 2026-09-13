import os
import time
import pygame
from config import get_resource_path

class SoundManager:
    def __init__(self):
        self.enabled = False
        self.tick_sound = None
        self._last_respin_sound_time = 0.0

        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(8)
            self.enabled = True

            tick_path = get_resource_path(os.path.join("sounds", "tick.wav"))
            if not os.path.exists(tick_path):
                tick_path = get_resource_path(os.path.join("assets", "sounds", "tick.wav"))

            if os.path.exists(tick_path):
                self.tick_sound = pygame.mixer.Sound(tick_path)
                self.tick_sound.set_volume(0.35)
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
        """Disabled per user request - only tick sound is active."""
        pass

    def play_gold(self):
        """Disabled per user request - only tick sound is active."""
        pass

    def play_respin(self):
        """Play tick sound."""
        self.play_tick()

    def play_sell(self):
        """Play tick sound on sell."""
        self.play_tick()


