import traci
import time

# Configuration
MIN_GREEN_DURATION = 10        # minimum steps a phase must stay active
STARVATION_THRESHOLD = 30      # max steps a lane can be ignored before forced green
LANE_WEIGHTS = {}              # dynamically filled after starting simulation

# Start SUMO with GUI
sumo_cmd = ["sumo-gui", "-c", "configs/map.sumocfg"]
traci.start(sumo_cmd)

# Assign weights to lanes based on their speed: faster lanes = more priority
for lane_id in traci.lane.getIDList():
    max_speed = traci.lane.getMaxSpeed(lane_id)
    LANE_WEIGHTS[lane_id] = 2.0 if max_speed >= 13.0 else 1.0

# Internal state tracking
tl_last_change = {}
tl_current_phase = {}
lane_starvation = {}

print(f"[DEBUG] Traffic lights found: {traci.trafficlight.getIDList()}")
print(f"[DEBUG] Vehicles in simulation: {traci.vehicle.getIDList()}")
print(f"[DEBUG] Routes loaded: {traci.route.getIDList()}")


def get_traffic_per_lane(tl_id):
    """
    Returns a dictionary mapping each controlled lane of the traffic light
    to the number of vehicles currently present on that lane.
    """
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    return {lane: traci.lane.getLastStepVehicleNumber(lane) for lane in lanes}

def is_all_red(phase):
    """
    Returns True if a phase contains only red or yellow signals.
    """
    return all(signal in ('r', 'y') for signal in phase.state)

def score_phase(phase, lanes, traffic_per_lane):
    """
    Scores a traffic light phase based on the total (weighted) number of vehicles
    that would receive green during this phase.
    """
    score = 0
    has_green = False
    for i, signal in enumerate(phase.state):
        if signal in ('G', 'g') and i < len(lanes):
            has_green = True
            lane = lanes[i]
            weight = LANE_WEIGHTS.get(lane, 1.0)
            score += traffic_per_lane.get(lane, 0) * weight
    return score if has_green else -1  # penalize phases without green

def choose_best_phase(tl_id, traffic_per_lane, step):
    """
    Selects the best phase to apply for a given traffic light based on:
    - lane vehicle counts (with weights)
    - starvation prevention
    - skipping phases with no green
    """
    logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tl_id)[0]
    phases = logic.phases
    lanes = traci.trafficlight.getControlledLanes(tl_id)

    # Starvation prevention: force green for starving lanes
    starvation_lanes = [lane for lane, count in lane_starvation.items()
                        if count >= STARVATION_THRESHOLD and lane in lanes]
    if starvation_lanes:
        for i, phase in enumerate(phases):
            if is_all_red(phase):
                continue
            for j, signal in enumerate(phase.state):
                if signal in ('G', 'g') and j < len(lanes):
                    if lanes[j] in starvation_lanes:
                        return i  # force phase for starving lane

    # Score and select best phase
    scores = []
    for phase in phases:
        if is_all_red(phase):
            scores.append(-1)
        else:
            scores.append(score_phase(phase, lanes, traffic_per_lane))

    return scores.index(max(scores))

# Main simulation loop
step = 0
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    for tl_id in traci.trafficlight.getIDList():
        current_phase = tl_current_phase.get(tl_id, -1)
        last_change = tl_last_change.get(tl_id, -MIN_GREEN_DURATION)

        traffic = get_traffic_per_lane(tl_id)

        # Update starvation counters
        for lane, count in traffic.items():
            if count > 0:
                lane_starvation[lane] = lane_starvation.get(lane, 0) + 1
            else:
                lane_starvation[lane] = 0

        # Decide whether to change phase
        if step - last_change >= MIN_GREEN_DURATION:
            best_phase = choose_best_phase(tl_id, traffic, step)

            if best_phase != current_phase:
                traci.trafficlight.setPhase(tl_id, best_phase)
                tl_last_change[tl_id] = step
                tl_current_phase[tl_id] = best_phase

                print(f"[Step {step}] {tl_id} → Phase {best_phase} | Traffic: {traffic}")

    time.sleep(0.1)
    step += 1

traci.close()
