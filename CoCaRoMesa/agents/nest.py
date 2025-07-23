from mesa.discrete_space import CellAgent

#   ===== NEST =====
class Nest(CellAgent):
    def __init__(self, model, color, cell):
        super().__init__(model)
        self.color = color
        self.cell = cell