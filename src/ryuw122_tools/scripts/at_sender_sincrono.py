#!/usr/bin/env python
# coding: utf-8

import rospy
import serial
from std_msgs.msg import String
from threading import Lock


class SerialATInterface(object):
    """
    Comunicación serial con el módulo Reyax mediante comandos AT.
    Publica la respuesta del módulo y envía comandos bajo demanda.
    """

    def __init__(self):
        self.serial = self._open_serial_port()
        self.lock = Lock()

        # Publicador de datos recibidos
        self.publisher = rospy.Publisher('ryuw122/raw', String, queue_size=10)
        # Suscriptor para recibir comandos a enviar
        rospy.Subscriber('ryuw122/send', String, self._on_message_to_send)

        rospy.loginfo("Nodo listo. Esperando comandos en /ryuw122/send...")

    # ------------------------------
    # Inicialización del puerto
    # ------------------------------
    def _open_serial_port(self):
        port = rospy.get_param('~port', '/dev/ttyTHS1')
        baud = int(rospy.get_param('~baud', 115200))
        timeout = float(rospy.get_param('~timeout', 1.0))

        try:
            ser = serial.Serial(port=port, baudrate=baud, timeout=timeout)
            rospy.loginfo("Puerto serial %s abierto a %d baudios", port, baud)
            return ser
        except Exception as error:
            rospy.logerr("No se pudo abrir %s: %s", port, str(error))
            rospy.signal_shutdown("Error al abrir puerto serial")
            raise

    # ------------------------------
    # Envío y recepción bajo demanda
    # ------------------------------
    def send(self, command):
        line = (command.strip() + '\r\n').encode('utf-8')
        with self.lock:
            self.serial.write(line)
            rospy.loginfo("Enviado: %s", command)

            while True:
                response = self.serial.readline()
                if not response:
                    break  # timeout
                decoded = response.decode('utf-8', errors='ignore').strip()
                if decoded:
                    rospy.loginfo("Recibido: %s", decoded)
                    self.publisher.publish(decoded)
                    if decoded.startswith("+ANCHOR_RCV"):
                        break  # ya tenemos la distancia

    def _on_message_to_send(self, msg):
        """Callback para manejar mensajes entrantes desde ROS."""
        self.send(msg.data)


def main():
    rospy.init_node('ryuw122_at')
    SerialATInterface()
    rospy.spin()


if __name__ == '__main__':
    main()
