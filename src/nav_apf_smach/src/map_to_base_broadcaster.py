#!/usr/bin/env python
# coding: utf-8

import rospy
import tf
from geometry_msgs.msg import Pose2D
from sensor_msgs.msg import Imu

BROADCAST_RATE_HZ = 30  # Frecuencia de publicación en Hz


class MapToBaseBroadcaster(object):
    """Nodo que publica la transformada de 'map' a 'base_link' usando UWB e IMU."""

    def __init__(self):
        self._transform_broadcaster = tf.TransformBroadcaster()

        # Estado de posición
        self._x = rospy.get_param("~init_x", 0.0)
        self._y = rospy.get_param("~init_y", 0.0)

        # Estado de orientación
        self._orientation_quat = (0.0, 0.0, 0.0, 1.0)
        self._initial_yaw = None  # Se usará para calibrar al inicio

        # Suscriptores
        rospy.Subscriber("/ryuw122/position", Pose2D, self._handle_uwb_pose, queue_size=1)
        rospy.Subscriber("/rtimulib_node/imu", Imu, self._handle_imu_orientation, queue_size=1)

    # ---------------------------
    # Callbacks de sensores
    # ---------------------------
    def _handle_uwb_pose(self, msg):
        """Actualiza la posición XY a partir del UWB."""
        self._x = msg.x
        self._y = msg.y

    def _handle_imu_orientation(self, msg):
        """Procesa la orientación cruda de la IMU y aplica calibración de yaw."""
        imu_quat = (
            msg.orientation.x,
            msg.orientation.y,
            msg.orientation.z,
            msg.orientation.w
        )
        self._orientation_quat = self._compute_calibrated_orientation(imu_quat)

    # ---------------------------
    # Orientación calibrada
    # ---------------------------
    def _compute_calibrated_orientation(self, imu_quat):
        """Devuelve la orientación calibrada con yaw relativo al frame 'map'."""
        roll, pitch, yaw = tf.transformations.euler_from_quaternion(imu_quat)

        if self._initial_yaw is None:
            # Guardamos la orientación inicial como referencia de 0°
            self._initial_yaw = yaw
            rospy.loginfo("Calibración inicial de yaw realizada (%.3f rad)" % self._initial_yaw)

        yaw_corrected = yaw - self._initial_yaw
        return tf.transformations.quaternion_from_euler(roll, pitch, yaw_corrected)

    # ---------------------------
    # Publicación de transformada
    # ---------------------------
    def _broadcast_transform(self):
        """Publica la transformada de 'map' a 'base_link'."""
        self._transform_broadcaster.sendTransform(
            (self._x, self._y, 0.0),
            self._orientation_quat,
            rospy.Time.now(),
            "base_link",
            "map"
        )

    # ---------------------------
    # Bucle principal
    # ---------------------------
    def run(self):
        """Ejecuta el ciclo principal de publicación de transformadas."""
        rate = rospy.Rate(BROADCAST_RATE_HZ)
        while not rospy.is_shutdown():
            self._broadcast_transform()
            rate.sleep()


if __name__ == "__main__":
    rospy.init_node("map_to_base_broadcaster")
    broadcaster = MapToBaseBroadcaster()
    broadcaster.run()
