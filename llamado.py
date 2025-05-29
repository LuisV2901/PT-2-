import Interfaz_trayectorias

interfaz = Interfaz_trayectorias.iniciar_interfaz_trayectorias(xmin=-100, xmax=0, ymin=-100, ymax=0, x0=-50, y0=-20, xc=-50, yc=0, fs=5)

# Luego, para obtener los puntos:
n,t = interfaz["obtener_parametros"]()
puntos = interfaz["obtener_puntos"]()
print(puntos)

print(n)
print(t)

