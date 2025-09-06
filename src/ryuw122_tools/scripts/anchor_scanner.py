#!/usr/bin/env python
# coding: utf-8

import rospy
from std_msgs.msg import Float32MultiArray, String
import re

class AnchorScannerClean(object):
    """
    Nodo ROS que consulta varias antenas del módulo Reyax y publica
    sus distancias en metros como un arreglo.
    """

    def __init__(self):
        rospy.init_node('anchor_scanner_clean')

        # Lista de antenas a consultar
        self.antenas = rospy.get_param('~antenas', ['ANTENA01', 'ANTENA02', 'ANTENA03'])
        # Diccionario que almacena las distancias actualizadas
        self.distancias = {antena: None for antena in self.antenas}

        # Publicador para enviar comandos AT al nodo síncrono
        self.sender_pub = rospy.Publisher('/ryuw122/send', String, queue_size=10)

        # Publicador para el arreglo de distancias en metros
        self.dist_pub = rospy.Publisher('/ryuw122/distancias', Float32MultiArray, queue_size=10)

        # Suscriptor para leer los mensajes de las antenas
        rospy.Subscriber('/ryuw122/raw', String, self.callback_raw)

        # Frecuencia de consulta en Hz
        self.rate_hz = rospy.get_param('~rate', 0.2)  # 0.2 Hz → 5 segundos
        self.rate = rospy.Rate(self.rate_hz)

        rospy.loginfo("Nodo AnchorScannerClean listo. Enviando comandos a antenas...")
        self.run()

    # ------------------------------
    # Parsing
    # ------------------------------

    @staticmethod
    def parse_distance(text):
        """
        Extrae antena y distancia en metros de un mensaje +ANCHOR_RCV.
        Retorna (antena, distancia_m) o None si no es válido.
        """
        if not text.startswith("+ANCHOR_RCV"):
            return None

        match = re.match(r"\+ANCHOR_RCV=(.*?),.*,,(\d+)\s*cm", text)
        if match:
            antena, distancia_cm = match.groups()
            return antena, float(distancia_cm) / 100.0  # Convertir cm a m
        return None

    # ------------------------------
    # Callback ROS
    # ------------------------------

    def callback_raw(self, msg):
        """
        Procesa los mensajes recibidos de /ryuw122/raw y actualiza distancias.
        """
        result = self.parse_distance(msg.data)
        if result:
            antena, distancia = result
            if antena in self.antenas:
                self.distancias[antena] = distancia
                rospy.loginfo("Distancias actualizadas: {}".format(self.distancias))
                self.publish_distances()

    # ------------------------------
    # Publicación
    # ------------------------------

    def publish_distances(self):
        """
        Publica un arreglo de distancias en el mismo orden de self.antenas.
        """
        array_msg = Float32MultiArray()
        array_msg.data = [self.distancias[antena] if self.distancias[antena] is not None else 0.0
                          for antena in self.antenas]
        self.dist_pub.publish(array_msg)

    # ------------------------------
    # Envío de comandos
    # ------------------------------

    def send_command(self, antena):
        """
        Envía el comando AT para consultar una antena específica.
        """
        cmd = "AT+ANCHOR_SEND={},4,TEST".format(antena)
        rospy.loginfo("Publicando comando a {}: {}".format(antena, cmd))
        self.sender_pub.publish(String(data=cmd))

    # ------------------------------
    # Loop principal
    # ------------------------------

    def run(self):
        """
        Envía comandos periódicamente a todas las antenas definidas.
        """
        while not rospy.is_shutdown():
            for antena in self.antenas:
                self.send_command(antena)
            self.rate.sleep()


if __name__ == '__main__':
    try:
        AnchorScannerClean()
    except rospy.ROSInterruptException:
        pass
