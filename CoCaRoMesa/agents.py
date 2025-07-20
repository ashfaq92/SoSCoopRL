from mesa.discrete_space import CellAgent
import utils


#   ===== NEST =====
class Nest(CellAgent):
    def __init__(self, model, color, cell):
        super().__init__(model)
        self.color = color
        self.cell = cell


#   ===== BOX =====
class Box(CellAgent):
    def __init__(self, model, color, cell):
        super().__init__(model)
        self.color = color
        self.cell = cell
        self.owner = None



#  ===== ROBOT BASE CLASS =====
class RobotBase(CellAgent):
    def __init__(self, model, color, cell, vision_range=3):
        super().__init__(model)
        self.color = color
        self.cell = cell
        self.vision_range = vision_range
        self.reachable_boxes = []
        self.targeted_box = None
        self.carried_box = None
        self.target_nest = None
        self.wander_amplitude = 3  # How far to wander (like GAMA)
        # self.movement_speed = 1    # How many cells to move per step
        self.previous_cell = None  # Remember where we came from
        # battery related
        self.max_battery = 300
        self.min_battery = 0
        self.initial_battery = self.max_battery
        self.battery_consum = 1
        self._battery = self.initial_battery
        # reward related
        self.reward = 2 * self.max_battery / 3          # two-third of max energy
        self.reduced_reward = self.max_battery / 3      # one-third of max energy
        # criticality related
        self.max_criticality = self.max_battery
        self.min_criticality = self.min_battery
        self._criticality = 0

    @property
    def battery(self):
        """Battery property with automatic constraint enforcement"""
        return self._battery

    @property
    def criticality(self):
        """Battery property with automatic constraint enforcement"""
        return self._criticality

    @battery.setter
    def battery(self, value):
        """Set battery value with min/max constraints enforced"""
        self._battery = max(self.min_battery, min(self.max_battery, int(value)))

    @criticality.setter
    def criticality(self, value):
        """Set criticality value with min/max constraints enforced"""
        self._criticality = max(self.min_criticality, min(self.max_criticality, int(value)))

    def step(self):
        # print(f'Robot {self.unique_id} ({self.color}) moving from {self.cell.coordinate}')
        self.update_battery()
        # update reachable boxes
        self.update_reachable_boxes()

        self.wander()

        self.search_box()

        self.update_carried_box_position()
        self.go_to_target_box()
        self.take_box()
        self.carry_box_to_nest()
        self.drop_box_in_nest()
        self.die()

    def update_battery(self):
        if self.battery > self.min_battery:
            moved_step = (self.cell != self.previous_cell)
            if moved_step:
                self.battery -= self.battery_consum   # Uses setter automatically

    def update_criticality(self):
        self.criticality = self.max_criticality - self.battery

    def update_reachable_boxes(self):
        neighborhood = self.cell.get_neighborhood(radius=self.vision_range, include_center=False)
        self.reachable_boxes = [agent for agent in neighborhood.agents if isinstance(agent, Box)]
        # box_data = [f'{b.unique_id} ({b.color}) at {b.cell.coordinate}' for b in self.reachable_boxes]
        # print(box_data)

    def wander(self):
        """Movement logic that prevents immediate backtracking"""
        # If we have a specific target (box or nest), don't wander
        if self.targeted_box or self.target_nest or self.battery <= self.min_battery:
            return

        # Get all neighbors except the previous cell
        neighbors = [cell for cell in self.cell.neighborhood if cell != self.previous_cell]
        
        # If no valid neighbors (trapped), then allow going back
        if not neighbors:
            neighbors = list(self.cell.neighborhood)

        if neighbors:
            self.previous_cell = self.cell
            self.cell = self.random.choice(neighbors)

    def search_box(self):
        raise NotImplementedError("You must implement search_box in a subclass.")

    def update_carried_box_position(self):
        """Upate carried box position to match robot position"""
        if self.carried_box and self.battery > self.min_battery:
            self.carried_box.cell = self.cell
            # self.carried_box.coordinate = self.cell.coordinate

    def go_to_target_box(self):
        if self.targeted_box and self.battery > self.min_battery:
            target_coord = self.targeted_box.cell.coordinate
            if self._move_towards_target(target_coord):
                print(f'Robot {self.unique_id} reached target box {self.targeted_box.unique_id}!')
            else:
                print('moving towards target box')

    def take_box(self):     # aka pickup box
        if self.targeted_box and self.targeted_box.cell.coordinate == self.cell.coordinate and self.battery > self.min_battery:
            self.carried_box = self.targeted_box
            self.targeted_box = None
            print('picked up the box')

    def carry_box_to_nest(self):
        if not self.carried_box or self.battery <= self.min_battery:
            return

        if self.carried_box in self.model.agents:
            # Find closest suitable nest
            matching_nests = [nest for nest in self.model.agents_by_type[Nest] if nest.color == self.carried_box.color]
            if matching_nests:
                self.target_nest = matching_nests[0]

            if self.target_nest:
                target_coord = self.target_nest.cell.coordinate
                if self._move_towards_target(target_coord):
                    print(f'Robot {self.unique_id} reached {self.carried_box.color} nest!')
                else:
                    print(f'carrying {self.carried_box.color} box to nest')
        else:
            # box is dead
            self.carried_box = None

    def drop_box_in_nest(self):
        if self.carried_box and self.target_nest and self.battery > self.min_battery and self.carried_box in self.model.agents:
            robot_coord = self.cell.coordinate
            box_coord = self.carried_box.cell.coordinate
            nest_coord = self.target_nest.cell.coordinate

            if robot_coord == box_coord and robot_coord == nest_coord:
                # set reward
                self.battery = self.battery + self._colors_reward_efficiency(self.carried_box.color)

                box_to_remove = self.carried_box

                # clear all agents' references to this box
                for agent in self.model.agents:
                    if hasattr(agent, "targeted_box") and agent.targeted_box == box_to_remove:
                        agent.targeted_box = None
                    if hasattr(agent, "carried_box") and agent.carried_box == box_to_remove:
                        agent.carried_box = None

                # kill the box (remove from the model)
                box_to_remove.remove()
                self.carried_box = None
                self.target_nest = None
                print('box deposited into nest!')

    def die(self):
        if self.battery <= self.min_battery:
            if self.carried_box:
                self.carried_box.owner = None
                self.carried_box = None
            if self.targeted_box:
                self.targeted_box.owner = None
                self.targeted_box = None
            self.color = 'gray'


    def _colors_reward_efficiency(self, box_color):
        resp = self.reward if box_color == self.color else self.reduced_reward
        print('box color', box_color, 'robot color', self.color, 'reward', resp)
        return resp


    def _move_towards_target(self, target_coord):
        """Move one step towards target coordinate"""
        current_coord = self.cell.coordinate
        # Check if already at target
        if current_coord == target_coord:
            return True  # Reached target

        # Move towards target
        neighbors = list(self.cell.neighborhood)
        if neighbors:
            # Find ALL neighbors with minimum distance (not just first one)
            distances = [(cell, utils.manhattan(cell.coordinate, target_coord)) for cell in neighbors]
            min_distance = min(distances, key=lambda x: x[1])[1]
            best_neighbors = [cell for cell, dist in distances if dist == min_distance]
            # Remember current position before moving
            self.previous_cell = self.cell
            # Randomly pick among equally good neighbors
            self.cell = self.random.choice(best_neighbors)
            return False  # Still moving

        return False  # No neighbors, can't move

    def _compute_anticipated_criticality(self, box_to_take):
        dist_box_to_me = utils.manhattan(self.cell.coordinate, box_to_take.cell.coordinate)
        nest_cell = None
        # Find closest suitable nest
        matching_nests = [nest for nest in self.model.agents_by_type[Nest] if nest.color == box_to_take.color]
        if matching_nests:
            nest_cell = matching_nests[0]

        dist_box_to_nest = utils.manhattan(box_to_take.cell.coordinate, nest_cell.cell.coordinate)
        anticipated_battery_before_reward = self.battery - (dist_box_to_me + dist_box_to_nest) * self.battery_consum

        if anticipated_battery_before_reward < 0:
            anticipated_battery_before_reward = 0

        anticipated_battery = anticipated_battery_before_reward + self._colors_reward_efficiency(box_to_take.color)

        # if anticipated_battery < self.min_battery or anticipated_battery_before_reward == 0:
        #     return self.max_criticality
        # elif anticipated_battery > self.max_battery:
        #     return self.min_criticality
        # else:
        #     return self.max_criticality - anticipated_battery
        # Updated version with safety check first:
        if anticipated_battery_before_reward <= 0:  # Robot dies during the mission
            return self.max_criticality
        elif self.min_battery < anticipated_battery < self.max_battery:
            return self.max_criticality - anticipated_battery
        elif anticipated_battery >= self.max_battery:
            return self.min_criticality
        else:  # anticipated_battery <= 0 (but robot survived the mission)
            return self.max_criticality




#  ===== ROBOT RANDOM =====
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


#  ===== ROBOT Cooperative =====
class RobotCooperative(RobotBase):
    pass


#  ===== ROBOT Saphesia =====
class RobotSaphesia(RobotBase):
    pass