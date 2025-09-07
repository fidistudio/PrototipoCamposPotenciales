#!/usr/bin/env python
# coding: utf-8

import rospy
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Pose2D

class TrilaterationNode(object):
    """
    Nodo ROS que recibe distancias a 3 antenas y calcula la posición XY
    usando trilateración, publicando Pose2D (x, y, theta=0).
    """

    def __init__(self):
        rospy.init_node('trilateration_node')

        # Coordenadas físicas de las antenas (metros)
        self.ant_coords = {
            'ANTENA01': {'x': 0.0, 'y': 0.0},
            'ANTENA02': {'x': 1.0, 'y': 0.0},
            'ANTENA03': {'x': 0.5, 'y': 1.0}
        }

        # Lista de antenas en el mismo orden que las distancias
        self.antennas = ['ANTENA01', 'ANTENA02', 'ANTENA03']

        # Suscriptor a las distancias suavizadas
        self.sub = rospy.Subscriber(
            '/ryuw122/distancias',
            Float32MultiArray,
            self.distances_callback
        )

        # Publicador de la posición
        self.pub = rospy.Publisher('/ryuw122/position', Pose2D, queue_size=10)

        rospy.loginfo("Nodo TrilaterationNode listo.")

    # --------------------------
    # Callback de distancias
    # --------------------------
    def distances_callback(self, msg):
        if len(msg.data) != 3:
            rospy.logwarn("Se esperaban 3 distancias, recibidas: {}".format(len(msg.data)))
            return

        # Extraer distancias
        d1, d2, d3 = msg.data

        # Extraer coordenadas
        x1, y1 = self.ant_coords[self.antennas[0]]['x'], self.ant_coords[self.antennas[0]]['y']
        x2, y2 = self.ant_coords[self.antennas[1]]['x'], self.ant_coords[self.antennas[1]]['y']
        x3, y3 = self.ant_coords[self.antennas[2]]['x'], self.ant_coords[self.antennas[2]]['y']

        # Trilateración
        pos = self.trilaterate(x1, y1, d1, x2, y2, d2, x3, y3, d3)

        # Publicar como Pose2D
        pose_msg = Pose2D()
        pose_msg.x = pos['x']
        pose_msg.y = pos['y']
        pose_msg.theta = 0.0  # sin orientación
        self.pub.publish(pose_msg)

    # --------------------------
    # Función de trilateración
    # --------------------------
    def trilaterate(self, x1, y1, r1, x2, y2, r2, x3, y3, r3):
        """
        Calcula posición XY usando trilateración con 3 antenas.
        Devuelve un diccionario {'x': X, 'y': Y}
        """
        # Radios al cuadrado
        r1_sq = r1 * r1
        r2_sq = r2 * r2
        r3_sq = r3 * r3

        # Sistema de ecuaciones
        A1 = 2 * (x2 - x1)
        B1 = 2 * (y2 - y1)
        C1 = r1_sq - r2_sq - x1*x1 + x2*x2 - y1*y1 + y2*y2

        A2 = 2 * (x3 - x1)
        B2 = 2 * (y3 - y1)
        C2 = r1_sq - r3_sq - x1*x1 + x3*x3 - y1*y1 + y3*y3

        # Determinante
        D = A1 * B2 - A2 * B1
        if D == 0:
            rospy.logwarn("Antenas mal posicionadas o colineales. Posición (0,0).")
            return {'x': 0.0, 'y': 0.0}

        # Regla de Cramer
        x = (C1 * B2 - C2 * B1) / D
        y = (A1 * C2 - A2 * C1) / D

        return {'x': x, 'y': y}

    # --------------------------
    # Loop principal
    # --------------------------
    def spin(self):
        rospy.spin()


if __name__ == "__main__":
    try:
        node = TrilaterationNode()
        node.spin()
    except rospy.ROSInterruptException:
        pass
