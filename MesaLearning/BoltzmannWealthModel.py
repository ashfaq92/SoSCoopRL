# File: wealth_app.py
# Proper Solara app structure for Mesa ABM

import mesa
import solara
from mesa import Model
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid
from mesa.visualization import SolaraViz, make_plot_component, make_space_component


def compute_gini(model):
    agent_wealths = [agent.wealth for agent in model.agents]
    if len(agent_wealths) == 0:
        return 0
    x = sorted(agent_wealths)
    N = len(x)
    if sum(x) == 0:
        return 0
    B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * sum(x))
    return 1 + (1 / N) - 2 * B


class MoneyAgent(CellAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self.wealth = 1

    def move(self):
        self.cell = self.cell.neighborhood.select_random_cell()

    def give_money(self):
        cellmates = [agent for agent in self.cell.agents if agent is not self]
        if cellmates:
            other = self.random.choice(cellmates)
            other.wealth += 1
            self.wealth -= 1

    def step(self):
        self.move()
        if self.wealth > 0:
            self.give_money()


class MoneyModel(Model):
    def __init__(self, n=10, width=10, height=10, seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        self.grid = OrthogonalMooreGrid((width, height), random=self.random)

        MoneyAgent.create_agents(
            self,
            self.num_agents,
            self.random.choices(self.grid.all_cells.cells, k=self.num_agents)
        )

        self.datacollector = mesa.DataCollector(
            model_reporters={"Gini": compute_gini},
            agent_reporters={"Wealth": "wealth"}
        )
        self.datacollector.collect(self)

    def step(self):
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)


def agent_portrayal(agent):
    size = 10
    color = "tab:red"
    if agent.wealth > 0:
        size = 50
        color = "tab:blue"
    return {"size": size, "color": color}


model_params = {
    "n": {
        "type": "SliderInt",
        "value": 50,
        "label": "Number of agents:",
        "min": 10,
        "max": 100,
        "step": 1,
    },
    "width": 10,
    "height": 10,
}


# Create the components
def create_visualization():
    money_model = MoneyModel(n=50, width=10, height=10)
    SpaceGraph = make_space_component(agent_portrayal)
    GiniPlot = make_plot_component("Gini")

    return SolaraViz(
        money_model,
        components=[SpaceGraph, GiniPlot],
        model_params=model_params,
        name="Boltzmann Wealth Model",
    )


# This is the key - define the app at module level
app = create_visualization()

# For Jupyter compatibility
Page = app  # Solara expects either 'app' or 'Page'

# If run directly, start server
if __name__ == "__main__":
    # This is just for testing - normally you'd use: solara run wealth_app.py
    print("Run with: solara run wealth_app.py")
    print("Or: python -m solara.server wealth_app.py")
    # solara run rough.py