import pygame
import math

class ChartManager:
    def __init__(self):
        self.points = []
        self.chart_mode = False
        self.font = pygame.font.Font(None, 24)

    def calculate_heading(self, p1, p2):
        dx = p2[0] - p1[0]
        dy = -(p2[1] - p1[1])  # Negative because pygame y increases downward
        heading = math.degrees(math.atan2(dy, dx))  # Swapped dx/dy for North=0
        heading = (90 - heading) % 360  # Adjust to make North=0
        return heading

    def handle_click(self, event, screen_pos, map_pos):
        if not self.chart_mode or event.type != pygame.MOUSEBUTTONDOWN:
            return False

        if not hasattr(self, 'activated'):
            if event.button == 1:
                self.activated = True
            return True

        if event.button == 1:
            self.points.append(map_pos)
            return True
        elif event.button == 2:
            self.points.clear()
            return True
        elif event.button == 3:
            self.chart_mode = False
            self.activated = False
            return True
        return False

    def draw(self, screen, transform_point):
        if not self.points:
            return

        screen_points = [transform_point(p) for p in self.points]

        # Draw only the lines first
        if len(screen_points) > 1:
            # Draw connecting lines
            pygame.draw.lines(screen, (255, 0, 0), False, screen_points, 2)

            # Draw only the heading numbers midway between points
            for i in range(len(self.points) - 1):
                mid_x = (screen_points[i][0] + screen_points[i + 1][0]) / 2
                mid_y = (screen_points[i][1] + screen_points[i + 1][1]) / 2
                mid_point = (int(mid_x), int(mid_y))

                # Only draw heading text at midpoint
                heading = self.calculate_heading(self.points[i], self.points[i + 1])
                text = self.font.render(f"{heading:.1f}°", True, (0, 0, 255))
                text_rect = text.get_rect(center=mid_point)
                screen.blit(text, text_rect)

        # Draw the points last
        for point in screen_points:
            pygame.draw.circle(screen, (255, 0, 0), point, 5)