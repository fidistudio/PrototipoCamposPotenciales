#!/usr/bin/env python
# coding: utf-8

import rospy
import tf
import tf2_ros
from geometry_msgs.msg import Pose2D, TransformStamped
from sensor_msgs.msg import Imu

BROADCAST_RATE_HZ = 30  # Hz

class MapToBaseBroadcaster:
    """Publica transformadas: map → base_link y base_link → laser_frame (TF) usando UWB + IMU."""

    def __init__(self):
        # -------------------------------
        # Parámetros configurables
        # -------------------------------
        self._antenna_offset_x = rospy.get_param("~antenna_offset_x", 0.0)
        self._antenna_offset_y = rospy.get_param("~antenna_offset_y", 0.0)
        self._lidar_offset_x = rospy.get_param("~lidar_offset_x", 0.2)
        self._lidar_offset_y = rospy.get_param("~lidar_offset_y", 0.0)
        self._lidar_offset_z = rospy.get_param("~lidar_offset_z", 0.1)
        self._init_x = rospy.get_param("~init_x", 0.0)
        self._init_y = rospy.get_param("~init_y", 0.0)

        # -------------------------------
        # Estado dinámico
        # -------------------------------
        self._x = self._init_x
        self._y = self._init_y
        self._orientation_quat = (0.0, 0.0, 0.0, 1.0)
        self._initial_yaw = None

        # -------------------------------
        # Transform broadcasters
        # -------------------------------
        self._tf_broadcaster = tf.TransformBroadcaster()
        self._static_br = tf2_ros.StaticTransformBroadcaster()
        self._publish_static_lidar_tf()

        # -------------------------------
        # Suscriptores
        # -------------------------------
        rospy.Subscriber("/ryuw122/position", Pose2D, self._uwb_callback)
        rospy.Subscriber("/rtimulib_node/imu", Imu, self._imu_callback)

    # -------------------------------
    # Callbacks sensores
    # -------------------------------
    def _uwb_callback(self, msg: Pose2D):
        """Actualiza la posición XY desde la antena UWB."""
        self._x = msg.x
        self._y = msg.y

    def _imu_callback(self, msg: Imu):
        """Actualiza la orientación calibrada desde la IMU."""
        imu_quat = (
            msg.orientation.x,
            msg.orientation.y,
            msg.orientation.z,
            msg.orientation.w
        )
        self._orientation_quat = self._compute_calibrated_orientation(imu_quat)

    # -------------------------------
    # Orientación calibrada
    # -------------------------------
    def _compute_calibrated_orientation(self, imu_quat):
        """Corrige yaw relativo a la orientación inicial."""
        roll, pitch, yaw = tf.transformations.euler_from_quaternion(imu_quat)
        if self._initial_yaw is None:
            self._initial_yaw = yaw
            rospy.loginfo("Calibración inicial de yaw: %.3f rad", self._initial_yaw)
        yaw_corrected = yaw - self._initial_yaw
        return tf.transformations.quaternion_from_euler(roll, pitch, yaw_corrected)

    # -------------------------------
    # Publicación TF dinámica
    # -------------------------------
    def _broadcast_transform(self):
        """Publica map → base_link usando offset de antena."""
        base_x = self._x - self._antenna_offset_x
        base_y = self._y - self._antenna_offset_y

        self._tf_broadcaster.sendTransform(
            (base_x, base_y, 0.0),
            self._orientation_quat,
            rospy.Time.now(),
            "base_link",
            "map"
        )

    # -------------------------------
    # Publicación TF estática del LiDAR
    # -------------------------------
    def _publish_static_lidar_tf(self):
        """Publica la transformada fija base_link → laser_frame."""
        t = TransformStamped()
        t.header.stamp = rospy.Time.now()
        t.header.frame_id = "base_link"
        t.child_frame_id = "laser"
        t.transform.translation.x = self._lidar_offset_x
        t.transform.translation.y = self._lidar_offset_y
        t.transform.translation.z = self._lidar_offset_z
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0
        self._static_br.sendTransform(t)

    # -------------------------------
    # Bucle principal
    # -------------------------------
    def run(self):
        rate = rospy.Rate(BROADCAST_RATE_HZ)
        while not rospy.is_shutdown():
            self._broadcast_transform()
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("map_to_base_broadcaster")
    broadcaster = MapToBaseBroadcaster()
    broadcaster.run()
