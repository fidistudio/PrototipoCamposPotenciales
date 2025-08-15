#!/usr/bin/env python
# encoding: utf-8

import rospy 
from sensor_msgs.msg import LaserScan

def callback(mensaje): 
    print(mensaje.ranges)
    print("\n")
    
def nodo():
    rospy.init_node('nodo_detect_obstacle')
    scan_sub = rospy.Subscriber('/scan', LaserScan, callback)
    rospy.spin()
    
if __name__ == '__main__': 
    try:
        nodo()
    except rospy.ROSInterruptException: 
        pass
        
