#!/usr/bin/env python
# encoding: utf-8

import rospy
import math
from sensor_msgs.msg import LaserScan

ACTIVATION_THRESHOLD = 1.0  # metros

def compute_sector_average(ranges, angle_min, angle_increment):
    x_coords, y_coords = [], []

    for i, distance in enumerate(ranges):
        if distance < ACTIVATION_THRESHOLD and not math.isinf(distance) and not math.isnan(distance):
            angle = angle_min + i * angle_increment
            x_coords.append(distance * math.cos(angle))
            y_coords.append(distance * math.sin(angle))

    if not x_coords:
        return None

    x_avg = sum(x_coords) / len(x_coords)
    y_avg = sum(y_coords) / len(y_coords)
    return x_avg, y_avg


def print_sector_average(sector_name, avg_coords):
    if avg_coords is None:
        print("No hay datos válidos en sector {}".format(sector_name))
    else:
        x, y = avg_coords
        print("Promedio sector {}: ({:.3f}, {:.3f})".format(sector_name, x*100, y*100))


def laser_callback(msg):
    mitad = len(msg.ranges) // 2

    left_sector = msg.ranges[mitad:]
    right_sector = msg.ranges[:mitad]

    left_avg = compute_sector_average(left_sector, msg.angle_min, msg.angle_increment)
    right_avg = compute_sector_average(right_sector, msg.angle_min + mitad*msg.angle_increment, msg.angle_increment)

    print_sector_average("izquierdo", left_avg)
    print_sector_average("derecho", right_avg)
    print("--------------\n")


def main():
    rospy.init_node('nodo_detect_obstacle')
    rospy.Subscriber('/scan', LaserScan, laser_callback)
    rospy.spin()


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
