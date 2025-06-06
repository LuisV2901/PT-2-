import Interfaz_trayectorias

ventana = Interfaz_trayectorias.VentanaTrayectorias(xmin=-100, xmax=0, ymin=-100, ymax=0, x0=-50, y0=-10, xc=-50, yc=0, fs=10)
print(ventana.muestrasn)
print(ventana.tiempo)
print(ventana.puntos_de_muestreo)
