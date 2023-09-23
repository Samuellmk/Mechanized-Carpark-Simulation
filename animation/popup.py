import pygame


# Define a class for the popup
class Popup:
    def __init__(self, car_id):
        self.font_size = 18
        self.font = pygame.font.Font(None, self.font_size)
        self.car_info = {
            "car id": car_id,
            "parked time": None,
            "exiting time": None,
        }
        self.text = ""
        self.visible = False

    def set_text(self, key_i, value):
        self.car_info[key_i] = value
        self.update_text()

    def update_text(self):
        self.text = ""
        for key, values in self.car_info.items():
            self.text += f"{key}: {values},"

    def show(self, position):
        self.visible = True
        self.position = position

    def hide(self):
        self.visible = False

    def render(self, screen):
        if self.visible:
            # Split the text into lines based on commas
            lines = self.text.split(",")
            text_surfaces = []
            max_width = 0
            total_height = 0

            # Render each line and find the maximum width and total height
            for line in lines:
                text_surface = self.font.render(line, True, (0, 0, 0))
                text_surfaces.append(text_surface)
                max_width = max(max_width, text_surface.get_width())
                total_height += text_surface.get_height()

            # Create a white box to fit all lines, with additional top padding
            top_padding = 10  # Adjust the padding as needed
            white_box_rect = pygame.Rect(
                self.position[0] - 10,
                self.position[1] - top_padding,
                max_width + 20,
                total_height + 10 + top_padding,
            )

            # Draw the white box
            pygame.draw.rect(screen, (255, 255, 255), white_box_rect)
            pygame.draw.rect(screen, (0, 0, 0), white_box_rect, 1)

            # Blit each line onto the screen with left alignment
            left_margin = white_box_rect.left + 10  # Adjust the margin as needed
            current_y = white_box_rect.top + 5 + top_padding
            for text_surface in text_surfaces:
                text_rect = text_surface.get_rect(left=left_margin, top=current_y)
                screen.blit(text_surface, text_rect)
                current_y += text_surface.get_height()
