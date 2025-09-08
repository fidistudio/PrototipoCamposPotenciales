#!/usr/bin/env python
# coding: utf-8

import rospy
import tf
import numpy as np
from geometry_msgs.msg import PoseStamped, Vector3
import actionlib
from nav_apf_smach.msg import NextWaypointAction, NextWaypointResult, NextWaypointFeedback

# ===========================
# Parámetros globales
# ===========================
STEP_SIZE = 0.5        #Metros
GOAL_TOLERANCE = 0.15  #Metros
FRAME_WORLD = 'map'
FRAME_BASE = 'base_link'

# Parámetros campos potenciales
d0 = 5.0       #Distancia donde el campo repulsivo deja de tener efecto en metros
epsilon1 = 1.0 #Constante atractiva
eta = 2.0      #Constante repulsiva

# ===========================
# Funciones de fuerza
# ===========================
def FuerzaAtractiva(q, q_dest):
    vector = q - q_dest
    distancia = np.linalg.norm(vector)
    if distancia < 10:
        return epsilon1 * vector
    return np.zeros(2)

def FuerzaRepulsiva(q, q_obst):
    vector = q - q_obst
    distancia = np.linalg.norm(vector)
    if distancia < d0 and distancia != 0:
        return -eta * ((1/distancia - 1/d0) * (1/(distancia**2))) * (vector / distancia)
    return np.zeros(2)

def MoverRobot(q, f_total):
    magnitud = np.linalg.norm(f_total)
    if magnitud == 0:
        return q.copy()
    return q - STEP_SIZE * (f_total / magnitud)

def calcular_siguiente_waypoint(pos_actual, objetivo, obstaculos):
    """Calcula siguiente waypoint usando las fuerzas del campo potencial"""
    f_attr = FuerzaAtractiva(pos_actual, objetivo)
    f_rep = np.zeros(2)
    for obst in obstaculos:
        f_rep += FuerzaRepulsiva(pos_actual, obst)
    
    f_total = f_attr + f_rep
    siguiente_pos = MoverRobot(pos_actual, f_total)

    waypoint = PoseStamped()
    waypoint.header.stamp = rospy.Time.now()
    waypoint.header.frame_id = FRAME_WORLD
    waypoint.pose.position.x = siguiente_pos[0]
    waypoint.pose.position.y = siguiente_pos[1]
    waypoint.pose.orientation.w = 0.0

    return waypoint, f_attr, f_rep, f_total

# ===========================
# Servidor de acción APF
# ===========================
class APFPlannerServer:
    def __init__(self):
        self.listener = tf.TransformListener()
        self.server = actionlib.SimpleActionServer(
            'apf_planner',
            NextWaypointAction,
            execute_cb=self.execute_cb,
            auto_start=False
        )
        self.server.start()
        rospy.loginfo("APF Planner ready.")

    # ---------------------------
    # Callback de ejecución
    # ---------------------------
    def execute_cb(self, goal):
        result = NextWaypointResult()
        feedback = NextWaypointFeedback()

        current_position = self.get_current_position()
        if current_position is None:
            self.server.set_aborted(text="TF unavailable")
            return

        goal_position = np.array([
            goal.target.pose.position.x,
            goal.target.pose.position.y
        ])

        # Ejemplo de obstáculos; en robot real reemplazar con datos de sensores o mapa
        obstaculos = [np.array([2.0, 2.0]), np.array([3.0, 1.5])]

        # Calcular distancia al objetivo
        vector_to_goal = goal_position - current_position
        distance_to_goal = float(np.linalg.norm(vector_to_goal))

        # Publicar feedback
        waypoint, f_attr, f_rep, f_total = calcular_siguiente_waypoint(current_position, goal_position, obstaculos)
        feedback.remaining_distance = distance_to_goal
        feedback.f_attr = Vector3(*f_attr, 0.0)
        feedback.f_rep = Vector3(*f_rep, 0.0)
        self.server.publish_feedback(feedback)

        # Revisar si se alcanzó el objetivo
        if distance_to_goal < GOAL_TOLERANCE:
            result.goal_reached = True
            result.next_waypoint = goal.target
            self.server.set_succeeded(result)
            return

        # Devolver siguiente waypoint
        result.goal_reached = False
        result.next_waypoint = waypoint
        self.server.set_succeeded(result)

    # ---------------------------
    # Obtener posición actual del robot
    # ---------------------------
    def get_current_position(self):
        try:
            self.listener.waitForTransform(FRAME_WORLD, FRAME_BASE, rospy.Time(0), rospy.Duration(1.0))
            translation, _ = self.listener.lookupTransform(FRAME_WORLD, FRAME_BASE, rospy.Time(0))
            return np.array([translation[0], translation[1]])
        except (tf.Exception, tf.LookupException, tf.ConnectivityException) as e:
            rospy.logerr(f"TF error: {e}")
            return None

# ===========================
# Nodo principal
# ===========================
if __name__ == '__main__':
    rospy.init_node('apf_planner_server')
    APFPlannerServer()
    rospy.spin()
