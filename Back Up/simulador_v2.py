import numpy as np
import pandas as pd
import funcionesSim as fn

#parametros iniciales del simulador
lambda_ =.5
mu = .8 
tasaCodificacion= 40 # tasaCodificacion Mbps
Lmax = 20 #segundos
tamanioVentana = 40 #tamanioVentana Mb
tasaDescargaMin = 1 #Mbps tasa de descarga minima entre peers
tasaDescargaObj = 30 #Mbps
Q=3
tasaTransmisionPeer = 5 #Mbps


#inicializar variables
eventos = []
tiempos = []
peersAtendidos=4
ID_peer = 0
tiempoActual = 0
Poblacion=0

servidores = {
        "ID servidor" : 1010,  
        "Tasa de transmision Disponible" : 1000, #Mbps
        "Le descargan":[[None]] 
    }
servidoresDatos = pd.DataFrame(servidores)
servidores = servidoresDatos

peers = {
        "ID peer" : 0,
        "Poblacion": 0,
        "Tasa de descarga": 0,  
        "Tasa de transmision Disponible" : 0,
        "Descarga a" : ["s1"],
        "Le descargan": [0],
        "t estimado descarga ventana" : [0]
    }

peersDatos = pd.DataFrame(peers)
peers = peersDatos.drop(0)



#Calcular el numero de ventanas
c = int(fn.NumVentanas(Lmax,tasaCodificacion,tamanioVentana)) #tomar encuenta que las ventanas estan distribuidas con los indices de 0 a c
print("Numero de ventanas: ",c)
Q=c

#Calcular Tiempo de producción de ventana
tiempoProdVentana = fn.CalcularTiempoProdVentana(tasaCodificacion,tamanioVentana,0)
eventos, tiempos = fn.ordenarEventos(eventos,tiempos,tiempoProdVentana,2)

#programar el primer arribo
IDpeer = ID_peer + 1
tiempoArribo,_ = fn.EventoArribo(lambda_,mu,tiempoActual)
eventos, tiempos = fn.ordenarEventos(eventos,tiempos,tiempoArribo,0)

while True:
    tiempoActual = tiempos[0]
    if  eventos[0] == 0:
        print("\n -------------------------------------------------------------")
        print(" Arribo de peer")

        ID_peer = ID_peer + 1
        
        #Programar siguiente arribo y abandono
        tiempoArribo,tiempoAbandono = fn.EventoArribo(lambda_,mu,tiempoActual)
        eventos, tiempos = fn.ordenarEventos(eventos,tiempos,tiempoArribo,0) # 0 evento arribo
        eventos, tiempos = fn.ordenarEventos(eventos,tiempos,tiempoAbandono,1) # 1 evento abandono
        #print(eventos,tiempos)

        #Asignar recursos con un esquema de asignacion
        peers,servidores = fn.EsquemaQventanas(peers,servidores,ID_peer,0,tasaDescargaMin,tasaDescargaObj,tasaTransmisionPeer,Q)
        
        #Calcular tiempo de descarga de ventana 
        peers,tiempoDescarga = fn.CalcularTiempoDescargaVentana(peers, ID_peer, tamanioVentana, tiempoActual)
        
        #Formar evento de transferencia a la ventana superior
        eventos, tiempos = fn.ordenarEventos(eventos,tiempos,tiempoDescarga,3) # 1 Transferencia a la ventana superior
        print(peers)
        
        
    elif eventos[0] == 1:
        print("\n -------------------------------------------------------------")
        print(" Abandono de peer")

    elif eventos[0] == 2:
        print("\n -------------------------------------------------------------")
        print("Transferencia a la ventana inmediata inferior", tiempoActual)
        
        peersDatos = fn.EventoTrfVentanaInf(peers,c)  
        print(peersDatos)

        #calcular el proximo fin de producción de ventana
        tiempoProdVentana = fn.CalcularTiempoProdVentana(tasaCodificacion,tamanioVentana,tiempoActual)
        eventos, tiempos = fn.ordenarEventos(eventos,tiempos,tiempoProdVentana,2)
        #print(eventos,tiempos)


    elif eventos[0] == 3:
        print("\n -------------------------------------------------------------")
        print("Transferencia a la ventana inmediata superior", tiempoActual)

        #calcular siguiente tiempo de ventana
        peers, ID_peerDescarga  = fn.EventoTrfVentanaSuperior(peers, tiempoActual)       
        peers,tiempoDescarga = fn.CalcularTiempoDescargaVentana(peers,ID_peerDescarga, tamanioVentana, tiempoActual)
        
        #Formar evento de transferencia a la ventana superior
        eventos, tiempos = fn.ordenarEventos(eventos,tiempos,tiempoDescarga,3) # 1 Transferencia a la ventana superior

    eventos.pop(0)
    tiempos.pop(0)

    
    
    if ID_peer == peersAtendidos:
        break
        

