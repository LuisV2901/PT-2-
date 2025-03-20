import numpy as np
import pandas as pd
import random



#------------------Funciones para administrar/crear eventos-----------------------------------------------

#Funcion : ordenarEventos ordena los eventos nuevos en el simulador de acuerdo con su tiempo de ejecucion
def ordenarEventos(eventos,tiempos, nuevoTiempo, nuevoEvento):
    eventos.append(nuevoEvento)
    tiempos.append(nuevoTiempo)
    eventosOrdenados = [x for _, x in sorted(zip(tiempos, eventos))] #solo se recupera a eventos de la funcion zip
    tiemposOrdenados = sorted(tiempos)

    return eventosOrdenados, tiemposOrdenados

#Funcion : Calcular el numero de ventanas tomando el intervalo de 0 a Lmax 
def NumVentanas(Lmax, tasaCod, tamanioVentana ): 
    tiempoVentana = tamanioVentana / tasaCod
    NumVentanas =  (Lmax/tiempoVentana) #las ventanas comienzan desde el indice 0

    return NumVentanas


#Funcion : Calcular el tiempo de producción de ventana
def CalcularTiempoProdVentana(tasaCod, tamanioVentana, tiempoActual):
    tiempoProduccion = tamanioVentana  / tasaCod
    tiempoVentana = tiempoProduccion + tiempoActual

    return tiempoVentana

# Funcion: Calcular el tiempo que tarda en descargar una ventana un peer 
def CalcularTiempoDescargaVentana(peers, ID_peer, tamanioVentana, tiempoActual): 

    peersDatos=pd.DataFrame(peers)
    peerSeleccionado=peersDatos.loc[peersDatos["ID peer"] == ID_peer]
    tasaDescargaPeer = peerSeleccionado["Tasa de descarga"].values[0]
    tiempoDescarga = (tamanioVentana / int(tasaDescargaPeer) ) + tiempoActual
    
    peersDatos.loc[peersDatos["ID peer"] == ID_peer, "t estimado descarga ventana" ] = tiempoDescarga
    
    #Nota, para el calculo de latencia promedio, 
    # se debe contemplar cuando se inicio la descarga  y para asi estimar que tanto se ha descargado al tiempo del calculo de latencia promedio
    
    
    return peersDatos,tiempoDescarga



#--------------------------------------------Eventos discretos-------------------------------------------------------

#Funcion : Evento discreto Arribos/Abandonos. Despues de un arribo se debe programar el siguiente arribo y un abandono
def EventoArribo(lambda_, mu, tiempoEvento):
    tea = np.random.exponential(1/lambda_)
    tds = np.random.exponential(1/mu)
    tiempoArribo = tiempoEvento+tea
    tiempoAbandono = tiempoEvento+tds
    
    return tiempoArribo,tiempoAbandono

def EventoTrfVentanaSuperior(peers, tiempoActual):
    #Buscar el peer que termino la descarga de la ventana
    peersDatos=pd.DataFrame(peers)    
    peerDescarga=peersDatos.loc[peersDatos["t estimado descarga ventana"] == tiempoActual] 

    #Actualizar poblacion
    ID_peerDescarga  = peerDescarga.loc[peersDatos["t estimado descarga ventana"] == tiempoActual, 'ID peer'].values[0]
    poblacion = peerDescarga.loc[peersDatos["t estimado descarga ventana"] == tiempoActual, 'Poblacion'].values[0]

    peersDatos.loc[peersDatos["ID peer"] == ID_peerDescarga, "Poblacion" ] = poblacion + 1


    return peersDatos, ID_peerDescarga

#Funcion : Evento discreto Transferencia a la ventana inferior. 
def EventoTrfVentanaInf(peers,numVentanas):
    peersDatos=pd.DataFrame(peers)
    
    for i in range(0, numVentanas): 
      if i == 0 :
          # Encontrar los índices de las filas donde "Poblacion" es 0
         indices_a_eliminar = peersDatos[peersDatos["Poblacion"] == i].index

        # Eliminar las filas usando el método drop
         peersDatos = peersDatos.drop(indices_a_eliminar)
      else :    
         peersDatos.loc[(peersDatos["Poblacion"] == i ),"Poblacion"] = i - 1 

    return peersDatos




#-------------------------------------------Esquemas de asignación----------------------------------------------------
#Nota _v1 : aqui se asume que siempre se cumple con la tasa de descarga objetivo


#Funcion : Esquema de asignacion Q ventanas 
def EsquemaQventanas(peers,servidores,ID_peer,poblacion,tasaDescargaMin,tasaDescargaObj,tasaTransmisionPeer,Q):
   
    asignacionPeer = False
    peersDatos=pd.DataFrame(peers)
    tasaDescargaPeer = 0 
    descargaA = []
   
    # Buscar peers que se encuentren en las siguientes Q ventanas posteriores (poblacion + 1)
    for i in range(poblacion+1,  poblacion + Q ): 
         nPeer = []
         if tasaDescargaPeer < tasaDescargaObj : 
            
            peersPoblacion = peersDatos.loc[(peersDatos["Poblacion"] == i ) & (peersDatos["Tasa de transmision Disponible"] >= tasaDescargaMin)]
             #buscar los peers que puedan proporcionar la tasa de descarga minima
            if len(peersPoblacion)>0 :
                    k=1
                    #seleccionar hasta que 
                    while True: 
                        
                        if len(nPeer) < len(peersPoblacion) :
                            
                            print("No. peer",k,len(peersPoblacion))
                            k = k + 1
                            #seleccionar un peer al azar
                            while True:
                                nrandom = random.randint(1, len(peersPoblacion)) 

                                if nrandom not in nPeer and nrandom != ID_peer  :
                                    nPeer.append(nrandom)
                                    break  # Rompe el ciclo cuando se agrega un número no repetido


                            index_to_access =  nPeer[-1] 
                            print("index",index_to_access)
                            try:    
                                    print("PEERS POBLACION")
                                    print(peersPoblacion)
                                    peerCandidato = peersPoblacion.loc[index_to_access - 1]
                                    ID_peerCandidato = peerCandidato.at["ID peer"]
                                    tasaTransmisionCandidato = peerCandidato.at["Tasa de transmision Disponible"]
                                    #descargan = peersDatos.loc[peersDatos['ID peer'] == ID_peerCandidato, 'Le descargan'].values[0]
                                        
                                    #Actualizar TASA DE TRANSMISION DISPONIBLE (tasaTransmision-tasaDescargaMin) donde TasaDescargaMin es la tasa de descarga ofrecida por el peer candidato
                                    peersDatos.loc[peersDatos["ID peer"] == ID_peerCandidato, "Tasa de transmision Disponible" ] = tasaTransmisionCandidato - tasaDescargaMin 
                                    
                                    #Actualizar lista de peers que LE DESCARGAN al peer candidato
                                    #descargan.append(ID_peer)
                                    peersDatos = AgregarListaPeers(peers, ID_peerCandidato, "Le descargan", ID_peer)
                                    
                                    # tasa de descarga actual + la tasa de descarga ofrecida por el peer 
                                    tasaDescargaPeer = tasaDescargaPeer + tasaDescargaMin 

                                    #Actualizar lista DESCARGA A
                                    descargaA.append(ID_peerCandidato)
                                    print("YAYAYAYAYAYA")

                            except KeyError as e:
                                print(f'Error: {e}')
                                print(f'Index {index_to_access} not found in DataFrame')    
                                



                        else :
                            break
               
         else:
                #Asignar recursos al peer # agregar uno por uno para tener un vector y no [[]]
                
                peersDatos = registroPeer(peers,ID_peer,poblacion,tasaDescargaPeer,tasaTransmisionPeer,None,None,None)
                peersDatos = AgregarListaPeers(peers, ID_peer, "Descarga a", descargaA)
                asignacionPeer = True
            
            
    if i == poblacion + Q - 1 and asignacionPeer == False : #agregar q si tiene datos disponibles hacer esto
        
        print("ASIGNACION DE RECURSOS DESDE EL SERVIDOR")
        #Se realiza la asignacion de recursos con el servidor
        tasaFaltante = tasaDescargaObj - tasaDescargaPeer
        
        #seleccionar un servidor al azar
        servidoresDatos=pd.DataFrame(servidores) 
        
        nrandom = random.randint(1, len(servidoresDatos))
        servidor = servidoresDatos.loc[- 1 + nrandom]

        ID_servidor = servidor.at["ID servidor"]
        tasaTransmisionServidor = servidor.at["Tasa de transmision Disponible"]
        servidoresDatos.loc[servidoresDatos["ID servidor"] == ID_servidor, "Tasa de transmision Disponible" ] = tasaTransmisionServidor - tasaFaltante                    
        
        servidoresDatos = AgregarListaServidor(servidoresDatos, ID_servidor, "Le descargan", ID_peer)
        
        descargaA.append(ID_servidor)
        
        peersDatos = registroPeer(peers,ID_peer,poblacion,tasaDescargaObj,tasaTransmisionPeer,descargaA,None,None)

    return peersDatos, servidoresDatos


#---------------------------------FUNCIONES PARA ADMINISTRAR LOS DATAFRAMES----------------------------


# Funcion para agregar un peer al dataframe
def registroPeer(peers,ID_peer,poblacion,tasaDescargaObj,tasaTransmisionPeer,descargaA, descargan,tiempoVentana):
  
    peersDatos=pd.DataFrame(peers)
    nuevaAsignacion = pd.DataFrame({
        "ID peer": [ID_peer], 
        "Poblacion": [poblacion],
        "Tasa de descarga":[ tasaDescargaObj],
        "Tasa de transmision Disponible": [tasaTransmisionPeer],
        "Descarga a":[[descargaA]],
        "Le descargan" :[[descargan]],
        "t estimado descarga ventana" : [tiempoVentana]
    })
    peersDatos = pd.concat([peersDatos, nuevaAsignacion], ignore_index=True)
    return peersDatos

# Función para agregar un valor a la lista en una celda específica
def AgregarListaPeers(peers, id_peer, columna, nuevo_valor):
    
    fila = peers.loc[peers['ID peer'] == id_peer]
    
    if fila.empty:
        print(f"No se encontró el ID peer {id_peer}.")
        return

    # Acceder a la celda específica
    idx = peers[peers['ID peer'] == id_peer].index[0]
    lista_actual = peers.at[idx, columna]
    
    if None in lista_actual:
        lista_actual.remove(None)

    if lista_actual is None:
        lista_actual = []
    
    if not isinstance(nuevo_valor, list):
        nuevo_valor = [nuevo_valor]
    
    # Agregar el nuevo valor a la lista
    lista_actual.extend(nuevo_valor)
    
    peers.at[idx, columna] = lista_actual
    
    return peers


# Función para agregar un valor a la lista en una celda específica
def AgregarListaServidor(servidores, id_servidor, columna, nuevo_valor):
    
    fila = servidores.loc[servidores['ID servidor'] == id_servidor]
    
    if fila.empty:
        print(f"No se encontró el ID  {id_servidor}.")
        return

    # Acceder a la celda específica
    idx = servidores[servidores['ID servidor'] == id_servidor].index[0]
    lista_actual = servidores.at[idx, columna]
    
    if None in lista_actual:
        lista_actual.remove(None)

    if lista_actual is None:
        lista_actual = []
    
    if not isinstance(nuevo_valor, list):
        nuevo_valor = [nuevo_valor]
    
    # Agregar el nuevo valor a la lista
    lista_actual.extend(nuevo_valor)
    
    servidores.at[idx, columna] = lista_actual
    
    return servidores

