import traci
import random


def get_random_sumo_position(connection) -> tuple[float, float]:
    edges = [e for e in connection.edge.getIDList() if not e.startswith(":")]
    edge_id = random.choice(edges)

    edge_lanes = connection.edge.getLaneNumber(edge_id)
    lane_index = random.randint(0, edge_lanes - 1)
    lane_position = random.uniform(
        0, connection.lane.getLength(edge_id + f"_{lane_index}")
    )
    x, y = connection.simulation.convert2D(edge_id, lane_position, lane_index)

    return x, y


if __name__ == "__main__":
    conn = traci.connect()

    for i in range(10):
        location = get_random_sumo_position(conn)

        conn.poi.add(
            poiID=f"random_location_{i}",
            x=location[0],
            y=location[1],
            color=(255, 0, 0, 255),
        )
