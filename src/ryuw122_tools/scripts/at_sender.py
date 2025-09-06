#!/usr/bin/env python
# coding: utf-8

import rospy
import serial
from std_msgs.msg import String
from threading import Lock


class SerialATInterface(object):
    """
    Maneja la comunicación serial con el módulo Reyax mediante comandos AT.
    Publica los datos recibidos y envía comandos periódicamente.
    """

    def __init__(self):
        self.serial = self._open_serial_port()
        self.lock = Lock()

        self.publisher = rospy.Publisher('ryuw122/raw', String, queue_size=10)
        rospy.Subscriber('ryuw122/send', String, self._on_message_to_send)

        # Configurar timers de lectura y envío
        self._start_periodic_reader()
        self._start_periodic_sender()

    # ------------------------------
    # Inicialización
    # ------------------------------

    def _open_serial_port(self):
        """Abre el puerto serial según parámetros de ROS."""
        port = rospy.get_param('~port', '/dev/ttyUSB0')
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

    def _start_periodic_reader(self):
        """Configura un temporizador para leer periódicamente del puerto serial."""
        read_period = float(rospy.get_param('~read_period', 0.05))
        rospy.Timer(rospy.Duration(read_period), self._on_read_timer)

    def _start_periodic_sender(self):
        """Configura un temporizador para enviar comandos periódicamente."""
        send_period = float(rospy.get_param('~send_period', 1.0))  # 1 Hz por defecto
        self.command = rospy.get_param('~send_command', 'AT+ANCHOR_SEND=ANTENA01,4,TEST')
        rospy.Timer(rospy.Duration(send_period), self._on_send_timer)

    # ------------------------------
    # Envío de datos
    # ------------------------------

    def send(self, command):
        """Envía un comando AT al dispositivo serial."""
        line = (command.strip() + '\r\n').encode('utf-8')
        with self.lock:
            try:
                self.serial.write(line)
                rospy.loginfo("Enviado: %s", command)
            except Exception as error:
                rospy.logwarn("Error al enviar comando: %s", str(error))

    def _on_message_to_send(self, msg):
        """Callback para manejar mensajes entrantes desde ROS."""
        self.send(msg.data)

    def _on_send_timer(self, _event):
        """Callback para enviar periódicamente el comando."""
        self.send(self.command)

    # ------------------------------
    # Recepción de datos
    # ------------------------------

    def _on_read_timer(self, _event):
        """Lee datos periódicamente del puerto serial."""
        raw_data = self._read_serial_data()
        if not raw_data:
            return

        decoded = raw_data.decode('utf-8', errors='ignore').strip()
        if decoded:
            rospy.loginfo("Recibido: %s", decoded)
            self.publisher.publish(decoded)

    def _read_serial_data(self):
        """Lee datos del buffer serial de manera segura."""
        with self.lock:
            try:
                if self.serial.in_waiting > 0:
                    return self.serial.read(self.serial.in_waiting)
                return self.serial.readline()
            except Exception as error:
                rospy.logwarn("Error al leer del puerto serial: %s", str(error))
                return b''


def main():
    rospy.init_node('ryuw122_at')
    SerialATInterface()
    rospy.spin()


if __name__ == '__main__':
    main()
