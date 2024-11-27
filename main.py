import pygame
import requests
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import time
from settings import Settings
from ui_elements import Button, Dropdown
from input_handler import InputHandler
import keyboard

class MapViewer:
    def __init__(self):
        self.settings = Settings()
        pygame.init()
        pygame.font.init()
        pygame.joystick.init()

        # Initialize display
        self.screen_width = self.settings.settings["resolution"]["width"]
        self.screen_height = self.settings.settings["resolution"]["height"]
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Combat Box Map Viewer by JaggedFel")

        # Initialize input handler
        self.input_handler = InputHandler(self)

        # View parameters
        self.zoom = 1.0
        self.x_offset = 0
        self.y_offset = 0
        self.pan_speed = 20
        self.zoom_speed = 0.1
        self.min_zoom = 0.2
        self.max_zoom = 3.0

        # Mouse control variables
        self.dragging = False
        self.last_mouse_pos = None
        self.wheel_zoom_speed = 0.1

        # Map tracking
        self.current_map_url = None
        self.check_interval = 30
        self.last_check_time = 0

        # Resolution options
        self.resolution_options = [
            "1920x1080",
            "1600x900",
            "1366x768",
            "1280x720"
        ]

        # Initialize UI elements
        self.settings_button = Button(10, 40, 100, 30, "Settings")
        self.refresh_button = Button(120, 40, 100, 30, "Refresh")
        self.show_settings = False

        self.resolution_dropdown = Dropdown(
            self.screen_width // 2 - 100,
            200,
            200,
            30,
            self.resolution_options
        )

        # Set initial resolution dropdown selection
        current_res = f"{self.screen_width}x{self.screen_height}"
        try:
            self.resolution_dropdown.selected_index = self.resolution_options.index(current_res)
        except ValueError:
            self.resolution_dropdown.selected_index = 0

        # Create initial placeholder
        self.create_placeholder_surface()

    def handle_input(self):
        self.input_handler.handle_input()

    def cleanup(self):
        self.input_handler.cleanup()
        pygame.quit()

    def setup_global_hotkeys(self):
        """Setup global hotkeys using the keyboard library"""
        keybinds = self.settings.settings["keybinds"]

        # Clear any existing hotkeys
        keyboard.unhook_all()

        # Register new hotkeys
        for action, bind in keybinds.items():
            if bind["type"] == "keyboard":
                key_name = pygame.key.name(bind["value"])
                try:
                    keyboard.on_press_key(key_name,
                                          lambda e, a=action: self.handle_action(a),
                                          suppress=False)
                except Exception as e:
                    print(f"Failed to bind key {key_name} for action {action}: {e}")

    def setup_global_input_handlers(self):
        """Set up handlers for all bound keys"""
        keybinds = self.settings.settings["keybinds"]

        for action, bind in keybinds.items():
            if bind["type"] == "keyboard":
                # Convert pygame key to Windows virtual key code
                vk_code = self.pygame_to_vk(bind["value"])
                if vk_code:
                    self.global_input.register_key_handler(
                        vk_code,
                        lambda a=action: self.handle_action(a)
                    )

    def pygame_to_vk(self, pygame_key):
        """Convert pygame key code to Windows virtual key code"""
        # This is a basic mapping, extend as needed
        key_mapping = {
            pygame.K_LEFT: win32con.VK_LEFT,
            pygame.K_RIGHT: win32con.VK_RIGHT,
            pygame.K_UP: win32con.VK_UP,
            pygame.K_DOWN: win32con.VK_DOWN,
            pygame.K_PLUS: win32con.VK_ADD,
            pygame.K_MINUS: win32con.VK_SUBTRACT,
            pygame.K_r: ord('R'),
            # Add more mappings as needed
        }
        return key_mapping.get(pygame_key)

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
        except:
            pass  # Silently fail if there's an error updating joysticks

    def create_settings_buttons(self):
        buttons = []
        y_pos = 200

        # Resolution button
        current_res = f"{self.screen_width}x{self.screen_height}"
        buttons.append(Button(self.screen_width // 2 - 100, y_pos, 200, 30, f"Resolution: {current_res}"))

        # Keybind buttons
        y_pos += 50
        for key, value in self.settings.settings["keybinds"].items():
            buttons.append(Button(self.screen_width // 2 - 100, y_pos, 200, 30, f"{key}: {pygame.key.name(value)}"))
            y_pos += 40

        return buttons

    def draw_settings_menu(self):
        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))

        # Draw settings title
        font = pygame.font.Font(None, 48)
        title = font.render("Settings", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title, title_rect)

        # Draw close button
        close_button = Button(self.screen_width - 60, 10, 50, 30, "X")
        close_button.draw(self.screen)

        # Draw resolution dropdown
        font = pygame.font.Font(None, 24)
        text = font.render("Resolution:", True, (255, 255, 255))
        self.screen.blit(text, (self.screen_width // 2 - 200, 205))
        self.resolution_dropdown.draw(self.screen)

        # Draw keybind buttons
        y_pos = 300
        for key, bind in self.settings.settings["keybinds"].items():
            text = font.render(f"{key}:", True, (255, 255, 255))
            self.screen.blit(text, (self.screen_width // 2 - 200, y_pos + 5))

            if bind["type"] == "keyboard":
                value_text = pygame.key.name(bind["value"])
            else:  # joystick
                joy_id = bind.get("joy_id", 0)
                value_text = f"Joy {joy_id} Button {bind['value']}"

            button = Button(self.screen_width // 2, y_pos, 150, 30, value_text)
            button.draw(self.screen)
            y_pos += 40

        # Add scroll wheel toggle
        y_pos = 250
        font = pygame.font.Font(None, 24)
        text = font.render("Use Scroll Wheel:", True, (255, 255, 255))
        self.screen.blit(text, (self.screen_width // 2 - 200, y_pos + 5))

        toggle_text = "ON" if self.settings.settings["use_scroll_wheel"] else "OFF"
        toggle_button = Button(self.screen_width // 2, y_pos, 150, 30, toggle_text)
        toggle_button.draw(self.screen)

    def toggle_resolution(self):
        self.current_resolution_index = (self.current_resolution_index + 1) % len(self.resolution_options)
        width, height = map(int, self.resolution_options[self.current_resolution_index].split('x'))
        self.settings.settings["resolution"]["width"] = width
        self.settings.settings["resolution"]["height"] = height
        self.screen_width = width
        self.screen_height = height
        self.screen = pygame.display.set_mode((width, height))
        self.settings.save_settings()

    def handle_settings_input(self, event, mouse_pos):
        """Handle inputs while in the settings menu"""
        if self.resolution_dropdown.handle_event(event):
            width, height = map(int, self.resolution_options[self.resolution_dropdown.selected_index].split('x'))
            self.settings.settings["resolution"]["width"] = width
            self.settings.settings["resolution"]["height"] = height
            self.screen_width = width
            self.screen_height = height
            self.screen = pygame.display.set_mode((width, height))

            # Recreate the dropdown with new screen dimensions
            self.resolution_dropdown = Dropdown(
                self.screen_width // 2 - 100,
                200,
                200,
                30,
                self.resolution_options
            )
            current_res = f"{self.screen_width}x{self.screen_height}"
            try:
                self.resolution_dropdown.selected_index = self.resolution_options.index(current_res)
            except ValueError:
                self.resolution_dropdown.selected_index = 0

            self.settings.save_settings()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Handle close button
            close_button_rect = pygame.Rect(self.screen_width - 60, 10, 50, 30)
            if close_button_rect.collidepoint(mouse_pos):
                self.show_settings = False
                return True

            # Handle scroll wheel toggle
            toggle_button_rect = pygame.Rect(self.screen_width // 2, 250, 150, 30)
            if toggle_button_rect.collidepoint(mouse_pos):
                self.settings.settings["use_scroll_wheel"] = not self.settings.settings["use_scroll_wheel"]
                self.settings.save_settings()
                return True

            # Handle keybind buttons
            y_pos = 300
            for key in self.settings.settings["keybinds"].keys():
                button_rect = pygame.Rect(self.screen_width // 2, y_pos, 150, 30)
                if button_rect.collidepoint(mouse_pos):
                    self.input_handler.wait_for_keybind(key)
                    return True
                y_pos += 40

        return False

    def wait_for_keybind(self, key_to_bind):
        waiting = True
        font = pygame.font.Font(None, 36)
        prompt = font.render(f"Press key or button for {key_to_bind} (ESC to cancel)...", True, (255, 255, 255))
        prompt_rect = prompt.get_rect(center=(self.screen_width // 2, self.screen_height // 2))

        # Temporarily unhook all keys while binding
        keyboard.unhook_all()

        while waiting:
            self.screen.fill((0, 0, 0))
            self.screen.blit(prompt, prompt_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        waiting = False
                    else:
                        self.settings.settings["keybinds"][key_to_bind] = {
                            "type": "keyboard",
                            "value": event.key
                        }
                        self.settings.save_settings()
                        waiting = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.settings.settings["keybinds"][key_to_bind] = {
                        "type": "joystick",
                        "joy_id": event.joy,
                        "value": event.button
                    }
                    self.settings.save_settings()
                    waiting = False

        # Restore global hotkeys
        self.input_handler.setup_global_hotkeys()

    def refresh_map(self):
        self.check_for_new_map(force=True)
    def create_placeholder_surface(self):
        self.original_surface = pygame.Surface((800, 600))
        self.original_surface.fill((50, 50, 50))
        font = pygame.font.Font(None, 36)
        text = font.render("Checking for map...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(400, 300))
        self.original_surface.blit(text, text_rect)

    def get_current_map_url(self):
        try:
            response = requests.get("https://combatbox.net/en/")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            current_map_div = soup.find('div', class_='dominant_coal')
            if current_map_div:
                map_link = current_map_div.find('a', href=lambda x: x and 'missionmapimages' in x)
                if map_link:
                    return map_link['href']
            return None
        except Exception as e:
            print(f"Error fetching map URL: {e}")
            return None

    def load_new_map(self, map_url):
        try:
            response = requests.get(map_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            self.original_image = Image.open(image_data)
            self.original_surface = pygame.image.fromstring(
                self.original_image.tobytes(), self.original_image.size, self.original_image.mode)
            self.zoom = 1.0
            self.x_offset = 0
            self.y_offset = 0
            print(f"Successfully loaded new map")
        except Exception as e:
            print(f"Error loading map: {e}")
            self.create_placeholder_surface()

    def constrain_position(self):
        scaled_width = int(self.original_surface.get_width() * self.zoom)
        scaled_height = int(self.original_surface.get_height() * self.zoom)

        min_x_offset = -(scaled_width - self.screen_width) // 2
        max_x_offset = (scaled_width - self.screen_width) // 2
        min_y_offset = -(scaled_height - self.screen_height) // 2
        max_y_offset = (scaled_height - self.screen_height) // 2

        if scaled_width < self.screen_width:
            self.x_offset = 0
        else:
            self.x_offset = max(min_x_offset, min(self.x_offset, max_x_offset))

        if scaled_height < self.screen_height:
            self.y_offset = 0
        else:
            self.y_offset = max(min_y_offset, min(self.y_offset, max_y_offset))

    def handle_zoom(self, zoom_in):
        # Store old dimensions
        old_scaled_width = int(self.original_surface.get_width() * self.zoom)
        old_scaled_height = int(self.original_surface.get_height() * self.zoom)

        # Calculate map center relative to view
        map_center_x = old_scaled_width // 2
        map_center_y = old_scaled_height // 2

        # Apply zoom
        old_zoom = self.zoom
        if zoom_in:
            self.zoom = min(self.max_zoom, self.zoom + self.wheel_zoom_speed)
        else:
            self.zoom = max(self.min_zoom, self.zoom - self.wheel_zoom_speed)

        # Calculate new dimensions
        new_scaled_width = int(self.original_surface.get_width() * self.zoom)
        new_scaled_height = int(self.original_surface.get_height() * self.zoom)

        # Adjust offset to maintain center point
        scale_factor = self.zoom / old_zoom
        self.x_offset = int(self.x_offset * scale_factor)
        self.y_offset = int(self.y_offset * scale_factor)

        self.constrain_position()

    def handle_mouse_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                self.dragging = True
                self.last_mouse_pos = event.pos
            elif event.button == 4:  # Mouse wheel up
                self.handle_zoom(True)
            elif event.button == 5:  # Mouse wheel down
                self.handle_zoom(False)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and self.last_mouse_pos:
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.x_offset += dx
                self.y_offset += dy
                self.last_mouse_pos = event.pos
                self.constrain_position()

    def check_for_new_map(self, force=False):
        current_time = time.time()
        if force or current_time - self.last_check_time >= self.check_interval:
            self.last_check_time = current_time
            new_map_url = self.get_current_map_url()

            if new_map_url and (force or new_map_url != self.current_map_url):
                print(f"Loading new map: {new_map_url}")
                self.load_new_map(new_map_url)
                self.current_map_url = new_map_url

    def handle_action(self, action):
        """Handle various actions based on input"""
        if not self.show_settings:  # Only handle actions when not in settings
            if action == "pan_left":
                self.x_offset += self.pan_speed
            elif action == "pan_right":
                self.x_offset -= self.pan_speed
            elif action == "pan_up":
                self.y_offset += self.pan_speed
            elif action == "pan_down":
                self.y_offset -= self.pan_speed
            elif action == "zoom_in":
                self.handle_zoom(True)
            elif action == "zoom_out":
                self.handle_zoom(False)
            elif action == "reset_view":
                self.zoom = 1.0
                self.x_offset = 0
                self.y_offset = 0

            self.constrain_position()

    def render(self):
        self.screen.fill((0, 0, 0))

        # Draw map
        scaled_width = int(self.original_surface.get_width() * self.zoom)
        scaled_height = int(self.original_surface.get_height() * self.zoom)

        scaled_surface = pygame.transform.scale(
            self.original_surface, (scaled_width, scaled_height))

        display_x = self.screen_width // 2 - scaled_width // 2 + self.x_offset
        display_y = self.screen_height // 2 - scaled_height // 2 + self.y_offset

        self.screen.blit(scaled_surface, (display_x, display_y))

        # Draw UI elements
        if self.current_map_url:
            font = pygame.font.Font(None, 24)
            map_name = self.current_map_url.split('/')[-1].replace('.jpg', '')
            text = font.render(f"Map: {map_name} | Zoom: {self.zoom:.1f}x", True, (255, 255, 255))
            self.screen.blit(text, (10, 10))

        self.settings_button.draw(self.screen)
        self.refresh_button.draw(self.screen)

        if self.show_settings:
            self.draw_settings_menu()

        pygame.display.flip()

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

    def run(self):
        running = True
        clock = pygame.time.Clock()

        # Initial map check
        self.check_for_new_map()
        self.last_joystick_update = time.time()

        while running:
            # Update joysticks every 5 seconds instead of every frame
            current_time = time.time()
            if current_time - self.last_joystick_update > 5:
                self.update_joysticks()
                self.last_joystick_update = current_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.show_settings:
                    self.show_settings = False
                    continue

                if self.show_settings:
                    if self.handle_settings_input(event, pygame.mouse.get_pos()):
                        continue
                else:
                    self.handle_mouse_input(event)

                    if self.settings_button.handle_event(event):
                        self.show_settings = not self.show_settings
                    elif self.refresh_button.handle_event(event):
                        self.refresh_map()

            if not self.show_settings:
                self.check_for_new_map()
                self.handle_input()

            self.render()
            clock.tick(60)  # Limit to 60 FPS

        pygame.quit()

    def cleanup(self):
        """Clean up resources"""
        pygame.quit()


def main():
    viewer = None
    try:
        viewer = MapViewer()
        viewer.run()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if viewer:
            viewer.cleanup()


if __name__ == "__main__":
    main()