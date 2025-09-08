#!/usr/bin/env python
# coding: utf-8

import rospy
import actionlib
import serial
from nav_apf_smach.msg import DriveToPoseAction, DriveToPoseResult, DriveToPoseFeedback


class ESP32SerialInterface(object):
    """Gestiona la comunicación serial con la ESP32."""

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=1.0):
        self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        rospy.loginfo("Conectado a ESP32 en {} a {} bps.".format(port, baudrate))

    def send_goal(self, x, y):
        """Envía un objetivo de navegación a la ESP32 en formato CSV."""
        message = "{:.2f},{:.2f}\n".format(x, y)
        self.serial.write(message.encode("utf-8"))
        rospy.loginfo("Objetivo enviado a ESP32: {}".format(message.strip()))

    def read_line(self):
        """Lee una línea desde la ESP32, decodificada y limpia."""
        try:
            line = self.serial.readline().decode("utf-8").strip()
            return line
        except Exception, e: 
            rospy.logwarn("Error al leer de ESP32: {}".format(e))
            return ""


class DriveToPoseActionServer(object):
    """Servidor de acción ROS que envía metas a la ESP32 y gestiona feedback/result."""

    def __init__(self, serial_interface):
        self.serial_interface = serial_interface
        self.action_server = actionlib.SimpleActionServer(
            name="drive_to_pose",
            ActionSpec=DriveToPoseAction,
            execute_cb=self.execute_callback,
            auto_start=False
        )
        self.action_server.start()
        rospy.loginfo("Servidor de acción 'drive_to_pose' listo.")

    def execute_callback(self, goal):
        """Ejecuta el ciclo de comunicación con la ESP32 para un objetivo recibido."""
        self.serial_interface.send_goal(
            goal.target.pose.position.x,
            goal.target.pose.position.y
        )

        while not rospy.is_shutdown():
            response = self.serial_interface.read_line()
            if not response:
                continue

            if response.startswith("DIST:"):
                self._handle_distance_feedback(response)
            elif response == "ARRIVED":
                self._handle_success()
                break
            elif response.startswith("ERROR:"):
                self._handle_error(response)
                break

    def _handle_distance_feedback(self, message):
        """Procesa feedback de distancia desde la ESP32."""
        try:
            distance = float(message.split(":")[1])
            feedback = DriveToPoseFeedback(remaining_distance=distance)
            self.action_server.publish_feedback(feedback)
            rospy.loginfo("Feedback distancia restante: {:.2f} m".format(distance))
        except ValueError:
            rospy.logwarn("Formato inválido en feedback: {}".format(message))

    def _handle_success(self):
        """Marca la acción como completada exitosamente."""
        result = DriveToPoseResult(arrived=True)
        self.action_server.set_succeeded(result)
        rospy.loginfo("Objetivo alcanzado (ARRIVED).")

    def _handle_error(self, message):
        """Aborta la acción en caso de error reportado por la ESP32."""
        self.action_server.set_aborted(text=message)
        rospy.logerr("Acción abortada: {}".format(message))


def main():
    rospy.init_node("drive_to_pose_server")

    try:
        serial_interface = ESP32SerialInterface(port="/dev/ttyUSB0", baudrate=115200)
        DriveToPoseActionServer(serial_interface)
        rospy.spin()
    except serial.SerialException, e:
        rospy.logfatal("No se pudo abrir puerto serial: {}".format(e))


if __name__ == "__main__":
    main()
