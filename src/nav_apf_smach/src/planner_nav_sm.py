#!/usr/bin/env python
# coding: utf-8

import rospy
import smach
import smach_ros
from geometry_msgs.msg import PoseStamped
from nav_apf_smach.msg import NextWaypointAction, DriveToPoseAction
from smach_ros import SimpleActionState


# ===========================
# Estado DECIDE
# ===========================
class CheckGoalReached(smach.State):
    """Estado que decide si el objetivo final ya fue alcanzado."""

    def __init__(self):
        smach.State.__init__(self, outcomes=['DONE', 'NAVIGATE'], input_keys=['goal_reached_in'])

    def execute(self, userdata):
        rospy.loginfo("[DECIDE] goal_reached_in = %s", userdata.goal_reached_in)
        if userdata.goal_reached_in:
            rospy.loginfo("[DECIDE] Objetivo alcanzado. Terminando máquina de estados.")
            return 'DONE'
        else:
            rospy.loginfo("[DECIDE] Objetivo no alcanzado. Navegando al siguiente waypoint.")
            return 'NAVIGATE'


# ===========================
# Funciones auxiliares
# ===========================
def create_target_pose():
    """Construye la meta final a partir de parámetros de ROS."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = rospy.get_param('~goal_x', 5.0)
    pose.pose.position.y = rospy.get_param('~goal_y', 4.0)
    pose.pose.orientation.w = 1.0
    rospy.loginfo("[SMACH] Target global creado: x=%.2f, y=%.2f", pose.pose.position.x, pose.pose.position.y)
    return pose


def build_plan_goal(userdata, goal):
    """Construye el goal para el planner (apf_planner)."""
    g = NextWaypointAction._goal_class()
    g.target = userdata.target
    rospy.loginfo("[PLAN] Enviando goal al APF Planner: x=%.2f, y=%.2f",
                  g.target.pose.position.x, g.target.pose.position.y)
    return g


def handle_plan_result(userdata, status, result):
    """Procesa el resultado del planner y actualiza el userdata."""
    userdata.next_waypoint = result.next_waypoint
    userdata.goal_reached = bool(result.goal_reached)

    rospy.loginfo(
        "[PLAN] Planner devolvió next_waypoint en base_link: x=%.2f, y=%.2f, goal_reached=%s",
        result.next_waypoint.pose.position.x,
        result.next_waypoint.pose.position.y,
        result.goal_reached
    )
    return 'succeeded'


def build_drive_goal(userdata, goal):
    """Construye el goal para el driver (drive_to_pose)."""
    g = DriveToPoseAction._goal_class()
    g.target = userdata.next_waypoint
    rospy.loginfo(
        "[NAVIGATE] Enviando robot hacia waypoint: x=%.2f, y=%.2f",
        g.target.pose.position.x,
        g.target.pose.position.y
    )
    return g


# ===========================
# Construcción de la máquina de estados
# ===========================
def build_state_machine():
    """Construye la máquina de estados completa."""
    sm = smach.StateMachine(outcomes=['DONE', 'FAILED'])
    sm.userdata.target = create_target_pose()
    sm.userdata.next_waypoint = PoseStamped()
    sm.userdata.goal_reached = False

    with sm:
        smach.StateMachine.add(
            'PLAN',
            SimpleActionState(
                'apf_planner',
                NextWaypointAction,
                goal_cb=build_plan_goal,
                result_cb=handle_plan_result
            ),
            transitions={'succeeded': 'DECIDE', 'aborted': 'FAILED'},
            remapping={
                'target': 'target',
                'next_waypoint': 'next_waypoint',
                'goal_reached': 'goal_reached_in'
            }
        )

        smach.StateMachine.add(
            'DECIDE',
            CheckGoalReached(),
            transitions={'DONE': 'DONE', 'NAVIGATE': 'NAVIGATE'},
            remapping={'goal_reached_in': 'goal_reached'}
        )

        smach.StateMachine.add(
            'NAVIGATE',
            SimpleActionState(
                'drive_to_pose',
                DriveToPoseAction,
                goal_cb=build_drive_goal
            ),
            transitions={'succeeded': 'PLAN', 'aborted': 'FAILED'},
            remapping={'next_waypoint': 'next_waypoint'}
        )

    return sm


# ===========================
# Nodo principal
# ===========================
def main():
    rospy.init_node('planner_nav_sm')

    rospy.loginfo("[SMACH] Iniciando máquina de estados APF Navigation.")
    sm = build_state_machine()

    sis = smach_ros.IntrospectionServer('apf_smach_view', sm, '/APF-SM')
    sis.start()

    outcome = sm.execute()
    rospy.loginfo("[SMACH] Máquina de estados finalizada con outcome: %s", outcome)

    rospy.spin()
    sis.stop()


if __name__ == '__main__':
    main()
