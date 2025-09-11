#!/usr/bin/env python
# coding: utf-8

import rospy
import math
import tf
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseArray, Pose, PointStamped

ACTIVATION_THRESHOLD = 1.0
FRAME_TARGET = "base_link"   # obstáculos en el frame del robot

class ObstacleDetector:
    def __init__(self):
        self.tf_listener = tf.TransformListener()
        self.pub = rospy.Publisher("/detected_obstacles", PoseArray, queue_size=1)
        rospy.Subscriber("/scan", LaserScan, self.laser_callback)

    def laser_callback(self, msg):
        mitad = len(msg.ranges) // 2
        left_sector = msg.ranges[mitad:]
        right_sector = msg.ranges[:mitad]

        left_avg = self._compute_sector_average(left_sector, msg.angle_min + mitad * msg.angle_increment, msg.angle_increment, msg.header.frame_id)
        right_avg = self._compute_sector_average(right_sector, msg.angle_min, msg.angle_increment, msg.header.frame_id)

        obstacles = PoseArray()
        obstacles.header.stamp = rospy.Time.now()
        obstacles.header.frame_id = FRAME_TARGET

        for avg in [left_avg, right_avg]:
            if avg is not None:
                pose = Pose()
                pose.position.x, pose.position.y = avg
                pose.orientation.w = 1.0
                obstacles.poses.append(pose)

        if obstacles.poses:
            self.pub.publish(obstacles)

    def _compute_sector_average(self, ranges, angle_min, angle_increment, frame_id):
        x_coords, y_coords = [], []

        for i, distance in enumerate(ranges):
            if distance < ACTIVATION_THRESHOLD and not math.isinf(distance) and not math.isnan(distance):
                angle = angle_min + i * angle_increment
                x_coords.append(distance * math.cos(angle))
                y_coords.append(distance * math.sin(angle))

        if not x_coords:
            return None

        # Coordenadas promedio en frame del LiDAR
        x_avg = sum(x_coords) / len(x_coords)
        y_avg = sum(y_coords) / len(y_coords)

        # Transformar a base_link
        try:
            point = PointStamped()
            point.header.stamp = rospy.Time(0)
            point.header.frame_id = frame_id
            point.point.x, point.point.y, point.point.z = x_avg, y_avg, 0.0

            point_in_base = self.tf_listener.transformPoint(FRAME_TARGET, point)
            return point_in_base.point.x, point_in_base.point.y
        except (tf.Exception, tf.LookupException, tf.ConnectivityException):
            return None


if __name__ == "__main__":
    rospy.init_node("obstacle_detector")
    ObstacleDetector()
    rospy.spin()
