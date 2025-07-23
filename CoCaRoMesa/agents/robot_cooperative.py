from collections import namedtuple

from .robot_base import RobotBase

#  ===== ROBOT Cooperative =====
Message = namedtuple("Message", ["sender", "performative", "content"])

class RobotCooperative(RobotBase):
    # Message content constants
    CRITICALITY_STRING = "criticality"
    DEMAND_BOX_STRING = "GiveMeYourBox"
    GIVE_MY_BOX_STRING = "GiveMyBoxToYou"
    REFUSE_STRING = "Ko"

    # Performative constants
    REQUEST = "request"
    AGREE = "agree"
    REFUSE = "refuse"
    INFORM = "inform"

    def __init__(self, model, color, cell, vision_range=3):
        super().__init__(model, color, cell, vision_range)

        self.requests = []
        self.agrees = []
        self.refuses = []
        self.informs = []
        self.box_reserved = False
        self.need_box_threshold = self.max_criticality / 2  # todo: why??
        self.is_request_criticality_last_cycle = False

    @property
    def _is_need_a_box(self):
        return self.need_box_threshold < self.criticality

    def search_box(self):
        if not self.reachable_boxes or self.battery <= self.min_battery:
            return

        for bx in self.reachable_boxes:
            message_sent = False
            ant_reach_crit = self._compute_anticipated_criticality(bx)
            if bx.owner is None:
                if self.carried_box is None:    # i am not carrying a box
                    if self.targeted_box is None:   # neither carrying nor targetting
                        self.targeted_box = bx
                        self.targeted_box.owner = self
                    else:   # not carrying but targetting
                        my_target_box_crit = self._compute_anticipated_criticality(self.targeted_box)
                        if ant_reach_crit < my_target_box_crit:    # check if this is a better box
                            self.targeted_box.owner = None
                            self.targeted_box = bx
                            self.targeted_box.owner = self
                else:   # I am carrying a box
                    my_carried_box_crit = self._compute_anticipated_criticality(self.carried_box)
                    if ant_reach_crit < my_carried_box_crit:  # check if this is a better box
                        # drop the current box
                        self.carried_box.owner = None
                        self.carried_box = None
                        # target the new better box
                        self.targeted_box = bx
                        self.targeted_box.owner = self
            else:   # box has an owner
                if bx.owner != self and not message_sent:  # check if i am not the owner
                    if self.carried_box is None:  # i dont carry a box
                        if self.targeted_box is None:  # neither carrying nor targetting
                            self._send(
                                to_id=bx.owner.unique_id,
                                performative=self.REQUEST,
                                content=[self.CRITICALITY_STRING, ant_reach_crit, self.criticality]
                            )
                        else:   # not carrying but targetting
                            my_target_box_crit = self._compute_anticipated_criticality(self.targeted_box)
                            if ant_reach_crit < my_target_box_crit:
                                self._send(
                                    to_id=bx.owner.unique_id,
                                    performative=self.REQUEST,
                                    content=[self.CRITICALITY_STRING, ant_reach_crit, self.criticality]
                                )
                    else:  # I'm carrying a box
                        my_carried_box_crit = self._compute_anticipated_criticality(self.carried_box)
                        if ant_reach_crit < my_carried_box_crit:
                            self._send(
                                to_id=bx.owner.unique_id,
                                performative=self.REQUEST,
                                content=[self.CRITICALITY_STRING, ant_reach_crit, self.criticality]
                            )

    def read_requests(self):
        if not self.requests or self.battery <= self.min_battery:
            return
        for request in self.requests:
            print(f"  Agent {self.unique_id} processing request from {request.sender}: {request.content}")
            request_type = request.content[0]
            if request_type==self.CRITICALITY_STRING and (self.carried_box or self.targeted_box):
                # Safe to assume there's a real box to act on
                my_ant_crit = 0
                if self.carried_box:
                    my_ant_crit = self._compute_anticipated_criticality(self.carried_box)
                elif self.targeted_box:
                    my_ant_crit = self._compute_anticipated_criticality(self.targeted_box)
                else:
                    raise ValueError('Unexpected error in read_requests!')

                sender_ant_crit = request.content[1]
                sender_instant_crit = request.content[2]
                if self.criticality >= sender_instant_crit:
                    if self.criticality >= my_ant_crit:
                        self._send(to_id=request.sender, performative=self.REFUSE, content=[self.REFUSE_STRING] )
                    else:
                        self._send(to_id=request.sender, performative=self.AGREE, content=[self.GIVE_MY_BOX_STRING])
                        self._send(to_id=request.sender, performative=self.INFORM, content=[self.GIVE_MY_BOX_STRING, my_ant_crit])
                        self.box_reserved = True
                elif self.criticality + 10 <= sender_instant_crit:
                    print("Sending box because you're much more critical")
                    self._send(to_id=request.sender, performative=self.AGREE, content=[self.GIVE_MY_BOX_STRING])
                    self._send(to_id=request.sender, performative=self.INFORM, content=[self.GIVE_MY_BOX_STRING, my_ant_crit])
                    self.box_reserved = True
                else:
                    self._send(to_id=request.sender, performative=self.REFUSE, content=[self.REFUSE_STRING])
            elif request_type == self.DEMAND_BOX_STRING:
                if self.carried_box:
                    self._send(to_id=request.sender, performative=self.AGREE, content=[self.carried_box])
                elif self.targeted_box:
                    self._send(to_id=request.sender, performative=self.AGREE, content=[self.targeted_box])
                else:
                    self._send(to_id=request.sender, performative=self.REFUSE, content=[self.REFUSE_STRING])

                # TODO: seems buggy. this must be in one of the above if statements
                # TODO: also, robots must exhange boxes not just dropping the box, comparing criticality before exchange
                self.carried_box = None
                self.targeted_box = None
                self.box_reserved = False
        self.requests.clear()

    def read_agrees(self):
        """Handle agree messages - GAMA style reflex"""
        if not self.agrees or self.battery <= self.min_battery:
            return

        for agree in self.agrees:
            agree_type = agree.content[0]
            if agree_type==self.GIVE_MY_BOX_STRING:
                self.is_request_criticality_last_cycle = False
            else:
                box_given = agree.content[0]
                print(box_given)
                if self.carried_box:
                    self.carried_box.owner = None
                    self.carried_box = None
                elif self.targeted_box:
                    self.targeted_box.owner = None
                self.targeted_box = box_given
                self.targeted_box.owner = self

        self.agrees.clear()

    def read_refuses(self):
        #TODO: double check this method: clear refuses? is_crit??
        """Handle refuse messages - GAMA style reflex"""
        if not self.refuses or self.battery <= 0:
            return
        self.is_request_criticality_last_cycle = False
        self.refuses.clear()

    def read_informs(self):
        """Handle inform messages - GAMA style reflex"""
        if not self.informs or self.battery <= 0:
            return
        best_criticality = self.max_criticality
        giver = None
        for inform in self.informs:
            # print(f"  Agent {self.unique_id} got info from {inform.sender}: {inform.content}")
            content_type = inform.content[0]
            if content_type==self.GIVE_MY_BOX_STRING:
                ant_crit_temp = inform.content[1]
                if ant_crit_temp < best_criticality:
                    best_criticality = ant_crit_temp
                    giver = inform.sender
        # request the box from the best give
        if giver:
            # todo: check if give is still in communication range
            self._send(to_id=giver, performative=self.REQUEST, content=[self.DEMAND_BOX_STRING])
            # Remove the reservation from others
            for inform in self.informs:
                content_type = inform.content[0]
                other_giver = inform.sender
                if content_type==self.GIVE_MY_BOX_STRING and giver != other_giver:
                    other_giver_agent = next(a for a in self.model.agents if a.unique_id == inform.sender)
                    other_giver_agent.box_reserved = False


        self.informs.clear()

    def step(self):
        # Process each message type separately (like GAMA reflexes)
        self.read_requests()
        self.read_agrees()
        self.read_refuses()
        self.read_informs()
        super().step()

    def _send(self, to_id, performative, content):
        # todo: no battery check in send?
        """send a message to another agent"""
        try:
            recipient = next(a for a in self.model.agents if a.unique_id==to_id)
            msg = Message(self.unique_id, performative, content)
            # add to a specific list based on performative
            target_list = getattr(recipient, f"{performative}s")
            target_list.append(msg)
            print(f"✓ {performative} sent: {self.unique_id} → {to_id}")
        except StopIteration:
            print(f"✗ Agent {to_id} not found!")