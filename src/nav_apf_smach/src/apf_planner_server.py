#!/usr/bin/env python
# coding: utf-8

import rospy
import tf
import numpy as np
import actionlib

from geometry_msgs.msg import PoseStamped, Vector3
from nav_apf_smach.msg import NextWaypointAction, NextWaypointResult, NextWaypointFeedback
from geometry_msgs.msg import PoseArray

# ===========================
# Constantes
# ===========================
STEP_SIZE = 0.5
GOAL_TOLERANCE = 0.15
FRAME_BASE = 'base_link'

ATTRACTIVE_GAIN = 1.0
REPULSIVE_GAIN = 2.0
REPULSIVE_DISTANCE = 5.0


# ===========================
# Funciones de cálculo APF
# ===========================
def attractive_force(current, goal):
    vector = goal - current
    distance = np.linalg.norm(vector)
    return ATTRACTIVE_GAIN * vector if distance < 10.0 else np.zeros(2)


def repulsive_force(current, obstacle):
    vector = current - obstacle
    distance = np.linalg.norm(vector)
    if 0 < distance < REPULSIVE_DISTANCE:
        return -REPULSIVE_GAIN * ((1.0/distance - 1.0/REPULSIVE_DISTANCE) / (distance**2)) * (vector / distance)
    return np.zeros(2)


def compute_total_force(current, goal, obstacles):
    f_attr = attractive_force(current, goal)
    f_rep = np.sum([repulsive_force(current, obs) for obs in obstacles], axis=0) if obstacles else np.zeros(2)
    return f_attr, f_rep, f_attr + f_rep


def compute_next_waypoint(current_pos, goal_pos, obstacles):
    f_attr, f_rep, f_total = compute_total_force(current_pos, goal_pos, obstacles)
    magnitude = np.linalg.norm(f_total)
    if magnitude > 0:
        next_pos = current_pos + (STEP_SIZE * f_total / magnitude)
    else:
        next_pos = current_pos.copy()

    waypoint = PoseStamped()
    waypoint.header.stamp = rospy.Time.now()
    waypoint.header.frame_id = FRAME_BASE
    waypoint.pose.position.x = next_pos[0]
    waypoint.pose.position.y = next_pos[1]
    waypoint.pose.orientation.w = 1.0

    return waypoint, f_attr, f_rep, f_total


# ===========================
# Servidor de acción APF
# ===========================
class APFPlannerServer:
    def __init__(self):
        self.tf_listener = tf.TransformListener()
        self.obstacles_base = []

        rospy.Subscriber("/detected_obstacles", PoseArray, self._obstacles_cb)

        self.server = actionlib.SimpleActionServer(
            'apf_planner',
            NextWaypointAction,
            execute_cb=self._execute_cb,
            auto_start=False
        )
        self.server.start()
        rospy.loginfo("[APF] Planner server listo.")

    # -------------------------------
    # Callbacks
    # -------------------------------
    def _obstacles_cb(self, msg):
        self.obstacles_base = [np.array([pose.position.x, pose.position.y]) for pose in msg.poses]

    def _execute_cb(self, goal):
        current_pos = np.array([0.0, 0.0])
        goal_in_base = self._transform_goal_to_base(goal.target)

        if goal_in_base is None:
            rospy.logerr("[APF] No se pudo transformar el goal a base_link")
            self.server.set_aborted()
            return

        waypoint, f_attr, f_rep, f_total = compute_next_waypoint(
            current_pos, goal_in_base, self.obstacles_base
        )

        distance_to_goal = np.linalg.norm(goal_in_base - current_pos)

        self._publish_feedback(goal.target, f_attr, f_rep, distance_to_goal)
        self._set_result(waypoint, distance_to_goal)

    # -------------------------------
    # Métodos auxiliares
    # -------------------------------
    def _transform_goal_to_base(self, goal_pose):
        try:
            transformed = self.tf_listener.transformPose(FRAME_BASE, goal_pose)
            return np.array([transformed.pose.position.x, transformed.pose.position.y])
        except (tf.Exception, tf.LookupException, tf.ConnectivityException) as e:
            rospy.logerr("[APF] Error transformando goal: %s", e)
            return None

    def _publish_feedback(self, goal_pose, f_attr, f_rep, distance):
        feedback = NextWaypointFeedback()
        feedback.remaining_distance = distance
        feedback.f_attr = Vector3(f_attr[0], f_attr[1], 0.0)
        feedback.f_rep = Vector3(f_rep[0], f_rep[1], 0.0)

        # Construir debug_info
        debug_str = "[APF DEBUG] Goal in base_link: x={:.2f}, y={:.2f}; Obstacles: ".format(
            goal_pose.pose.position.x, goal_pose.pose.position.y
        )
        obstacles_str = ", ".join(
            ["({:.2f}, {:.2f})".format(obs[0], obs[1]) for obs in self.obstacles_base]
        )
        feedback.debug_info = debug_str + obstacles_str

        self.server.publish_feedback(feedback)

    def _set_result(self, waypoint, distance_to_goal):
        result = NextWaypointResult()
        result.next_waypoint = waypoint
        result.goal_reached = distance_to_goal < GOAL_TOLERANCE
        self.server.set_succeeded(result)
        rospy.loginfo("[APF] Resultado enviado: goal_reached=%s, waypoint=(%.2f, %.2f)",
                      result.goal_reached, waypoint.pose.position.x, waypoint.pose.position.y)


# ===========================
# Nodo principal
# ===========================
if __name__ == '__main__':
    rospy.init_node('apf_planner_server')
    APFPlannerServer()
    rospy.spin()
