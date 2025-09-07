#!/usr/bin/env python
# coding: utf-8

import rospy
import serial
from std_msgs.msg import String, Float32MultiArray
from threading import Lock
import re


class AnchorDistancePublisher(object):
    """
    Nodo ROS que comunica con módulo Reyax, lee distancias de varias antenas
    y publica un arreglo de distancias suavizadas con filtro exponencial y
    descarte de outliers, compatible con Python 2.7.
    """

    def __init__(self):
        rospy.init_node('anchor_distance_publisher')

        self._setup_parameters()
        self._setup_serial()
        self._setup_publishers()
        self._setup_timers()

        rospy.loginfo("Nodo AnchorDistancePublisher listo.")

    # --------------------------
    # Configuración
    # --------------------------
    def _setup_parameters(self):
        self.antennas = rospy.get_param('~antennas', ['ANTENA01', 'ANTENA02', 'ANTENA03'])
        self.distances = {ant: None for ant in self.antennas}
        self.alpha = rospy.get_param('~alpha', 0.3)  # filtro exponencial
        self.max_jump = rospy.get_param('~max_jump', 0.2)  # descarte de outliers en metros
        self.send_rate_hz = rospy.get_param('~send_rate', 1) #Hz
        self.read_period = rospy.get_param('~read_period', 0.05)
        self.port = rospy.get_param('~port', '/dev/ttyTHS1')
        self.baud = int(rospy.get_param('~baud', 115200))
        self.timeout = float(rospy.get_param('~timeout', 1.0))

        self.send_commands = [
            "AT+ANCHOR_SEND={},4,TEST".format(ant) for ant in self.antennas
        ]

    def _setup_serial(self):
        self.serial_lock = Lock()
        try:
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout
            )
            rospy.loginfo("Puerto serial %s abierto a %d baudios", self.port, self.baud)
        except Exception as e:
            rospy.logerr("No se pudo abrir %s: %s", self.port, str(e))
            rospy.signal_shutdown("Error al abrir puerto serial")
            raise

    def _setup_publishers(self):
        self.raw_pub = rospy.Publisher('/ryuw122/raw', String, queue_size=10)
        self.dist_pub = rospy.Publisher('/ryuw122/distancias', Float32MultiArray, queue_size=10)

    def _setup_timers(self):
        rospy.Timer(rospy.Duration(self.read_period), self._read_serial_timer)
        rospy.Timer(rospy.Duration(1.0 / self.send_rate_hz), self._send_commands_timer)

    # --------------------------
    # Serial
    # --------------------------
    def _send_command(self, command):
        """Envía un comando AT al módulo con protección de lock."""
        with self.serial_lock:
            try:
                self.serial_port.write((command + '\r\n').encode('utf-8'))
                rospy.logdebug("Comando enviado: %s", command)
            except Exception as e:
                rospy.logwarn("Error al enviar comando: %s", str(e))

    def _read_serial_line(self):
        """Lee una línea completa desde el puerto serial."""
        with self.serial_lock:
            try:
                return self.serial_port.readline()
            except Exception as e:
                rospy.logwarn("Error al leer serial: %s", str(e))
                return b''

    # --------------------------
    # Timers
    # --------------------------
    def _send_commands_timer(self, _event):
        """Envía los comandos AT a cada antena con pequeño retraso."""
        for cmd in self.send_commands:
            self._send_command(cmd)
            rospy.sleep(0.5)

    def _read_serial_timer(self, _event):
        """Procesa todas las líneas disponibles en el buffer serial."""
        while self.serial_port.inWaiting() > 0:
            raw_line = self._read_serial_line()
            if not raw_line:
                continue

            text = raw_line.strip()
            if isinstance(text, bytes):
                text = text.decode('utf-8', 'ignore')

            if text:
                self.raw_pub.publish(text)
                self._process_distance_line(text)

    # --------------------------
    # Parsing y filtrado
    # --------------------------
    def _process_distance_line(self, text):
        """Extrae antena y distancia de un mensaje +ANCHOR_RCV y aplica filtrado."""
        if not text.startswith("+ANCHOR_RCV"):
            return

        match = re.match(r"\+ANCHOR_RCV=(.*?),.*,,(\d+)\s*cm", text)
        if not match:
            return

        antenna, dist_cm = match.groups()
        dist_m = float(dist_cm) / 100.0

        if antenna in self.antennas:
            self._update_distance(antenna, dist_m)
            self._publish_distances()

    def _update_distance(self, antenna, new_dist):
        """Actualiza la distancia usando filtro exponencial y descartando outliers."""
        prev_dist = self.distances[antenna]

        # Ignorar saltos muy grandes (outliers)
        if prev_dist is not None and abs(new_dist - prev_dist) > self.max_jump:
            rospy.logwarn("Descartando medida extrema: {} -> {}".format(prev_dist, new_dist))
            return

        if prev_dist is None:
            self.distances[antenna] = new_dist
        else:
            self.distances[antenna] = (
                self.alpha * new_dist + (1 - self.alpha) * prev_dist
            )

    def _publish_distances(self):
        """Publica las distancias suavizadas en un Float32MultiArray."""
        array_msg = Float32MultiArray()
        array_msg.data = [
            self.distances[ant] if self.distances[ant] is not None else 0.0
            for ant in self.antennas
        ]
        self.dist_pub.publish(array_msg)

    # --------------------------
    # Loop principal
    # --------------------------
    def spin(self):
        rospy.spin()


if __name__ == "__main__":
    try:
        node = AnchorDistancePublisher()
        node.spin()
    except rospy.ROSInterruptException:
        pass
