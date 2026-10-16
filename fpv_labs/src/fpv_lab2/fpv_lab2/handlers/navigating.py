import math
from typing import TYPE_CHECKING

from ..flight_state import FlightState
from .handler import FlightStateHandler

if TYPE_CHECKING:
    from ..flight_test_node import FlightTestNode


class NavigatingHandler(FlightStateHandler):
    def handle(self, node: "FlightTestNode") -> None:
        if node.status is None or not node.status.armed:
            node.fail("Drone disarmed unexpectedly during navigation")
            return
        pos = node.position()
        if pos is None:
            return

        ex = node.target_xy[0] - pos[0]
        ey = node.target_xy[1] - pos[1]
        dist = math.hypot(ex, ey)

        if dist <= node.TARGET_TOLERANCE:
            node.send_velocity(0.0, 0.0)
            node.reached_count += 1
            if node.reached_count >= node.REACHED_CYCLES:
                node.get_logger().info(
                    f"Target reached, distance {dist:.3f} m, stopping"
                )
                node.stop_started_at = node.get_clock().now()
                node.state = FlightState.STOPPING
            return

        node.reached_count = 0
        speed = min(node.MAX_SPEED, max(node.MIN_SPEED, node.SPEED_GAIN * dist))
        node.send_velocity(speed * ex / dist, speed * ey / dist)
        node.get_logger().info(
            f"pos=({pos[0]:.2f}, {pos[1]:.2f}) dist={dist:.2f} m "
            f"speed={speed:.2f} m/s",
            throttle_duration_sec=1.0,
        )
