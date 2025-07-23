import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid
from mesa.datacollection import DataCollector

from agents.box import Box
from agents.nest import Nest
from agents.robot_base import RobotBase
from agents.robot_cooperative import RobotCooperative
from agents.robot_greedy import RobotGreedy
from agents.robot_random import RobotRandom
from agents.robot_saphesia import RobotSaphesia


class CoCaRoModel(mesa.Model):
    def __init__(self, robot_type, robot_num, box_num, width=50, height=50, seed=None):
        super().__init__(seed=seed)
        self.grid = OrthogonalVonNeumannGrid( (width, height), random=self.random)
        self.robot_type = robot_type
        self.robot_num = robot_num
        self.box_num = box_num
        # Track steps for dynamic box spawning
        self.box_spawn_interval = 3
        self.colors = ["red", "green", "blue"]

        self.initialize_nests()
        self.initialize_boxes()
        self.initialize_robots()

        self.data_collector = DataCollector(
            model_reporters={
                "BoxCount": lambda m: sum(isinstance(b, Box) for b in m.agents),
                "MeanBatteryLevel": lambda m: (
                    sum(robot.battery for robot in m.get_robots()) / len(m.get_robots())
                    if m.get_robots()  # non-empty list is truthy
                    else 0
                ),
                "AliveRobots": lambda m: len([
                    r for r in m.get_robots() if r.battery > 0
                ]),
            }
        )

    def get_robots(self):
        """Helper method to get all robot agents"""
        return [agent for agent in self.agents if isinstance(agent, RobotBase)]

    def initialize_nests(self):
        nest_num = 3
        nest_locations = [self.grid[(15, 15)], self.grid[(35, 15)], self.grid[(25, 32)]]
        shuffled_colors = self.random.sample(self.colors, len(self.colors))

        Nest.create_agents(
            self,
            nest_num,
            color=shuffled_colors,
            cell=nest_locations,
        )

    def initialize_boxes(self):
        Box.create_agents(
            self,
            self.box_num,
            color=self.random.choices(self.colors, k=self.box_num),
            cell=self.random.choices(self.grid.all_cells.cells, k=self.box_num),
        )


    def initialize_robots(self):
        robots_per_color = self.robot_num // len(self.colors)

        # Assign equal number of robots to each color
        color_list = []
        for color in self.colors:
            color_list += [color] * robots_per_color

        # if robot_num is not divisable by num_colors, assign robots randomly
        remaining = self.robot_num - len(color_list)
        color_list += self.random.choices(self.colors, k=remaining)

        # Map robot types to classes
        robot_classes = {
            "RANDOM": RobotRandom,
            "GREEDY": RobotGreedy,
            "COOPERATIVE": RobotCooperative,
            "SAPHESIA": RobotSaphesia
        }
        # Get the robot class based on type
        robot_class = robot_classes.get(self.robot_type)

        robot_class.create_agents(
            self,
            self.robot_num,
            color=color_list,
            cell=self.random.choices(self.grid.all_cells.cells, k=self.robot_num),
        )


    def get_agents_by_color(self, color):
        return [agnt for agnt in self.agents if agnt.color == color]

    def print_agent_summary(self):
        print(f"\nAgent Summary:")
        print(f"Total agents: {len(self.agents)}")
        for color in ["red", "blue", "green"]:
            count = len(self.get_agents_by_color(color))
            print(f"  {color}: {count} agents")

    def step(self):
        print(f"=== Model Step {self.steps} | {len(self.agents)} agents ===")
        self.agents.shuffle_do("step")

        # Spawn boxes every 3 steps (after step 0)
        if self.steps > 0 and self.steps % self.box_spawn_interval == 0:
            self._spawn_new_box()

        self.data_collector.collect(self)

    def _spawn_new_box(self):
        """Spawn new box at random location with random color"""
        empty_cells = [cell for cell in self.grid.all_cells if cell.is_empty]
        if empty_cells:
            new_box = Box(
                self,
                color=self.random.choice(self.colors),
                cell=self.random.choice(empty_cells)
            )




# Test it
if __name__ == "__main__":
    model = CoCaRoModel("random", robot_num=2, box_num=3, width=3, height=3)


    print("=== Initial State ===")
    model.print_agent_summary()

    print("\n=== Step 1 ===")
    model.step()

    print("\n=== Step 2 ===")
    model.step()

    model.print_agent_summary()