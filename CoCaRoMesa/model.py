
import mesa
from mesa.discrete_space import OrthogonalVonNeumannGrid, CellAgent

from agents import Nest, Box, RobotRandom, RobotCooperative, RobotSaphesia
from mesa.datacollection import DataCollector

class CoCaRoModel(mesa.Model):
    def __init__(self, robot_type, width=50, height=50, seed=None):
        super().__init__(seed=seed)
        self.grid = OrthogonalVonNeumannGrid( (width, height), random=self.random)
        self.robot_type = robot_type

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
        box_num = 100
        Box.create_agents(
            self,
            box_num,
            color=self.random.choices(self.colors, k=box_num),
            cell=self.random.choices(self.grid.all_cells.cells, k=box_num),
        )


    def initialize_robots(self):
        robot_num = 1

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
            robot_num,
            color=self.random.choices(self.colors, k=robot_num),
            # todo: robot color equal num (90=30red, 30green, 30blue)
            cell=self.random.choices(self.grid.all_cells.cells, k=robot_num),
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