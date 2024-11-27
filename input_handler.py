# input_handler.py
import pygame
import keyboard
import time


class InputHandler:
    def __init__(self, map_viewer):
        self.map_viewer = map_viewer
        self.joysticks = {}
        self.last_joystick_update = time.time()
        self.update_joysticks()
        self.setup_global_hotkeys()

    def setup_global_hotkeys(self):
        """Setup global hotkeys using the keyboard library"""
        keybinds = self.map_viewer.settings.settings["keybinds"]

        # Clear any existing hotkeys
        keyboard.unhook_all()

        # Register new hotkeys
        for action, bind in keybinds.items():
            if bind["type"] == "keyboard":
                key_name = self.pygame_to_keyboard_key(bind["value"])
                if key_name:
                    try:
                        keyboard.on_press_key(key_name,
                                              lambda e, a=action: self.map_viewer.handle_action(a),
                                              suppress=False)
                    except Exception as e:
                        print(f"Failed to bind key {key_name} for action {action}: {e}")

    def pygame_to_keyboard_key(self, pygame_key):
        """Convert pygame key code to keyboard library key name"""
        key_mapping = {
            pygame.K_LEFT: 'left',
            pygame.K_RIGHT: 'right',
            pygame.K_UP: 'up',
            pygame.K_DOWN: 'down',
            pygame.K_PLUS: '+',
            pygame.K_KP_PLUS: '+',
            pygame.K_MINUS: '-',
            pygame.K_KP_MINUS: '-',
            pygame.K_r: 'r',
            pygame.K_ESCAPE: 'esc'
        }
        return key_mapping.get(pygame_key)

    def update_joysticks(self):
        try:
            for i in range(pygame.joystick.get_count()):
                if i not in self.joysticks:
                    joy = pygame.joystick.Joystick(i)
                    joy.init()
                    self.joysticks[i] = {
                        "joystick": joy,
                        "num_buttons": joy.get_numbuttons()
                    }
        except:
            pass

    def handle_input(self):
        # Get all inputs at once
        keys = pygame.key.get_pressed()
        keybinds = self.map_viewer.settings.settings["keybinds"]

        # Handle keyboard inputs
        for action, bind in keybinds.items():
            if bind["type"] == "keyboard" and keys[bind["value"]]:
                self.map_viewer.handle_action(action)

        # Handle joystick inputs
        for action, bind in keybinds.items():
            if bind["type"] == "joystick":
                try:
                    joy = self.joysticks[bind["joy_id"]]["joystick"]
                    if joy.get_button(bind["value"]):
                        self.map_viewer.handle_action(action)
                except:
                    continue

        # Update joysticks periodically
        current_time = time.time()
        if current_time - self.last_joystick_update > 5:
            self.update_joysticks()
            self.last_joystick_update = current_time

    def cleanup(self):
        """Clean up keyboard bindings"""
        keyboard.unhook_all()

    def wait_for_keybind(self, key_to_bind):
        waiting = True
        font = pygame.font.Font(None, 36)
        prompt = font.render(f"Press key or button for {key_to_bind} (ESC to cancel)...", True, (255, 255, 255))
        prompt_rect = prompt.get_rect(center=(self.map_viewer.screen_width // 2, self.map_viewer.screen_height // 2))

        # Temporarily unhook all keys while binding
        keyboard.unhook_all()

        while waiting:
            self.map_viewer.screen.fill((0, 0, 0))
            self.map_viewer.screen.blit(prompt, prompt_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        waiting = False
                    else:
                        self.map_viewer.settings.settings["keybinds"][key_to_bind] = {
                            "type": "keyboard",
                            "value": event.key
                        }
                        self.map_viewer.settings.save_settings()
                        waiting = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.map_viewer.settings.settings["keybinds"][key_to_bind] = {
                        "type": "joystick",
                        "joy_id": event.joy,
                        "value": event.button
                    }
                    self.map_viewer.settings.save_settings()
                    waiting = False

        # Restore global hotkeys
        self.setup_global_hotkeys()