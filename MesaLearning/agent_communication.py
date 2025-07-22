import mesa


class Message:
    def __init__(self, sender, performative, content):
        self.sender = sender
        self.performative = performative
        self.content = content

    def __repr__(self):
        return f"Message(from:{self.sender}, {self.performative}, {self.content})"


class MyAgent(mesa.Agent):
    def __init__(self, model):
        super().__init__(model)
        self.battery = 100

        # GAMA-style separate message lists
        self.requests = []
        self.agrees = []
        self.refuses = []
        self.informs = []

    def send(self, to_id, performative, content):
        """Send message to another agent"""
        try:
            recipient = next(a for a in self.model.agents if a.unique_id == to_id)
            msg = Message(self.unique_id, performative, content)

            # Add to specific list based on performative
            target_list = getattr(recipient, f"{performative}s")
            target_list.append(msg)

            print(f"✓ {performative} sent: {self.unique_id} → {to_id}")

        except StopIteration:
            print(f"✗ Agent {to_id} not found!")

    def read_requests(self):
        """Handle request messages - GAMA style reflex"""
        if not self.requests or self.battery <= 0:
            return

        for request in self.requests:
            print(f"  Agent {self.unique_id} processing request from {request.sender}: {request.content}")

            # Decision logic
            if self.can_fulfill(request.content):
                self.send(request.sender, "agree", f"OK to {request.content}")
            else:
                self.send(request.sender, "refuse", "Cannot help")

        self.requests.clear()

    def read_agrees(self):
        """Handle agree messages - GAMA style reflex"""
        if not self.agrees or self.battery <= 0:
            return

        for agree in self.agrees:
            print(f"  Agent {self.unique_id} got agreement from {agree.sender}: {agree.content}")
            # Maybe start some action...

        self.agrees.clear()

    def read_refuses(self):
        """Handle refuse messages - GAMA style reflex"""
        if not self.refuses or self.battery <= 0:
            return

        for refuse in self.refuses:
            print(f"  Agent {self.unique_id} got refusal from {refuse.sender}: {refuse.content}")
            # Maybe try alternative...

        self.refuses.clear()

    def read_informs(self):
        """Handle inform messages - GAMA style reflex"""
        if not self.informs or self.battery <= 0:
            return

        for inform in self.informs:
            print(f"  Agent {self.unique_id} got info from {inform.sender}: {inform.content}")
            # Process information...

        self.informs.clear()

    def can_fulfill(self, content):
        """Simple decision logic"""
        return "help" in str(content).lower()

    def step(self):
        """Agent step - GAMA-style message processing"""
        print(f"\n--- Agent {self.unique_id} step ---")

        # Process each message type separately (like GAMA reflexes)
        self.read_requests()
        self.read_agrees()
        self.read_refuses()
        self.read_informs()


class MyModel(mesa.Model):
    def __init__(self, n_agents=5):
        super().__init__()

        # Create agents
        MyAgent.create_agents(self, n_agents)

        print(f"Created {n_agents} agents with GAMA-style messaging")
        print("Agent unique_ids:", [a.unique_id for a in self.agents])

    def step(self):
        print(f"\n========== MODEL STEP {self.steps} ==========")

        # Some agents send messages to others
        if self.steps == 1:
            print("Sending initial messages...")
            # Use actual unique_ids, not array indices
            self.agents[0].send(self.agents[1].unique_id, "request", "help with box")
            self.agents[1].send(self.agents[2].unique_id, "request", "give me resource")
            self.agents[2].send(self.agents[3].unique_id, "request", "cooperation needed")
            self.agents[3].send(self.agents[4].unique_id, "inform", "box location at (5,3)")

        # All agents process their messages
        self.agents.do("step")


# Demo run
if __name__ == "__main__":
    model = MyModel(5)

    print("\n" + "=" * 50)
    print("GAMA-STYLE MESSAGING DEMO")
    print("=" * 50)

    for i in range(3):
        model.step()

    print(f"\n✓ Demo complete after {model.steps} steps")