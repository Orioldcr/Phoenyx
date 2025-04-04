import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class FrontDistanceNode(Node):
    def __init__(self):
        super().__init__('front_distance_node')
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_callback,
            10
        )
        self.subscription  # Evita que el garbage collector elimine la suscripción

    def laser_callback(self, msg):
        # Obtiene el índice central del array de distancias
        num_readings = len(msg.ranges)
        front_index = num_readings // 2  # Asumiendo que el escaneo es simétrico
        front_distance = msg.ranges[front_index]

        # Imprime la distancia frontal
        self.get_logger().info(f'Distancia frontal: {front_distance:.2f} metros')

        # Umbral de advertencia
        warning_threshold = 0.5  # 50 cm
        if front_distance < warning_threshold:
            self.get_logger().warn('¡Obstáculo muy cerca!')


def main(args=None):
    rclpy.init(args=args)
    node = FrontDistanceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
