# settings.py
import json
import os
import pygame
import win32con

class Settings:
    def __init__(self):
        self.config_file = "map_viewer_config.json"
        self.default_settings = {
            "resolution": {"width": 1920, "height": 1080},
            "use_scroll_wheel": True,
            "keybinds": {
                "pan_left": {"type": "keyboard", "value": pygame.K_LEFT},
                "pan_right": {"type": "keyboard", "value": pygame.K_RIGHT},
                "pan_up": {"type": "keyboard", "value": pygame.K_UP},
                "pan_down": {"type": "keyboard", "value": pygame.K_DOWN},
                "zoom_in": {"type": "keyboard", "value": pygame.K_PLUS},
                "zoom_out": {"type": "keyboard", "value": pygame.K_MINUS},
                "reset_view": {"type": "keyboard", "value": pygame.K_r}
            }
        }
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return self.default_settings.copy()
        except:
            return self.default_settings.copy()

    def save_settings(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=4)