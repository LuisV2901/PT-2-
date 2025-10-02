from Diccionario_modelos import modelos as Diccionario_modelos
from Diccionario_modelos import marcas as Diccionario_marcas
import pandas as pd

class rollo:
    def __init__(self, largo, marca, color):
        self.largo = largo
        self.marca = marca
        self.color = color
        self.lienzos_usados = 0

    def calcular_lienzos(self, largo_tendido):
        return round(self.largo / largo_tendido)
    
    def informacion_rollo(self):
        return f"Rollo - Largo: {self.largo}, Marca: {self.marca}, Color: {self.color}"
    
class habilitacion:
    def __init__(self, rollos, piezas_totales, Valores_Tallas, modelo, total_tallas):
        self.etiquetas_bordadas = 0
        self.instrucciones_lavado = 0
        self.ganchos = 0
        self.tallas = []
        
        self.etiqueta_carton = 0
        self.plastifechas = 0
        self.codigos_barras = []

        self.cierres = []
        self.botones = []

        self.rollos = rollos
        self.piezas_totales = piezas_totales
        self.valores_tallas = Valores_Tallas
        self.total_tallas = total_tallas

        self.modelo = modelo
        self.lista_tallas_cantidades = []

        self.definir_valores_totales()

    def obtener_colores_rollos(self):
        colores = set()
        for rollo in self.rollos:
            if rollo.color not in colores:
                colores.add(rollo.color)
        return list(colores)
    
    def definir_valores_totales(self):
        self.etiquetas_bordadas = self.piezas_totales
        self.instrucciones_lavado = self.piezas_totales
        self.ganchos = self.piezas_totales
        self.etiqueta_carton = self.piezas_totales
        self.plastifechas = self.piezas_totales
    
    def cantidad_por_color(self):
        colores = {}
        for rollo in self.rollos:
            if rollo.color in colores:
                colores[rollo.color] += rollo.lienzos_usados
            else:
                colores[rollo.color] = rollo.lienzos_usados
        return colores


class corte:
    def __init__(self):
        self.modelo = input("Ingrese el modelo: ")
        self.marca = Diccionario_modelos[int(self.modelo)]["Marca"]
        print(f"Marca del modelo {self.modelo}: {self.marca}")
        
        self.largo_tendido = float(input("Ingrese el largo del tendido: "))
        self.tallas = []
        self.valores_tallas = {}

        self.total_tallas = 0
        self.rollos = []
        self.lienzos_totales = 0
        self.otro_rollo = True

        self.piezas_totales = 0
        self.lista_tallas_cantidades = []

        self.agregar_tallas()
        self.agregar_rollo()
        self.calcular_piezas_totales()

    def agregar_tallas(self):
        while True:
            talla = input("Ingrese una talla (o 'salir' para terminar): ")
            if talla.lower() == 'salir':
                break
            try:
                talla = int(talla)
                if talla in self.tallas:
                    print("La talla ya existe.")
                else:
                    self.tallas.append(talla)
                    valor = float(input(f"Ingrese el valor para la talla {talla}: "))
                    self.valores_tallas[talla] = valor
                    self.total_tallas += valor
            except ValueError:
                print("Por favor, ingrese un número válido para la talla.")
        print("Tallas actualizadas:", self.tallas)
        print("Valores de tallas actualizados:", self.valores_tallas)
        print("Total de valores de tallas:", self.total_tallas)

    def agregar_rollo(self):
        while self.otro_rollo !=False:
            largo_rollo = float(input("Ingrese el largo del rollo: "))
            marca_rollo = input("Ingrese la marca del rollo: ")
            color_rollo = input("Ingrese el color del rollo: ")
            nuevo_rollo = rollo(largo_rollo, marca_rollo, color_rollo)
            self.rollos.append(nuevo_rollo)
            lienzos = input(f"Los lienzos colocados son: {nuevo_rollo.calcular_lienzos(self.largo_tendido)}? (s/n): ").lower()
            if lienzos == 's':
                self.lienzos_totales += nuevo_rollo.calcular_lienzos(self.largo_tendido)
                nuevo_rollo.lienzos_usados = nuevo_rollo.calcular_lienzos(self.largo_tendido)
            else:
                lienzos = int(input("Ingrese el número correcto de lienzos colocados: "))
                self.lienzos_totales += lienzos
                nuevo_rollo.lienzos_usados = lienzos
            respuesta = input("¿Desea agregar otro rollo? (s/n): ").lower()
            if respuesta != 's':
                self.otro_rollo = False

    def calcular_piezas_totales(self):
        self.piezas_totales = self.lienzos_totales * self.total_tallas
        for talla in self.tallas:
            cantidad = self.lienzos_totales * self.valores_tallas[talla]
            self.lista_tallas_cantidades.append((talla, cantidad))
        return self.piezas_totales

print("Bienvenido al sistema de Fabricacion")

Nuevo_corte = corte()
Nueva_habilitacion = habilitacion(Nuevo_corte.rollos, Nuevo_corte.piezas_totales, Nuevo_corte.valores_tallas, Nuevo_corte.modelo, Nuevo_corte.total_tallas)
print("\n--- DETALLES DEL TENDIDO ---") 

print(f"Total de lienzos colocados: {Nuevo_corte.lienzos_totales}")

print(f"Valores de Tallas: {Nuevo_corte.valores_tallas}")
print(f"Tallas totales: {Nuevo_corte.total_tallas}" )

print(f"Piezas totales a producir: {Nuevo_corte.piezas_totales}")
print(f"Lista de tallas y cantidades: {Nuevo_corte.lista_tallas_cantidades}")

print("\n--- DETALLES DE LA HABILITACION ---") 
print(f"Modelo: {Nueva_habilitacion.modelo}")
print(f"Marca: {Nuevo_corte.marca}")
print(f"\nColores de los rollos utilizados: {Nueva_habilitacion.obtener_colores_rollos()}")
print(f"Etiquetas bordadas de la marca {Nuevo_corte.marca}: {Nueva_habilitacion.etiquetas_bordadas}")
print(f"Instrucciones de lavado: {Nueva_habilitacion.instrucciones_lavado}")
print(f"Ganchos: {Nueva_habilitacion.ganchos}")
print("\nTallas y cantidades:")
for talla, cantidad in Nuevo_corte.lista_tallas_cantidades:
    print(f"Talla: {talla}, Cantidad: {cantidad}")


print("\nCantidad por color de rollos usados:")
cantidades_color = Nueva_habilitacion.cantidad_por_color()

for color, cantidad in cantidades_color.items():
    print(f"Color: {color}, Cantidad de lienzos usados: {cantidad} por cantidad de tallas {Nuevo_corte.total_tallas} da un total de {cantidad * Nuevo_corte.total_tallas} piezas")
    Nueva_habilitacion.cierres.append((color, cantidad * Nuevo_corte.total_tallas * Diccionario_modelos[int(Nuevo_corte.modelo)]["Cierres"]))
    Nueva_habilitacion.botones.append((color, cantidad * Nuevo_corte.total_tallas * Diccionario_modelos[int(Nuevo_corte.modelo)]["Botones"]))

print("\nCierres:")
for color, cantidad in Nueva_habilitacion.cierres:
    print(f"Color {color}: {cantidad}")
print("\nBotones: ")
for color, cantidad in Nueva_habilitacion.botones:
    print(f"Color {color}: {cantidad}")

print(f"\nEtiqueta de cartón de la marca {Nuevo_corte.marca}: {Nueva_habilitacion.etiqueta_carton}")
print(f"Plastifechas: {Nueva_habilitacion.plastifechas}")
print(f"Códigos de barras: {Nueva_habilitacion.codigos_barras}")\

colores = Nueva_habilitacion.obtener_colores_rollos()
tallas = Nuevo_corte.tallas
data = []
Barcodes = []
for color in colores:
    fila = []
    for talla in tallas:
        cantidad_lienzos = sum(r.lienzos_usados for r in Nuevo_corte.rollos if r.color == color)
        cantidad = cantidad_lienzos * Nuevo_corte.valores_tallas[talla]
        fila.append(cantidad)
        # Generar el barcode como un solo string y guardar junto con la cantidad
        barcode = f"{Diccionario_marcas[Nuevo_corte.marca]['Barcode']}{Nuevo_corte.modelo}{color}{talla}"
        Barcodes.append((barcode, cantidad))
    fila.append(sum(fila))  # Total por color (fila)
    data.append(fila)

# Agregar fila de totales por talla (columna)
totales_col = []
for idx, talla in enumerate(tallas):
    total_talla = sum(data[f][idx] for f in range(len(colores)))
    totales_col.append(total_talla)
totales_col.append(sum(totales_col))  # Total general

# Crear DataFrame con totales
columnas = [str(t) for t in tallas] + ['Total']
index = colores + ['Total']
data.append(totales_col)
df = pd.DataFrame(data, columns=columnas, index=index)

print("\n--- MATRIZ DE UNIDADES POR TALLA Y COLOR ---")
print(df)

print("\n--- CÓDIGOS DE BARRAS GENERADOS ---")
for barcode, cantidad in Barcodes:   
    print(f"Barcode: {barcode}, Cantidad: {cantidad}")

print("\n--- Metros de tela utilizados por color ---")
for color, cantidad in Nueva_habilitacion.cantidad_por_color().items():
    metros = cantidad * Nuevo_corte.largo_tendido
    print(f"Color: {color}, Metros de tela utilizados: {metros} metros")


    

    
    