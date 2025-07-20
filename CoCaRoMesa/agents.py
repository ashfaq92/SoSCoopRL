import mesa
from mesa.discrete_space import CellAgent


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
        self.battery = 300
        self.wander_amplitude = 3  # How far to wander (like GAMA)
        self.movement_speed = 1    # How many cells to move per step
        self.previous_cell = None  # Remember where we came from


    def update_reachable_boxes(self):
        neighborhood = self.cell.get_neighborhood(radius=self.vision_range, include_center=False)
        self.reachable_boxes = [agent for agent in neighborhood.agents if isinstance(agent, Box)]
        # box_data = [f'{b.unique_id} ({b.color}) at {b.cell.coordinate}' for b in self.reachable_boxes]
        # print(box_data)


    def move(self):
        current_x, current_y = self.cell.coordinate
        
        target_x = max(0, min(self.model.grid.width - 1, 
                            current_x + self.random.randint(-self.wander_amplitude, self.wander_amplitude)))
        target_y = max(0, min(self.model.grid.height - 1,
                            current_y + self.random.randint(-self.wander_amplitude, self.wander_amplitude)))
        
        # Find target cell
        for cell in self.model.grid.all_cells:
            if cell.coordinate == (target_x, target_y):
                self.move_towards_target((target_x, target_y))
                return
        
        # Fallback - but don't go back to previous cell
        neighbors = [cell for cell in self.cell.neighborhood if cell != self.previous_cell]
        
        if neighbors:
            self.cell = self.random.choice(neighbors)
        else:
            self.cell = self.cell.neighborhood.select_random_cell()

    def search_box(self):
        raise NotImplementedError("You must implement search_box in a subclass.")

    def move_towards_target(self, target_coord):
        """Move one step towards target coordinate"""
        current_coord = self.cell.coordinate
        # Check if already at target
        if current_coord == target_coord:
            return True  # Reached target

        # Move towards target
        neighbors = list(self.cell.neighborhood)
        if neighbors:
            # Find ALL neighbors with minimum distance (not just first one)
            distances = [(cell, abs(cell.coordinate[0] - target_coord[0]) + abs(cell.coordinate[1] - target_coord[1])) for cell in neighbors]
            min_distance = min(distances, key=lambda x: x[1])[1]
            best_neighbors = [cell for cell, dist in distances if dist == min_distance]
            # Remember current position before moving
            self.previous_cell = self.cell
            # Randomly pick among equally good neighbors
            self.cell = self.random.choice(best_neighbors)
            return False  # Still moving

        return False  # No neighbors, can't move


    def go_to_target_box(self):
        if self.targeted_box and self.battery > 0:
            target_coord = self.targeted_box.cell.coordinate
            if self.move_towards_target(target_coord):
                print(f'Robot {self.unique_id} reached target box {self.targeted_box.unique_id}!')
            else:
                print('moving towards target box')

    def take_box(self):
        if self.targeted_box and self.targeted_box.cell.coordinate == self.cell.coordinate and self.battery > 0:
            self.carried_box = self.targeted_box
            self.targeted_box = None
            print('picked up the box')

    def carry_box_to_nest(self):
        if self.carried_box and self.battery > 0:
            if self.carried_box in self.model.agents:
                # Find suitable nest
                nests = self.model.agents_by_type[Nest]
                matching_nests = nests.select(lambda nest: nest.color == self.carried_box.color)
                if matching_nests:
                    self.target_nest = matching_nests[0]

                if self.target_nest:
                    target_coord = self.target_nest.cell.coordinate
                    if self.move_towards_target(target_coord):
                        print(f'Robot {self.unique_id} reached {self.carried_box.color} nest!')
                    else:
                        print(f'carrying {self.carried_box.color} box to nest')
            else:
                # box is dead
                self.carried_box = None

    def update_carried_box_position(self):
        """Upate carried box position to match robot position"""
        if self.carried_box and self.battery > 0:
            self.carried_box.cell = self.cell
            # self.carried_box.coordinate = self.cell.coordinate

    def drop_box_in_nest(self):
        if self.carried_box and self.target_nest and self.battery > 0 and self.carried_box in self.model.agents:
            # Triple check all are at same location (paranoia level: max! 🔥)
            robot_coord = self.cell.coordinate
            box_coord = self.carried_box.cell.coordinate
            nest_coord = self.target_nest.cell.coordinate

            if robot_coord == box_coord and robot_coord == nest_coord and box_coord == nest_coord:
                # set reward
                box_to_remove = self.carried_box

                # clear all agents' references to this box
                for agent in self.model.agents:
                    if hasattr(agent, "targeted_box") and agent.targeted_box == box_to_remove:
                        agent.targeted_box = None
                    if hasattr(agent, "carried_box") and agent.carried_box == box_to_remove:
                        agent.carried_box = None

                # kill the box (remove from model)
                box_to_remove.remove()
                self.carried_box = None
                self.target_nest = None
                print(f'Robot {self.unique_id} dropped {box_to_remove.color} box in nest!')

    def step(self):
        # print(f'Robot {self.unique_id} ({self.color}) moving from {self.cell.coordinate}')
        self.move()
        # print(f'  -> now at {self.cell.coordinate}')
        self.update_carried_box_position()

        # update reachable boxes
        self.update_reachable_boxes()

        # update reachable boxes
        self.search_box()
        self.go_to_target_box()
        self.take_box()
        self.carry_box_to_nest()
        self.drop_box_in_nest()




#  ===== ROBOT RANDOM =====
class RobotRandom(RobotBase):
    def __init__(self, model, color, cell, vision_range=3):
        super().__init__(model, color, cell, vision_range)

    def search_box(self):
        if self.reachable_boxes and self.targeted_box is None and self.carried_box is None and self.battery > 0:
            available_boxes = [box for box in self.reachable_boxes if box.owner is None]
            if available_boxes:
                self.targeted_box = self.random.choice(available_boxes)
                self.targeted_box.owner = self  # Reserve it immediately
                print(f'targeted box {self.targeted_box.unique_id}')



#  ===== ROBOT Cooperative =====
class RobotCooperative(RobotBase):
    pass

#  ===== ROBOT Saphesia =====
class RobotSaphesia(RobotBase):
    pass