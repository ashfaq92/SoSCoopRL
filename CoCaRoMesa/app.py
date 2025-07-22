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
    ax.grid(True, linestyle='--', linewidth=0.5)

    solara.FigureMatplotlib(fig)

@solara.component
def MeanBatteryPlot(model):
    update_counter.get()  # ensures re-rendering on step

    # Retrieve collected data
    df = model.data_collector.get_model_vars_dataframe().reset_index()

    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()

    # Plot using seaborn (with matplotlib backend)
    sns.lineplot(data=df, x="index", y="MeanBatteryLevel", ax=ax)

    ax.set_title("Mean Battery Level Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Mean Battery")
    ax.grid(True, linestyle='--', linewidth=0.5)

    solara.FigureMatplotlib(fig)


@solara.component
def AliveRobotsPlot(model):
    update_counter.get()  # ensures re-rendering on step

    # Retrieve collected data
    df = model.data_collector.get_model_vars_dataframe().reset_index()

    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()

    # Plot using seaborn (with matplotlib backend)
    sns.lineplot(data=df, x="index", y="AliveRobots", ax=ax)

    ax.set_title("Alive Robots Over Time")
    ax.set_xlabel("Step")
    ax.set_ylabel("Alive Robots")
    ax.grid(True, linestyle='--', linewidth=0.5)


    solara.FigureMatplotlib(fig)



def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {
        "size": 200,
        "color": "tab:"+agent.color,
    }
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
    "width": 50,
    "height": 50,
    "robot_type": "COOPERATIVE",
    "robot_num": 90,
    "box_num": 18
}

def grow_figure(ax):
    # ax is your grid’s Axes; get the Figure and resize it
    ax.figure.set_size_inches(20, 20)

# create the components
def create_visualization():
    cocaro_model = CoCaRoModel(
        robot_type= model_params["robot_type"], 
        robot_num=model_params["robot_num"], 
        box_num=model_params["box_num"], 
        width=model_params["width"], 
        height=model_params["height"]
    )
    SpaceGraph = make_space_component(
        agent_portrayal,
        post_process=grow_figure
    )

    return SolaraViz(
        model=cocaro_model,
        components=[SpaceGraph, BoxCountPlot, MeanBatteryPlot, AliveRobotsPlot],
        model_params=model_params,
        name="CoCaRo Model",
    )

app = create_visualization()
Page = app

if __name__ == "__main__":
    print("Run with: solara run app.py")
    print("Or: python -m solara.server app.py")