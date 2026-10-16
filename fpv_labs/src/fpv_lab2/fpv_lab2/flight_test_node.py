from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_srvs.srv import Trigger
from ardupilot_msgs.msg import Status
from ardupilot_msgs.srv import ArmMotors, ModeSwitch, Takeoff

from .flight_state import FlightState
from .handlers import HANDLERS


class FlightTestNode(Node):
    GUIDED_MODE = 4
    LAND_MODE = 9
    TAKEOFF_ALTITUDE = 10.0
    HOVER_DURATION = 10.0

    # Navigation settings
    TARGET_TOLERANCE = 0.25   # m
    MAX_SPEED = 1.0           # m/s
    MIN_SPEED = 0.15          # m/s
    SPEED_GAIN = 0.6          # (m/s) per metre of remaining distance
    REACHED_CYCLES = 5        # consecutive cycles inside tolerance
    STOP_DURATION = 10.0      # s of zero velocity before landing

    def __init__(self):
        super().__init__("flight_test")
        self.declare_parameter("dx", 4.0)
        self.declare_parameter("dy", 0.0)
        self.dx = float(self.get_parameter("dx").value)
        self.dy = float(self.get_parameter("dy").value)

        self.state = FlightState.WAITING_FOR_SYSTEM
        self.request_in_progress = False
        self.status = None
        self.odometry = None
        self.hover_started_at = None
        self.start_xy = None
        self.target_xy = None
        self.reached_count = 0
        self.stop_started_at = None
        self._handlers = HANDLERS

        self.status_subscription = self.create_subscription(
            Status, "/ap/v1/status", self.status_callback, 10
        )
        self.odometry_subscription = self.create_subscription(
            Odometry, "/odometry", self.odometry_callback, 10
        )
        self.cmd_vel_publisher = self.create_publisher(
            TwistStamped, "/ap/v1/cmd_vel", 10
        )

        self.prearm_client = self.create_client(Trigger, "/ap/v1/prearm_check")
        self.mode_client = self.create_client(ModeSwitch, "/ap/v1/mode_switch")
        self.arm_client = self.create_client(ArmMotors, "/ap/v1/arm_motors")
        self.takeoff_client = self.create_client(
            Takeoff, "/ap/v1/experimental/takeoff"
        )

        self.timer = self.create_timer(0.2, self.control_loop)
        self.get_logger().info("Flight test node started")
        self.get_logger().info(f"Variant offsets: dx={self.dx}, dy={self.dy}")
        self.get_logger().info("Waiting for ArduPilot and ROS services...")

    def status_callback(self, message):
        self.status = message

    def odometry_callback(self, message):
        self.odometry = message
        if self.start_xy is None:
            p = message.pose.pose.position
            self.start_xy = (p.x, p.y)
            self.target_xy = (p.x - self.dx, p.y - self.dy)
            self.get_logger().info(
                f"Start position: ({p.x:.2f}, {p.y:.2f}); "
                f"target: ({self.target_xy[0]:.2f}, {self.target_xy[1]:.2f})"
            )

    def position(self):
        if self.odometry is None:
            return None
        p = self.odometry.pose.pose.position
        return (p.x, p.y)

    def send_velocity(self, vx, vy, vz=0.0):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.twist.linear.x = float(vx)
        msg.twist.linear.y = float(vy)
        msg.twist.linear.z = float(vz)
        self.cmd_vel_publisher.publish(msg)

    def services_ready(self):
        return (
            self.prearm_client.service_is_ready()
            and self.mode_client.service_is_ready()
            and self.arm_client.service_is_ready()
            and self.takeoff_client.service_is_ready()
        )

    def control_loop(self):
        handler = self._handlers.get(self.state)
        if handler is not None:
            handler.handle(self)

    def call_mode_switch(self, mode, callback):
        self.request_in_progress = True
        request = ModeSwitch.Request()
        request.mode = mode
        future = self.mode_client.call_async(request)
        future.add_done_callback(callback)
        self.get_logger().info(f"Requesting flight mode {mode}")

    def fail(self, message):
        self.get_logger().error(message)
        self.state = FlightState.ERROR
