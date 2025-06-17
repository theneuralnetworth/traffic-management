import traci

class VehicleAgent:
    def __init__(self, veh_id):
        self.id = veh_id
        self.total_wait_time = 0
        self.current_wait = 0
        self.lane = None
        self.stopped = False

    def update(self, tls_agents):
        # Verifica velocidade atual
        speed = traci.vehicle.getSpeed(self.id)
        lane_id = traci.vehicle.getLaneID(self.id)
        self.lane = lane_id

        if speed < 0.1:
            self.current_wait += 1  # segundos parados
            self.stopped = True
        else:
            self.total_wait_time += self.current_wait
            self.current_wait = 0
            self.stopped = False

        # Obter próximo semáforo
        tls_info = traci.vehicle.getNextTLS(self.id)

        if tls_info:
            tls_id, dist, light_state, lane = tls_info[0]
            if dist < 20 and self.stopped:  # próximo do semáforo
                # Notificar semáforo
                if tls_id in tls_agents:
                    tls_agents[tls_id].notify_waiting(self.id, lane_id, self.current_wait)

    def get_total_wait_time(self):
        return self.total_wait_time + self.current_wait
