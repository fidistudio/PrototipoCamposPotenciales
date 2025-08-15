#!/usr/bin/env python
# encoding: utf-8
import rospy
import numpy as np

# Parámetros iniciales 
q0 = np.array([1.0, 1.0])     # Posición inicial 
q_dest = np.array([5.0, 4.0]) # Destino
q_obst = np.array([2.0, 2.0]) # Obstáculo 

d0 = 5.0
epsilon1 = 1.0
eta = 2.0
delta0 = 0.5

def FuerzaAtractiva(q, q_dest):
    vector = q - q_dest
    distancia = np.linalg.norm(vector)
    if distancia < 10: 
        return epsilon1 * vector
    return np.array([0.0, 0.0])
    
def FuerzaRepulsiva(q, q_obst):
    vector = q - q_obst
    distancia = np.linalg.norm(vector)
    if distancia < d0 and distancia != 0:
        return -eta * ((1/distancia - 1/d0) * (1/(distancia**2))) * (vector/distancia)
    return np.array([0.0, 0.0])
   
def MoverRobot(q, f_total): 
    magnitud = np.linalg.norm(f_total)
    if magnitud == 0: 
        return q
    return q - delta0 * (f_total / magnitud)

if __name__ == '__main__':
    rospy.init_node('campos_potenciales_node', anonymous=True)

    rate = rospy.Rate(2)  # 2 Hz (0.5 seg por iteración)
    posicion = q0.copy()

    # Encabezado de la tabla
    print("{:>4} | {:>8} | {:>8} | {:>18} | {:>18} | {:>18}".format(
        "Iter", "Pos X", "Pos Y", "F_attr", "F_rep", "F_total"
    ))
    print("-" * 90)

    iteracion = 0
    try:
        while not rospy.is_shutdown() and iteracion < 10:
            f_attr = FuerzaAtractiva(posicion, q_dest)
            f_rep  = FuerzaRepulsiva(posicion, q_obst)
            f_total = f_attr + f_rep

            # Mostrar datos en consola
            print("{:4d} | {:8.3f} | {:8.3f} | {:>18} | {:>18} | {:>18}".format(
                iteracion,
                posicion[0],
                posicion[1],
                str(np.round(f_attr, 3)),
                str(np.round(f_rep, 3)),
                str(np.round(f_total, 3))
            ))

            # Mover robot
            posicion = MoverRobot(posicion, f_total)

            # Condición de llegada
            if np.linalg.norm(q_dest - posicion) < 0.1:
                print("Destino alcanzado en {} iteraciones.".format(iteracion+1))
                break

            iteracion += 1
            rate.sleep()

    except rospy.ROSInterruptException:
        pass
