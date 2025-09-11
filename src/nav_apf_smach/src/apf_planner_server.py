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
STEP_SIZE = 0.5
GOAL_TOLERANCE = 0.15
FRAME_WORLD = 'map'
FRAME_BASE = 'base_link'

ATTRACTIVE_GAIN = 1.0
REPULSIVE_GAIN = 2.0
REPULSIVE_DISTANCE = 5.0

# ===========================
# Funciones auxiliares
# ===========================
def attractive_force(current, goal):
    """Calcula la fuerza atractiva hacia el objetivo en coordenadas relativas al robot."""
    vector = current - goal
    distance = np.linalg.norm(vector)
    if distance < 10.0:
        return ATTRACTIVE_GAIN * vector
    return np.zeros(2)

def repulsive_force(current, obstacle):
    """Calcula la fuerza repulsiva respecto a un obstáculo en coordenadas relativas al robot."""
    vector = current - obstacle
    distance = np.linalg.norm(vector)
    if 0 < distance < REPULSIVE_DISTANCE:
        return -REPULSIVE_GAIN * ((1.0/distance - 1.0/REPULSIVE_DISTANCE) / (distance**2)) * (vector / distance)
    return np.zeros(2)

def move_robot(current, total_force):
    """Calcula la siguiente posición relativa al robot."""
    magnitude = np.linalg.norm(total_force)
    if magnitude == 0:
        return current.copy()
    return current - STEP_SIZE * (total_force / magnitude)

def transform_pose(tf_listener, pose, target_frame):
    """Transforma una PoseStamped a otro frame."""
    try:
        transformed_pose = tf_listener.transformPose(target_frame, pose)
        return np.array([transformed_pose.pose.position.x, transformed_pose.pose.position.y])
    except (tf.Exception, tf.LookupException, tf.ConnectivityException) as e:
        rospy.logerr("Error transformando pose a %s: %s", target_frame, e)
        return None

def compute_forces(current_pos, goal_pos, obstacles):
    """Calcula la fuerza total sobre el robot dada la meta y los obstáculos."""
    f_attr = attractive_force(current_pos, goal_pos)
    f_rep = np.zeros(2)
    for obs in obstacles:
        f_rep += repulsive_force(current_pos, obs)
    return f_attr, f_rep, f_attr + f_rep

def compute_next_waypoint(tf_listener, goal_pose, obstacles_map):
    """Calcula el siguiente waypoint en base_link y devuelve fuerzas para debug."""
    current_pos = np.array([0.0, 0.0])  # robot en origen de base_link
    goal_in_base = transform_pose(tf_listener, goal_pose, FRAME_BASE)
    obstacles_in_base = [transform_pose(tf_listener, obs, FRAME_BASE) for obs in obstacles_map]
    obstacles_in_base = [o for o in obstacles_in_base if o is not None]

    f_attr, f_rep, f_total = compute_forces(current_pos, goal_in_base, obstacles_in_base)
    next_pos_in_base = move_robot(current_pos, f_total)

    waypoint_base = PoseStamped()
    waypoint_base.header.stamp = rospy.Time.now()
    waypoint_base.header.frame_id = FRAME_BASE
    waypoint_base.pose.position.x = next_pos_in_base[0]
    waypoint_base.pose.position.y = next_pos_in_base[1]
    waypoint_base.pose.orientation.w = 1.0

    return waypoint_base, f_attr, f_rep, f_total, goal_in_base, obstacles_in_base

def get_robot_position(tf_listener):
    """Obtiene la posición del robot en el frame map."""
    try:
        trans, _ = tf_listener.lookupTransform(FRAME_WORLD, FRAME_BASE, rospy.Time(0))
        return np.array([trans[0], trans[1]])
    except (tf.Exception, tf.LookupException, tf.ConnectivityException) as e:
        rospy.logerr("No se pudo obtener la posición del robot en %s: %s", FRAME_WORLD, e)
        return None

# ===========================
# Servidor de acción
# ===========================
class APFPlannerServer:
    """Servidor de acción que genera waypoints usando APF y coord. relativas."""

    def __init__(self):
        self.tf_listener = tf.TransformListener()
        self.server = actionlib.SimpleActionServer(
            'apf_planner',
            NextWaypointAction,
            execute_cb=self.execute_cb,
            auto_start=False
        )
        self.server.start()
        rospy.loginfo("[APF] Planner server listo.")

    def execute_cb(self, goal):
        """Callback principal de la acción."""
        robot_pos_map = get_robot_position(self.tf_listener)
        if robot_pos_map is None:
            self.server.set_aborted()
            return

        obstacles_map = self._generate_example_obstacles()
        waypoint, f_attr, f_rep, f_total, goal_in_base, obstacles_in_base = compute_next_waypoint(
            self.tf_listener, goal.target, obstacles_map
        )

        distance_to_goal = np.linalg.norm(
            robot_pos_map - np.array([goal.target.pose.position.x, goal.target.pose.position.y])
        )

        # Publicar feedback detallado
        self._publish_feedback(
            goal_pose_map=goal.target,
            goal_in_base=goal_in_base,
            obstacles_in_base=obstacles_in_base,
            f_attr=f_attr,
            f_rep=f_rep,
            distance=distance_to_goal
        )

        self._set_result(waypoint, distance_to_goal)

    def _publish_feedback(self, goal_pose_map, goal_in_base, obstacles_in_base, f_attr, f_rep, distance):
        """Publica feedback enriquecido para depuración."""
        feedback = NextWaypointFeedback()
        feedback.remaining_distance = distance
        feedback.f_attr = Vector3(f_attr[0], f_attr[1], 0.0)
        feedback.f_rep = Vector3(f_rep[0], f_rep[1], 0.0)

        obstacle_strs = []
        for i, obs in enumerate(obstacles_in_base):
            obstacle_strs.append("obs%d_base=(%.2f, %.2f)" % (i+1, obs[0], obs[1]))

        feedback.debug_info = (
            "goal_map=(%.2f, %.2f) | goal_base=(%.2f, %.2f) | obstacles_base=[%s] | "%
            (
                goal_pose_map.pose.position.x,
                goal_pose_map.pose.position.y,
                goal_in_base[0],
                goal_in_base[1],
                ", ".join(obstacle_strs)
            )
        )

        self.server.publish_feedback(feedback)

    def _set_result(self, waypoint, distance_to_goal):
        """Define el resultado de la acción."""
        result = NextWaypointResult()
        result.next_waypoint = waypoint
        result.goal_reached = distance_to_goal < GOAL_TOLERANCE
        self.server.set_succeeded(result)
        rospy.loginfo("[APF] Resultado enviado: goal_reached=%s, waypoint=(%.2f, %.2f)",
                      result.goal_reached,
                      waypoint.pose.position.x,
                      waypoint.pose.position.y)

    def _generate_example_obstacles(self):
        """Crea obstáculos de ejemplo en frame map."""
        obstacles = []

        obs1 = PoseStamped()
        obs1.header.frame_id = FRAME_WORLD
        obs1.pose.position.x = 2.0
        obs1.pose.position.y = 2.0
        obstacles.append(obs1)

        obs2 = PoseStamped()
        obs2.header.frame_id = FRAME_WORLD
        obs2.pose.position.x = 3.0
        obs2.pose.position.y = 1.5
        obstacles.append(obs2)

        return obstacles

# ===========================
# Nodo principal
# ===========================
if __name__ == '__main__':
    rospy.init_node('apf_planner_server')
    APFPlannerServer()
    rospy.spin()
