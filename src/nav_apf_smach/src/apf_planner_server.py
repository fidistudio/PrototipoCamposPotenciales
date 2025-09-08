#!/usr/bin/env python
# coding: utf-8

import rospy
import tf
import numpy as np
from geometry_msgs.msg import PoseStamped, Vector3
import actionlib
from nav_apf_smach.msg import NextWaypointAction, NextWaypointResult, NextWaypointFeedback

# ===========================
# Constantes
# ===========================
STEP_SIZE = 0.5        # metros
GOAL_TOLERANCE = 0.15  # metros
FRAME_WORLD = 'map'
FRAME_BASE = 'base_link'

# Campos potenciales
ATTRACTIVE_GAIN = 1.0
REPULSIVE_GAIN = 2.0
REPULSIVE_DISTANCE = 5.0

# ===========================
# Funciones de fuerza
# ===========================
def attractive_force(current_pos, goal_pos):
    """Calcula la fuerza atractiva hacia el objetivo"""
    vector = current_pos - goal_pos
    distance = np.linalg.norm(vector)
    if distance < 10.0:
        return ATTRACTIVE_GAIN * vector
    return np.zeros(2)

def repulsive_force(current_pos, obstacle_pos):
    """Calcula la fuerza repulsiva de un obstáculo"""
    vector = current_pos - obstacle_pos
    distance = np.linalg.norm(vector)
    if 0 < distance < REPULSIVE_DISTANCE:
        return -REPULSIVE_GAIN * ((1.0/distance - 1.0/REPULSIVE_DISTANCE) * (1.0 / (distance**2))) * (vector / distance)
    return np.zeros(2)

def move_robot(current_pos, total_force):
    """Calcula la siguiente posición del robot basado en la fuerza total"""
    magnitude = np.linalg.norm(total_force)
    if magnitude == 0:
        return current_pos.copy()
    return current_pos - STEP_SIZE * (total_force / magnitude)

def compute_next_waypoint(current_pos, goal_pos, obstacles):
    """Calcula el siguiente waypoint usando fuerzas de campo potencial"""
    f_attr = attractive_force(current_pos, goal_pos)
    f_rep = np.zeros(2)
    for obs in obstacles:
        f_rep += repulsive_force(current_pos, obs)
    f_total = f_attr + f_rep
    next_pos = move_robot(current_pos, f_total)

    waypoint = PoseStamped()
    waypoint.header.stamp = rospy.Time.now()
    waypoint.header.frame_id = FRAME_WORLD
    waypoint.pose.position.x = next_pos[0]
    waypoint.pose.position.y = next_pos[1]
    waypoint.pose.orientation.w = 1.0

    return waypoint, f_attr, f_rep, f_total

# ===========================
# Servidor de acción APF
# ===========================
class APFPlannerServer(object):
    def __init__(self):
        self.tf_listener = tf.TransformListener()
        self.server = actionlib.SimpleActionServer(
            'apf_planner',
            NextWaypointAction,
            execute_cb=self.execute_cb,
            auto_start=False
        )
        self.server.start()
        rospy.loginfo("APF Planner server ready.")

    def execute_cb(self, goal):
        current_pos = self.get_current_position()
        if current_pos is None:
            self.server.set_aborted(text="TF unavailable")
            return

        goal_pos = np.array([goal.target.pose.position.x,
                             goal.target.pose.position.y])

        # Obstáculos de ejemplo
        obstacles = [np.array([2.0, 2.0]), np.array([3.0, 1.5])]

        distance_to_goal = float(np.linalg.norm(goal_pos - current_pos))

        waypoint, f_attr, f_rep, f_total = compute_next_waypoint(current_pos, goal_pos, obstacles)

        feedback = NextWaypointFeedback()
        feedback.remaining_distance = distance_to_goal
        feedback.f_attr = Vector3(f_attr[0], f_attr[1], 0.0)
        feedback.f_rep = Vector3(f_rep[0], f_rep[1], 0.0)
        self.server.publish_feedback(feedback)

        result = NextWaypointResult()
        if distance_to_goal < GOAL_TOLERANCE:
            result.goal_reached = True
            result.next_waypoint = goal.target
            rospy.loginfo("Goal reached.")
        else:
            result.goal_reached = False
            result.next_waypoint = waypoint
            rospy.loginfo("Next waypoint computed.")

        self.server.set_succeeded(result)

    def get_current_position(self):
        """Obtiene la posición actual del robot desde TF"""
        try:
            self.tf_listener.waitForTransform(FRAME_WORLD, FRAME_BASE, rospy.Time(0), rospy.Duration(1.0))
            trans, _ = self.tf_listener.lookupTransform(FRAME_WORLD, FRAME_BASE, rospy.Time(0))
            return np.array([trans[0], trans[1]])
        except (tf.Exception, tf.LookupException, tf.ConnectivityException), e:
            rospy.logerr("TF error: %s", e)
            return None

# ===========================
# Nodo principal
# ===========================
if __name__ == '__main__':
    rospy.init_node('apf_planner_server')
    APFPlannerServer()
    rospy.spin()
