#!/usr/bin/env python
# coding: utf-8

import rospy
import actionlib
import serial
from nav_apf_smach.msg import DriveToPoseAction, DriveToPoseResult, DriveToPoseFeedback


class ESP32SerialInterface:
    """Gestiona la comunicación serial con la ESP32."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200, timeout: float = 1.0):
        self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        rospy.loginfo(f"Conectado a ESP32 en {port} a {baudrate} bps.")

    def send_goal(self, x: float, y: float) -> None:
        """Envía un objetivo de navegación a la ESP32 en formato CSV."""
        message = f"{x:.2f},{y:.2f}\n"
        self.serial.write(message.encode("utf-8"))
        rospy.loginfo(f"Objetivo enviado a ESP32: {message.strip()}")

    def read_line(self) -> str:
        """Lee una línea desde la ESP32, decodificada y limpia."""
        try:
            line = self.serial.readline().decode("utf-8").strip()
            return line
        except Exception as e:
            rospy.logwarn(f"Error al leer de ESP32: {e}")
            return ""


class DriveToPoseActionServer:
    """Servidor de acción ROS que envía metas a la ESP32 y gestiona feedback/result."""

    def __init__(self, serial_interface: ESP32SerialInterface):
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

    def _handle_distance_feedback(self, message: str) -> None:
        """Procesa feedback de distancia desde la ESP32."""
        try:
            distance = float(message.split(":")[1])
            feedback = DriveToPoseFeedback(remaining_distance=distance)
            self.action_server.publish_feedback(feedback)
            rospy.loginfo(f"Feedback distancia restante: {distance:.2f} m")
        except ValueError:
            rospy.logwarn(f"Formato inválido en feedback: {message}")

    def _handle_success(self) -> None:
        """Marca la acción como completada exitosamente."""
        result = DriveToPoseResult(arrived=True)
        self.action_server.set_succeeded(result)
        rospy.loginfo("Objetivo alcanzado (ARRIVED).")

    def _handle_error(self, message: str) -> None:
        """Aborta la acción en caso de error reportado por la ESP32."""
        self.action_server.set_aborted(text=message)
        rospy.logerr(f"Acción abortada: {message}")


def main():
    rospy.init_node("drive_to_pose_server")

    try:
        serial_interface = ESP32SerialInterface(port="/dev/ttyUSB0", baudrate=115200)
        DriveToPoseActionServer(serial_interface)
        rospy.spin()
    except serial.SerialException as e:
        rospy.logfatal(f"No se pudo abrir puerto serial: {e}")


if __name__ == "__main__":
    main()
