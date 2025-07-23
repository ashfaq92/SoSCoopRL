#  ===== ROBOT RANDOM =====
from .robot_base import RobotBase


class RobotRandom(RobotBase):
    def __init__(self, model, color, cell, vision_range=3):
        super().__init__(model, color, cell, vision_range)

    def search_box(self):
        if self.reachable_boxes and self.targeted_box is None and self.carried_box is None and self.battery > self.min_battery:
            available_boxes = [box for box in self.reachable_boxes if box.owner is None]
            if available_boxes:
                self.targeted_box = self.random.choice(available_boxes)
                self.targeted_box.owner = self  # Reserve it immediately
                print(f'targeted box {self.targeted_box.unique_id}')