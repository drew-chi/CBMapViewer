import win32con
import win32gui
import win32api
import win32file
from ctypes import *
from ctypes.wintypes import *
import pygame
import time


class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", DWORD),
        ("scanCode", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", POINTER(ULONG))
    ]


class WindowsInputHandler:
    def __init__(self, map_viewer):
        self.map_viewer = map_viewer
        self.handlers = {}
        self.running = True
        self.hook = None
        self.pointer = None

        # Joystick handling
        self.joysticks = {}
        self.last_joystick_update = time.time()
        self.initial_button_states = {}
        self.update_joysticks()

    def update_joysticks(self):
        """Update the list of connected joysticks"""
        try:
            for i in range(pygame.joystick.get_count()):
                if i not in self.joysticks:
                    joy = pygame.joystick.Joystick(i)
                    joy.init()
                    self.joysticks[i] = {
                        "joystick": joy,
                        "num_buttons": joy.get_numbuttons()
                    }
        except Exception as e:
            print(f"Error updating joysticks: {e}")

    def get_initial_button_states(self):
        """Get the initial state of all joystick buttons"""
        self.initial_button_states.clear()
        for joy_id, joy_info in self.joysticks.items():
            joy = joy_info["joystick"]
            self.initial_button_states[joy_id] = {}
            for b in range(joy.get_numbuttons()):
                self.initial_button_states[joy_id][b] = joy.get_button(b)

    def register_key_handler(self, vk_code, callback):
        """Register a callback for a specific virtual key code"""
        self.handlers[vk_code] = callback

    def hook_proc(self, nCode, wParam, lParam):
        """Windows hook procedure for keyboard"""
        try:
            if nCode >= 0 and wParam == win32con.WM_KEYDOWN:
                kb = cast(lParam, POINTER(KBDLLHOOKSTRUCT)).contents
                vk_code = kb.vkCode
                if vk_code in self.handlers:
                    self.handlers[vk_code]()
        except Exception as e:
            print(f"Error in hook_proc: {e}")
        return windll.user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

    def start(self):
        """Start the keyboard hook"""
        CMPFUNC = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
        self.pointer = CMPFUNC(self.hook_proc)

        handle = win32api.GetModuleHandle(None)
        handle_ptr = c_void_p(handle)

        self.hook = windll.user32.SetWindowsHookExA(
            win32con.WH_KEYBOARD_LL,
            self.pointer,
            handle_ptr,
            0
        )

        if not self.hook:
            raise WinError()

    def handle_input(self):
        """Handle joystick and keyboard inputs"""
        current_time = time.time()
        if current_time - self.last_joystick_update > 5:
            self.update_joysticks()
            self.last_joystick_update = current_time

        # Direct keyboard state checking
        key_state = win32api.GetKeyState
        keybinds = self.map_viewer.settings.settings["keybinds"]

        for action, bind in keybinds.items():
            if bind["type"] == "keyboard":
                vk_code = self.map_viewer.pygame_to_vk(bind["value"])
                if vk_code and key_state(vk_code) < 0:  # Key is pressed
                    self.map_viewer.handle_action(action)
            elif bind["type"] == "joystick":
                try:
                    joy = self.joysticks[bind["joy_id"]]["joystick"]
                    if joy.get_button(bind["value"]):
                        self.map_viewer.handle_action(action)
                except Exception:
                    continue
    def wait_for_keybind(self, key_to_bind):
        """Wait for a key or button press to create a new keybinding"""
        # Temporarily stop the global hook
        self.stop()

        waiting = True
        font = pygame.font.Font(None, 36)
        prompt = font.render(f"Press key or button for {key_to_bind} (ESC to cancel)...", True, (255, 255, 255))
        prompt_rect = prompt.get_rect(center=(self.map_viewer.screen_width // 2, self.map_viewer.screen_height // 2))

        # Update joysticks and get initial states
        self.update_joysticks()

        # Display "Getting ready..." message
        ready_prompt = font.render("Getting ready...", True, (255, 255, 255))
        ready_rect = ready_prompt.get_rect(
            center=(self.map_viewer.screen_width // 2, self.map_viewer.screen_height // 2))
        self.map_viewer.screen.fill((0, 0, 0))
        self.map_viewer.screen.blit(ready_prompt, ready_rect)
        pygame.display.flip()

        # Wait a moment and get initial button states
        pygame.time.wait(500)
        self.get_initial_button_states()

        while waiting:
            self.map_viewer.screen.fill((0, 0, 0))
            self.map_viewer.screen.blit(prompt, prompt_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
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
                    # Check if this button was initially pressed
                    if not self.initial_button_states.get(event.joy, {}).get(event.button, False):
                        self.map_viewer.settings.settings["keybinds"][key_to_bind] = {
                            "type": "joystick",
                            "joy_id": event.joy,
                            "value": event.button
                        }
                        self.map_viewer.settings.save_settings()
                        waiting = False

        # Restart the global hook and reset the handlers
        self.start()
        self.map_viewer.setup_global_input_handlers()

    def stop(self):
        """Stop the keyboard hook and cleanup joysticks"""
        if self.hook:
            windll.user32.UnhookWindowsHookEx(self.hook)
            self.hook = None
            self.pointer = None

        # Cleanup joysticks
        for joy_id in self.joysticks:
            try:
                self.joysticks[joy_id]["joystick"].quit()
            except:
                pass
        self.joysticks.clear()
        self.initial_button_states.clear()