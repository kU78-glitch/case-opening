import os
import pygame

class SoundManager:
    def __init__(self):
        self.enabled = False
        self.tick_sound = None
        self.win_sound = None
        self.gold_sound = None

        try:
            pygame.mixer.init()
            self.enabled = True
            base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sounds")

            tick_path = os.path.join(base_path, "tick.wav")
            win_path = os.path.join(base_path, "win.wav")
            gold_path = os.path.join(base_path, "gold.wav")

            if os.path.exists(tick_path):
                self.tick_sound = pygame.mixer.Sound(tick_path)
                self.tick_sound.set_volume(0.3)
            if os.path.exists(win_path):
                self.win_sound = pygame.mixer.Sound(win_path)
                self.win_sound.set_volume(0.5)
            if os.path.exists(gold_path):
                self.gold_sound = pygame.mixer.Sound(gold_path)
                self.gold_sound.set_volume(0.6)
        except Exception as e:
            print(f"Warning: Audio could not be initialized: {e}")
            self.enabled = False

    def play_tick(self):
        if self.enabled and self.tick_sound:
            try:
                self.tick_sound.play()
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

