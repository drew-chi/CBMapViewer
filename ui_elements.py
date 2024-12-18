import pygame


class Button:
    def __init__(self, x, y, width, height, text, color=(100, 100, 100), hover_color=(150, 150, 150),
                 active_color=(200, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.active_color = active_color
        self.is_hovered = False
        self.is_active = False

    def draw(self, screen):
        if self.is_active:
            color = self.active_color
        else:
            color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        font = pygame.font.Font(None, 24)
        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False


class Dropdown:
    def __init__(self, x, y, width, height, options):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.open = False
        self.selected_index = 0
        self.option_height = height
        self.color = (100, 100, 100)
        self.hover_color = (150, 150, 150)
        self.hover_index = -1

    def draw(self, screen):
        # Create background overlay when dropdown is open
        if self.open:
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)
            screen.blit(overlay, (0, 0))

        # Draw main button
        pygame.draw.rect(screen, self.color, self.rect)
        font = pygame.font.Font(None, 24)
        text = font.render(self.options[self.selected_index], True, (255, 255, 255))
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

        # Draw dropdown options
        if self.open:
            dropdown_bg = pygame.Surface((self.rect.width, self.option_height * len(self.options)))
            dropdown_bg.fill((50, 50, 50))
            screen.blit(dropdown_bg, (self.rect.x, self.rect.y + self.option_height))

            for i, option in enumerate(self.options):
                if i != self.selected_index:
                    option_rect = pygame.Rect(
                        self.rect.x,
                        self.rect.y + (i + 1) * self.option_height,
                        self.rect.width,
                        self.option_height
                    )
                    color = self.hover_color if i == self.hover_index else self.color
                    pygame.draw.rect(screen, color, option_rect)
                    text = font.render(option, True, (255, 255, 255))
                    text_rect = text.get_rect(center=option_rect.center)
                    screen.blit(text, text_rect)

    def handle_event(self, event):
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.rect.collidepoint(mouse_pos):
                self.open = not self.open
            elif self.open:
                for i, option in enumerate(self.options):
                    if i != self.selected_index:
                        option_rect = pygame.Rect(
                            self.rect.x,
                            self.rect.y + (i + 1) * self.option_height,
                            self.rect.width,
                            self.option_height
                        )
                        if option_rect.collidepoint(mouse_pos):
                            self.selected_index = i
                            self.open = False
                            changed = True
                            break
                self.open = False
        return changed