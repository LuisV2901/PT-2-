import matplotlib.pyplot as plt
import numpy as np

# Datos
sensores = ['CO2', 'TEMPERATURA', 'HUMEDAD', 'IRRADIANCIA', 'eCO2', 'TVOC']
m1_m2 = [0.673, 0.293, 1.699, 0.376, 16.986, 16.883]
m3_m2 = [0.448, 0.228, 0.098, 0.470, 1.196, 7.792]

x = np.arange(len(sensores))  # posiciones para los grupos
width = 0.35  # ancho de las barras

fig, ax = plt.subplots(figsize=(10,6))
bar1 = ax.bar(x - width/2, m1_m2, width, label='M1/M2 (%)')
bar2 = ax.bar(x + width/2, m3_m2, width, label='M3/M2 (%)')

ax.set_xlabel('Sensor')
ax.set_ylabel('Porcentaje (%)')
ax.set_title('Porcentaje de diferencia entre sensores')
ax.set_xticks(x)
ax.set_xticklabels(sensores)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.show()
