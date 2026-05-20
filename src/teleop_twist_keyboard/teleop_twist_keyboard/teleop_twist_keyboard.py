#!/usr/bin/env python3

import select
import sys
import termios
import tty
import time

import rclpy
from rclpy.subscription import Subscription
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState


MOVE_BINDINGS = {
    'i': (1, 0, 0, 0),
    'o': (1, 0, 0, -1),
    'j': (0, 0, 0, 1),
    'l': (0, 0, 0, -1),
    'u': (1, 0, 0, 1),
    ',': (-1, 0, 0, 0),
    '.': (-1, 0, 0, 1),
    'm': (-1, 0, 0, -1),
    'O': (1, -1, 0, 0),
    'I': (1, 0, 0, 0),
    'J': (0, 1, 0, 0),
    'L': (0, -1, 0, 0),
    'U': (1, 1, 0, 0),
    '<': (-1, 0, 0, 0),
    '>': (-1, -1, 0, 0),
    'M': (-1, 1, 0, 0),
    't': (0, 0, 1, 0),
    'b': (0, 0, -1, 0),
}

SPEED_BINDINGS = {
    'q': (1.1, 1.1),
    'z': (0.9, 0.9),
    'w': (1.1, 1.0),
    'x': (0.9, 1.0),
    'e': (1.0, 1.1),
    'c': (1.0, 0.9),
}

ARM_BINDINGS = {
    'r': -1,   # gira hacia arriba
    'f': 1,    # gira hacia abajo
}

HELP = """
Control Your Robot
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

For holonomic mode (strafing), hold shift:
---------------------------
   U    I    O
   J    K    L
   M    <    >

t : up (+z)
b : down (-z)

q/z : increase/decrease all speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

k : force stop

Arm control:
Brazo robotico:
r : elbow up
f : elbow down

CTRL-C to quit
"""


def _get_key(settings, timeout=0.1):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def _vels(speed, turn):
    return f'currently:\tspeed {speed:.3f}\tturn {turn:.3f}'


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


class ArmStateTracker:
    def __init__(self):
        self.elbow_position = 0.0
    
    def joint_state_callback(self, msg):
        if 'elbow_joint' in msg.name:
            idx = msg.name.index('elbow_joint')
            self.elbow_position = msg.position[idx]



def main():
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init(args=sys.argv)
    node = rclpy.create_node('teleop_twist_keyboard')

    cmd_vel_topic = node.declare_parameter('cmd_vel_topic', '/cmd_vel').value
    elbow_topic = node.declare_parameter('elbow_topic', '/elbow_joint_cmd').value
    shoulder_topic = node.declare_parameter('shoulder_topic', '/shoulder_pan_cmd').value

    speed = float(node.declare_parameter('speed', 0.5).value)
    turn = float(node.declare_parameter('turn', 1.0).value)

    arm_step = float(node.declare_parameter('arm_step', 0.1).value)
    arm_min = float(node.declare_parameter('arm_min', -1.57).value)
    arm_max = float(node.declare_parameter('arm_max', 0.0).value)
    arm_position = float(node.declare_parameter('arm_initial', 0.0).value)

    twist_pub = node.create_publisher(Twist, cmd_vel_topic, 10)
    elbow_pub = node.create_publisher(Float64, elbow_topic, 10)
    shoulder_pub = node.create_publisher(Float64, shoulder_topic, 10)
    
    # Tracker para leer posición real del joint desde Gazebo
    arm_state = ArmStateTracker()
    joint_state_sub = node.create_subscription(JointState, '/joint_states', arm_state.joint_state_callback, 10)

    # Estado de movimiento persistente
    x = 0
    y = 0
    z = 0
    th = 0
    arm_direction = 0  # -1: gira arriba, 0: parado, 1: gira abajo

    status = 0
    last_key_time = time.time()

    try:
        print(HELP)
        print(_vels(speed, turn))

        # Enviar posición inicial del brazo
        initial_arm = Float64()
        initial_arm.data = _clamp(arm_position, arm_min, arm_max)
        arm_position = initial_arm.data
        elbow_pub.publish(initial_arm)
        
        shoulder_zero = Float64()
        shoulder_zero.data = 0.0
        shoulder_pub.publish(shoulder_zero)

        while True:
            key = _get_key(settings, timeout=0.05)
            current_time = time.time()
            
            # Usar posición real del joint desde Gazebo
            arm_position = arm_state.elbow_position

            if key in MOVE_BINDINGS:
                x, y, z, th = MOVE_BINDINGS[key]
                last_key_time = current_time
            elif key in SPEED_BINDINGS:
                speed *= SPEED_BINDINGS[key][0]
                turn *= SPEED_BINDINGS[key][1]
                print(_vels(speed, turn))
                status += 1
                if status == 14:
                    print(HELP)
                    status = 0
            elif key == 'k':
                x = 0
                y = 0
                z = 0
                th = 0
                arm_direction = 0
                last_key_time = current_time
            elif key in ARM_BINDINGS:
                arm_direction = ARM_BINDINGS[key]
                last_key_time = current_time
            elif key == '\x03':
                break
            else:
                # Sin tecla presionada en este ciclo
                if key == '' and (current_time - last_key_time) > 0.3:
                    # Detener movimiento después de ~300ms sin teclas
                    x = 0
                    y = 0
                    z = 0
                    th = 0
                    arm_direction = 0

            # Calcular posición del brazo basada en dirección continua
            target_pos = arm_position + (arm_direction * arm_step)

            # Publicar comando del vehículo
            twist = Twist()
            twist.linear.x = x * speed
            twist.linear.y = y * speed
            twist.linear.z = z * speed
            twist.angular.x = 0.0
            twist.angular.y = 0.0
            twist.angular.z = th * turn
            twist_pub.publish(twist)

            # Publicar comando del brazo
            elbow_msg = Float64()
            elbow_msg.data = target_pos
            elbow_pub.publish(elbow_msg)
            
            # Mantener hombro bloqueado en 0 (eje Z fijo)
            shoulder_msg = Float64()
            shoulder_msg.data = 0.0
            shoulder_pub.publish(shoulder_msg)

    finally:
        # Detener vehículo
        stop = Twist()
        stop.linear.x = 0.0
        stop.linear.y = 0.0
        stop.linear.z = 0.0
        stop.angular.x = 0.0
        stop.angular.y = 0.0
        stop.angular.z = 0.0
        twist_pub.publish(stop)

        # Parar brazo
        stop_arm = Float64()
        stop_arm.data = arm_state.elbow_position
        elbow_pub.publish(stop_arm)
        
        # Hombro en 0
        stop_shoulder = Float64()
        stop_shoulder.data = 0.0
        shoulder_pub.publish(stop_shoulder)

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
