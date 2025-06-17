import traci

class TrafficLightAgent:
    def __init__(self, tls_id):
        self.id = tls_id
        self.in_lanes = traci.trafficlight.getControlledLanes(tls_id)
        self.out_lanes = self._get_outgoing_lanes()
        self.waiting_vehicles = {}  # {lane_id: [vehicle_ids]}
    
    def _get_outgoing_lanes(self):
        out_lanes = set()
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.id)[0]
        for link in logic.getAllLinks():
            for conn in link:
                out_lanes.add(conn[1])  # conn[1] is outgoing lane
        return list(out_lanes)

    def notify_waiting(self, vehicle_id, lane_id, waiting_time):
        if lane_id not in self.waiting_vehicles:
            self.waiting_vehicles[lane_id] = set()
        self.waiting_vehicles[lane_id].add(vehicle_id)

    def compute_pressure(self, phase_lanes):
        pressure = 0
        for lane in phase_lanes:
            in_count = traci.lane.getLastStepVehicleNumber(lane)
            out_count = sum([traci.lane.getLastStepVehicleNumber(out) for out in self.out_lanes if out != lane])
            pressure += in_count - out_count
        return pressure

    def update(self):
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(self.id)[0]
        phases = logic.getPhases()
        
        max_pressure = -float('inf')
        best_phase_index = 0

        for i, phase in enumerate(phases):
            controlled_lanes = logic.getControlledLanes(i)
            pressure = self.compute_pressure(controlled_lanes)
            if pressure > max_pressure:
                max_pressure = pressure
                best_phase_index = i

        # Change to the best phase
        traci.trafficlight.setPhase(self.id, best_phase_index)
        self.waiting_vehicles.clear()
