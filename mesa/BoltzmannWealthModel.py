import numpy as np
import pandas as pd
import seaborn as sns
import mesa

class MoneyAgent(mesa.Agent):
    """An agent with fixed initial wealth"""
    def __init__(self, model):
        super().__init__(model) # type: ignore
        self.wealth = 1
    
    def say_hi(self):
        print(f"hi from {self.unique_id}")

class MoneyModel(mesa.Model):
    def __init__(self, n, seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        # create agents
        MoneyAgent.create_agents(model=self, n=self.num_agents)

    def step(self):
        self.agents.shuffle_do("say_hi");


if __name__ == '__main__':
    starter_model = MoneyModel(10)
    starter_model.step()