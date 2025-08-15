#!/usr/bin/env python
# encoding: utf-8

import rospy
from sensor_msgs.msg import LaserScan

# Constantes
UmbralActivacion = 0.5  # metros

def callback(mensaje):
    mitad = len(mensaje.ranges) // 2

    print("Obstáculos cerca en sectores:")

    print("Sector derecho:")
    for i in range(mitad):
        dist = mensaje.ranges[i]
        if dist < UmbralActivacion:
            ang = mensaje.angle_min + i * mensaje.angle_increment
            print("[%d] Distancia: %.3f m, Ángulo: %.3f rad (%.1f deg)" % (i, dist, ang, ang*180/3.1416))

    print("\nSector izquierdo:")
    for i in range(mitad, len(mensaje.ranges)):
        dist = mensaje.ranges[i]
        if dist < UmbralActivacion:
            ang = mensaje.angle_min + i * mensaje.angle_increment
            print("[%d] Distancia: %.3f m, Ángulo: %.3f rad (%.1f deg)" % (i, dist, ang, ang*180/3.1416))

    print("--------------\n")



def nodo():
    rospy.init_node('nodo_detect_obstacle')
    scan_sub = rospy.Subscriber('/scan', LaserScan, callback)
    rospy.spin()

if __name__ == '__main__':
    try:
        nodo()
    except rospy.ROSInterruptException:
        pass
