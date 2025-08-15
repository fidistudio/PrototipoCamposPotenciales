#!/usr/bin/env python
# encoding: utf-8

import rospy
import math
from sensor_msgs.msg import LaserScan

# Constantes
UmbralActivacion = 1.0  # metros

def callback(mensaje):
    mitad = len(mensaje.ranges) // 2

    X_izq, Y_izq = [], []
    X_der, Y_der = [], []

    for i in range(len(mensaje.ranges)):
        dist = mensaje.ranges[i]
        if dist < UmbralActivacion and not math.isinf(dist) and not math.isnan(dist):
            ang = mensaje.angle_min + i * mensaje.angle_increment
            x = dist * math.cos(ang)
            y = dist * math.sin(ang)

            if i < mitad:
                X_izq.append(x)
                Y_izq.append(y)
            else:
                X_der.append(x)
                Y_der.append(y)

    if X_izq and Y_izq:
        x_izq_prom = sum(X_izq) / len(X_izq)
        y_izq_prom = sum(Y_izq) / len(Y_izq)
    else:
        x_izq_prom = y_izq_prom = None

    if X_der and Y_der:
        x_der_prom = sum(X_der) / len(X_der)
        y_der_prom = sum(Y_der) / len(Y_der)
    else:
        x_der_prom = y_der_prom = None

    if x_izq_prom is not None and y_izq_prom is not None:
        print("Promedio sector derecho: (%.3f, %.3f)" % (x_izq_prom*100, y_izq_prom*100))
    else:
        print("No hay datos válidos en sector derecho")

    if x_der_prom is not None and y_der_prom is not None:
        print("Promedio sector izquierdo: (%.3f, %.3f)" % (x_der_prom*100, y_der_prom*100))
    else:
        print("No hay datos válidos en sector izquierdo")

    print("--------------\n")


def nodo():
    rospy.init_node('nodo_detect_obstacle')
    scan_sub = rospy.Subscriber('/scan', LaserScan, callback)
    rospy.spin()



if __name__ == '__main__':
    try:
        nodo()
    except rospy.ROSInterruptException:
        passf
