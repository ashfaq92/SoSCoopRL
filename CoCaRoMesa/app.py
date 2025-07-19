from mesa.visualization import make_space_component, SolaraViz
from mesa.visualization.utils import update_counter
from matplotlib.figure import Figure
import seaborn as sns
import solara
from model import CoCaRoModel
from agents import Nest, Box, RobotBase


@solara.component
def BoxCountPlot(model):
    update_counter.get()  # ensures re-rendering on step

    # Retrieve collected data
    df = model.data_collector.get_model_vars_dataframe().reset_index()

    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()

    # Plot using seaborn (with matplotlib backend)
    sns.lineplot(data=df, x="index", y="BoxCount", ax=ax)

    ax.set_title("Box Count Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Box Count")

    solara.FigureMatplotlib(fig)

def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {
        "size": 200,
        "color": "tab:"+agent.color,
    }
    # todo: zorder not working
    if isinstance(agent, Box):
        portrayal["marker"] = "s"   # square for boxes
        portrayal["zorder"] = 1
    elif isinstance(agent, Nest):
        portrayal["marker"] = "H"   # hexagon for trash bins
        portrayal["zorder"] = 0     # background layer
    elif isinstance(agent, RobotBase):
        portrayal["marker"] = "^"   # triangle pointing up for robots
        portrayal["zorder"] = 2     # top layer

    return portrayal


model_params = {
    "n": {
       "type": "SliderInt",
        "value": 50,
        "label": "Number of Agents:",
        "min": 10,
        "max": 100,
        "step": 1
    },
    "width": 50,
    "height": 50,
    "robot_type": "random",
}

def grow_figure(ax):
    # ax is your grid’s Axes; get the Figure and resize it
    ax.figure.set_size_inches(20, 20)

# create the components
def create_visualization():
    cocaro_model = CoCaRoModel(robot_type="random", width=50, height=50)
    SpaceGraph = make_space_component(
        agent_portrayal,
        post_process=grow_figure
    )

    return SolaraViz(
        model=cocaro_model,
        components=[SpaceGraph, BoxCountPlot],
        model_params=model_params,
        name="CoCaRo Model",
    )

app = create_visualization()
Page = app

if __name__ == "__main__":
    print("Run with: solara run app.py")
    print("Or: python -m solara.server wealth_app.py")