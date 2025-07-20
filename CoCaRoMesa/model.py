
import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid, CellAgent

from agents import Nest, Box, RobotRandom, RobotCooperative, RobotSaphesia
from mesa.datacollection import DataCollector

class CoCaRoModel(mesa.Model):
    def __init__(self, robot_type, robot_num, box_num, width=50, height=50, seed=None):
        super().__init__(seed=seed)
        self.grid = OrthogonalVonNeumannGrid( (width, height), random=self.random)
        self.robot_type = robot_type
        self.robot_num = robot_num
        self.box_num = box_num

        self.colors = ["red", "green", "blue"]

        self.initialize_nests()
        self.initialize_boxes()
        self.initialize_robots()

        self.data_collector = DataCollector(
            model_reporters={
                "BoxCount": lambda m: sum(isinstance(b, Box) for b in m.agents)
            }
        )

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
            "random": RobotRandom,
            "cooperative": RobotCooperative,
            "saphesia": RobotSaphesia
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
        print(f"=== Model Step - {len(self.agents)} agents ===")
        self.agents.shuffle_do("step")
        self.data_collector.collect(self)



# Test it
if __name__ == "__main__":
    model = CoCaRoModel("random", width=3, height=3)

    print("=== Initial State ===")
    model.print_agent_summary()

    print("\n=== Step 1 ===")
    model.step()

    print("\n=== Step 2 ===")
    model.step()

    model.print_agent_summary()