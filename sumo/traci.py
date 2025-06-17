import traci

# Caminho para o teu ficheiro .sumocfg
sumo_cfg = "isep.sumocfg"

# Lança o SUMO em modo GUI (ou "sumo" para headless)
sumo_cmd = ["sumo-gui", "-c", sumo_cfg]

# Inicia a simulação com o TraCI
traci.start(sumo_cmd)

# Simula 100 passos
for step in range(100):
    traci.simulationStep()

    # Exemplo: listar IDs de veículos
    vehicle_ids = traci.vehicle.getIDList()
    print(f"Step {step}: veículos ativos → {vehicle_ids}")

    # Exemplo: estado de semáforo (se existir)
    if traci.trafficlight.getIDList():
        light_id = traci.trafficlight.getIDList()[0]
        phase = traci.trafficlight.getPhase(light_id)
        print(f"Semáforo {light_id} na fase {phase}")

# Termina a simulação
traci.close()
