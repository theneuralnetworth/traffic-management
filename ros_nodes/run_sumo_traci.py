import os
import sys
import traci

def setup_sumo_path():
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("Erro: Por favor, defina a variável de ambiente 'SUMO_HOME'.")

def get_vehicles_at_intersection(junction_id):
    vehicle_count = 0
    incoming_lanes = traci.junction.getIncomingLanes(junction_id)
    
    for lane_id in incoming_lanes:
        vehicle_count += traci.lane.getLastStepVehicleNumber(lane_id)
        
    return vehicle_count

def run_simulation():
    sumo_binary = "sumo-gui"
    config_path = "intersection.sumocfg"
    
    sumo_cmd = [sumo_binary, "-c", config_path]

    print(f"A iniciar o SUMO com o ficheiro: {config_path}")
    traci.start(sumo_cmd)
    
    intersection_to_monitor = "intersection_1"
    step = 0
    
    print("A iniciar o loop da simulação...")
    while step < 1000:
        traci.simulationStep()
        
        if step % 5 == 0:
            try:
                num_vehicles = get_vehicles_at_intersection(intersection_to_monitor)
                print(f"Passo {step}: Veículos em '{intersection_to_monitor}' = {num_vehicles}")
            
            except traci.TraCIException:
                print(f"Erro: Intersecção '{intersection_to_monitor}' não encontrada. Verifique o seu ficheiro .net.xml.")
                break
        
        step += 1

    traci.close()
    print("Simulação concluída.")

if __name__ == "__main__":
    setup_sumo_path()
    run_simulation() 