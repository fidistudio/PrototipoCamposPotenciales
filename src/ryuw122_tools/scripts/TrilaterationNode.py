#!/usr/bin/env python
# coding: utf-8

import rospy
import math
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Pose2D
from collections import namedtuple

# Definición de una antena como namedtuple
Antenna = namedtuple("Antenna", ["x", "y", "z"])


class TrilaterationNode(object):
    """
    Nodo ROS que recibe distancias a 3 antenas y calcula la posición XY
    usando trilateración. Publica la posición como Pose2D.
    """

    def __init__(self):
        rospy.init_node("trilateration_node")

        # Antenas en el espacio (coordenadas en metros)
        self.antennas = {
            "ANTENA01": Antenna(0.0, 0.0, 0.5),
            "ANTENA02": Antenna(1.0, 0.0, 1.0),
            "ANTENA03": Antenna(0.5, 1.0, 0.2),
        }
        self.antenna_order = ["ANTENA01", "ANTENA02", "ANTENA03"]

        self.subscriber = rospy.Subscriber(
            "/ryuw122/distancias",
            Float32MultiArray,
            self.handle_distances,
        )
        self.publisher = rospy.Publisher("/ryuw122/position", Pose2D, queue_size=10)

        rospy.loginfo("Nodo TrilaterationNode inicializado.")

    def handle_distances(self, msg):
        """Procesa las distancias recibidas y publica la posición calculada."""
        if len(msg.data) != 3:
            rospy.logwarn("Se esperaban 3 distancias, recibidas: {}".format(len(msg.data)))
            return

        projected_distances = self._project_distances(msg.data)
        pose = self._compute_pose(projected_distances)
        self.publisher.publish(pose)

    def _project_distances(self, distances):
        """Proyecta las distancias medidas al plano XY."""
        result = []
        for d, ant_name in zip(distances, self.antenna_order):
            antenna = self.antennas[ant_name]
            if d < antenna.z:
                rospy.logwarn(
                    "Distancia {:.2f} menor que altura {:.2f}, inválida.".format(d, antenna.z)
                )
                result.append(0.0)
            else:
                d_proj = math.sqrt(d**2 - antenna.z**2)
                result.append(d_proj)
        return result

    def _compute_pose(self, distances):
        """Ejecuta la trilateración y devuelve un Pose2D."""
        d1, d2, d3 = distances
        a1, a2, a3 = (self.antennas[name] for name in self.antenna_order)

        x, y = self._trilaterate(
            a1.x, a1.y, d1,
            a2.x, a2.y, d2,
            a3.x, a3.y, d3
        )
        pose = Pose2D()
        pose.x = x
        pose.y = y
        pose.theta = 0.0
        return pose

    def _trilaterate(self, x1, y1, r1, x2, y2, r2, x3, y3, r3):
        """Calcula la posición XY usando trilateración con 3 antenas."""
        r1_sq, r2_sq, r3_sq = r1**2, r2**2, r3**2

        A1 = 2 * (x2 - x1)
        B1 = 2 * (y2 - y1)
        C1 = r1_sq - r2_sq - x1**2 + x2**2 - y1**2 + y2**2

        A2 = 2 * (x3 - x1)
        B2 = 2 * (y3 - y1)
        C2 = r1_sq - r3_sq - x1**2 + x3**2 - y1**2 + y3**2

        D = A1 * B2 - A2 * B1
        if D == 0:
            rospy.logwarn("Antenas mal posicionadas o colineales. Retornando (0,0).")
            return 0.0, 0.0

        x = (C1 * B2 - C2 * B1) / D
        y = (A1 * C2 - A2 * C1) / D
        return x, y

    def spin(self):
        rospy.spin()


if __name__ == "__main__":
    try:
        node = TrilaterationNode()
        node.spin()
    except rospy.ROSInterruptException:
        pass
