import math
from typing import TYPE_CHECKING

from ..flight_state import FlightState
from .handler import FlightStateHandler

if TYPE_CHECKING:
    from ..flight_test_node import FlightTestNode


class StoppingHandler(FlightStateHandler):
    def handle(self, node: "FlightTestNode") -> None:
        node.send_velocity(0.0, 0.0)
        elapsed = (
            node.get_clock().now() - node.stop_started_at
        ).nanoseconds / 1e9
        if elapsed < node.STOP_DURATION:
            return

        pos = node.position()
        error = math.hypot(
            pos[0] - node.target_xy[0], pos[1] - node.target_xy[1]
        )
        node.get_logger().info("=== RESULT BEFORE LANDING ===")
        node.get_logger().info(
            f"Start:  ({node.start_xy[0]:.3f}, {node.start_xy[1]:.3f})"
        )
        node.get_logger().info(
            f"Target: ({node.target_xy[0]:.3f}, {node.target_xy[1]:.3f})"
        )
        node.get_logger().info(f"Actual: ({pos[0]:.3f}, {pos[1]:.3f})")
        node.get_logger().info(f"Error:  {error:.3f} m")
        node.state = FlightState.LANDING
