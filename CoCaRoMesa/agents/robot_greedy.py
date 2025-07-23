from .robot_base import RobotBase


#  ===== ROBOT GREEDY =====
class RobotGreedy(RobotBase):
    def __init__(self, model, color, cell, vision_range=3):
        super().__init__(model, color, cell, vision_range)

    def search_box(self):
        """Non-cooperative greedy box selection algorithm"""
        if not self.reachable_boxes or self.battery <= self.min_battery:
            return

        for bx in self.reachable_boxes:
            # skip if box is already owned by someone else
            if bx.owner and bx.owner != self:
                continue

            ant_reach_crit = self._compute_anticipated_criticality(bx)
            # not carrying anything
            if self.carried_box is None:
                if self.targeted_box is None:  # neither carrying nor targetting
                    self.targeted_box = bx
                    self.targeted_box.owner = self
                else:  # not carrying but targeting
                    my_target_box_crit = self._compute_anticipated_criticality(self.targeted_box)
                    # check if this is a better box (lower criticality = better)
                    if ant_reach_crit < my_target_box_crit:
                        self.targeted_box.owner = None
                        self.targeted_box = bx
                        self.targeted_box.owner = self
            # carrying a box
            else:
                my_carried_box_crit = self._compute_anticipated_criticality(self.carried_box)
                # check if this is a better box
                if ant_reach_crit < my_carried_box_crit:
                    # drop the current box (on spot, not at nest)
                    self.carried_box.owner = None
                    self.carried_box = None
                    # Target the new better box
                    self.targeted_box = bx
                    self.targeted_box.owner = self

