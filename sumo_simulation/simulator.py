import traci
import time

# Configurações
MIN_GREEN_DURATION = 10
STARVATION_THRESHOLD = 30
LANE_WEIGHTS = {}

# Iniciar SUMO com GUI
sumo_cmd = ["sumo-gui", "-c", "configs_small/map.sumocfg"]
traci.start(sumo_cmd)

# Atribuir pesos às vias (baseado na velocidade máxima)
for lane_id in traci.lane.getIDList():
    max_speed = traci.lane.getMaxSpeed(lane_id)
    LANE_WEIGHTS[lane_id] = 2.0 if max_speed >= 13.0 else 1.0

# ⚠️ Substituir lógica static por lógica actuated para controlo manual
for tl_id in traci.trafficlight.getIDList():
    original_logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tl_id)[0]
    new_logic = traci.trafficlight.Logic(
        programID=original_logic.programID,
        type=0,  # 0 = actuated (manual)
        currentPhaseIndex=0,
        phases=original_logic.phases
    )
    traci.trafficlight.setCompleteRedYellowGreenDefinition(tl_id, new_logic)

# Estado interno
tl_last_change = {}
tl_current_phase = {}
lane_starvation = {}

print(f"[DEBUG] Traffic lights found: {traci.trafficlight.getIDList()}")
print(f"[DEBUG] Vehicles in simulation: {traci.vehicle.getIDList()}")
print(f"[DEBUG] Routes loaded: {traci.route.getIDList()}")

def get_traffic_per_lane(tl_id):
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    return {lane: traci.lane.getLastStepVehicleNumber(lane) for lane in lanes}

def is_all_red(phase):
    return all(signal in ('r', 'y') for signal in phase.state)

def score_phase(phase, lanes, traffic_per_lane):
    score = 0
    has_green = False
    for i, signal in enumerate(phase.state):
        if signal in ('G', 'g') and i < len(lanes):
            has_green = True
            lane = lanes[i]
            weight = LANE_WEIGHTS.get(lane, 1.0)
            score += traffic_per_lane.get(lane, 0) * weight
    return score if has_green else -1

def choose_best_phase(tl_id, traffic_per_lane, step):
    logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tl_id)[0]
    phases = logic.phases
    lanes = traci.trafficlight.getControlledLanes(tl_id)

    # Prevenção de inanição (starvation)
    starvation_lanes = [lane for lane, count in lane_starvation.items()
                        if count >= STARVATION_THRESHOLD and lane in lanes]
    if starvation_lanes:
        for i, phase in enumerate(phases):
            if is_all_red(phase):
                continue
            for j, signal in enumerate(phase.state):
                if signal in ('G', 'g') and j < len(lanes):
                    if lanes[j] in starvation_lanes:
                        return i

    # Scoring normal
    scores = []
    for phase in phases:
        if is_all_red(phase):
            scores.append(-1)
        else:
            scores.append(score_phase(phase, lanes, traffic_per_lane))

    return scores.index(max(scores))

# Loop principal
step = 0
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    for tl_id in traci.trafficlight.getIDList():
        traffic = get_traffic_per_lane(tl_id)

        # 🔴 Desliga semáforo se não há carros em nenhuma entrada
        if sum(traffic.values()) == 0:
            red_state = 'r' * len(traci.trafficlight.getControlledLanes(tl_id))
            traci.trafficlight.setRedYellowGreenState(tl_id, red_state)
            continue

        current_phase = tl_current_phase.get(tl_id, -1)
        last_change = tl_last_change.get(tl_id, -MIN_GREEN_DURATION)

        for lane, count in traffic.items():
            if count > 0:
                lane_starvation[lane] = lane_starvation.get(lane, 0) + 1
            else:
                lane_starvation[lane] = 0

        # Decide se muda a fase
        if step - last_change >= MIN_GREEN_DURATION:
            best_phase = choose_best_phase(tl_id, traffic, step)

            if best_phase != current_phase:
                traci.trafficlight.setPhase(tl_id, best_phase)
                tl_current_phase[tl_id] = best_phase
                tl_last_change[tl_id] = step

        print(f"[Step {step}] {tl_id} → Phase {tl_current_phase.get(tl_id, 'N/A')} | Traffic: {traffic}")

    time.sleep(0.1)
    step += 1

traci.close()
