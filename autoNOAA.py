#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#      Script de sintonizacion automatica de SDR para satelites NOAA       #
############################################################################

import socket
import sys
import os
import time
import sched
from datetime import datetime, timedelta
from dateutil import tz
import signal
import threading
from subprocess import check_output

if not os.path.isfile('/usr/bin/predict'):
    print "No se puede iniciar predict, Parece que no se encuentra instalado en sus sitema\n"
    print "Intente instalarlo usando: \"sudo apt install gpredict\"\n"
    sys.exit(1)

def crea_tle(ruta):
    print 'ATENCION: El archivo predict.tle no es correcto, SE RECONSTRUYE'
    print 'SYS: Descargando elementos keplerianos'
    os.system(str(os.getcwd()+'/actu_tle.py'))
    print 'SYS: Elementos keplerianos descargados'
    print 'SYS: Reconstruyendo archivo predict.tle'
    rarchivo = str(os.getcwd()+'/weather.txt')
    archivo = open(rarchivo, "r")
    if os.path.isfile(ruta):
        os.remove(ruta)
    tarchivo = open(ruta, "w")
    activado = False
    for linea in archivo.readlines():
        if not activado:
            if linea[:6] == 'NOAA 15':
                tarchivo.write('NOAA-15\n')
                activado = True
                cuenta = 1
            elif linea[:6] == 'NOAA 18':
                tarchivo.write('NOAA-18\n')
                activado = True
                cuenta = 1
            elif linea[:6] == 'NOAA 19':
                tarchivo.write('NOAA-19\n')
                activado = True
                cuenta = 1
        else:
            tarchivo.write(linea)
            if cuenta == 2:
                activado = False
            cuenta += 1
    print 'SYS: Archivo predict.tle reconstruido'
    archivo.close
    tarchivo.close
    os.remove(str(os.getcwd()+'/weather.txt'))

ruta = os.environ['HOME']+'/.predict/predict.qth'
if not os.path.isfile(ruta):
    print('ERROR: NO EXISTEN DATOS PARA LA ESTACION LOCAL (QTH) EN PREDICT. CONFIGURELO PRIMERO.')
    pregunta = raw_input("¿Quiere configurarlo ahora? [S] Para configurarlo [N] Para configurarlo con predict")
    if pregunta == 'N':
        sys.exit(0)
    else:
        os.system('predict')

ruta = os.environ['HOME']+'/.predict/predict.tle'
if not os.path.isfile(ruta):
    crea_tle(ruta)
else:
    lineas = len(open(ruta).readlines())
    if lineas != 9:
        crea_tle(ruta)

def get_pid(name):
    return check_output(["pidof",name])

def utctolocal(dato):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = datetime.strptime(dato, '%d%b%y %H:%M:%S')
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    central = str(central)
    central = central[:len(central)-6]
    return central

def daemon_rtl(frq):
    print "SYS: rtl_fm y play conectados"
    os.system("rtl_fm -f "+frq+" -M fm -s 170k -A fast -r 32k -l 0 -E deemp | play -r 11025 -t raw -e s -b 16 -c 1 -V1 - > /dev/null 2>&1")


def sintoniza(estado):
    if estado:
        os.system('clear')
        print "########################################"
        print "#         SISTEMA SINTONIZADO          #"
        print "#            REPRODUCIENDO             #"
        print "########################################"
        print "Sintonizamos "+str(l[0].a)+" en "+str(l[0].d)+" hasta "+str(l[0].c)
        d = threading.Thread(target=daemon_rtl, args=(l[0].d,))
        d.setDaemon(True)
        d.start()
    else:
        print "Paramos..."
        nproceso = int(get_pid("rtl_fm"))
        os.system("kill "+str(nproceso))

class satl:
    def __init__(self,a,b,c,d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    def __str__(self):
        return "a=%s b=%s c=%s d=%s" % (self.a,self.b,self.c,self.d)
    def __cmp__( self, other ) :
        if self.b < other.b :
            rst = -1
        elif self.b > other.b :
            rst = 1
        else:
            rst = 0
        return rst

os.system("gnome-terminal -e 'predict -s' &")
ejecuciones = 0
# Hacemos que cuando acabe se vuelva a repetir
while True:
    os.system("clear")
    ejecuciones += 1
    def signal_handler(signal, frame):
        print ' SALIDA CORRECTA'
        nproceso = int(get_pid("predict"))
        if nproceso:
            os.system("kill "+str(nproceso))
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        nproceso = int(get_pid("predict"))
    except:
        os.system("gnome-terminal -e 'predict -s'")
        try:
            nproceso = int(get_pid("predict"))
        except:
            print "No se ha iniciado predict"
            sys.exit(1)

    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    port=1210
    addr="127.0.0.1"
    # Obtenemos los datos del QTH configurados en predict
    data=str("GET_QTH")
    s.sendto(data,(addr,port))
    data,addr=s.recvfrom(1024)
    qth = data.split("\n")
    if qth[0] == 'W1AW':
        nproceso = int(get_pid("predict"))
        os.system('kill '+str(nproceso))
        print "### ATENCION ### Los datos de la estacion local no han sido configurados."
        print "                 Esto provoca que los datos de prediccion no sean correctos"
        print "                 para su localizacion actual."
        print "   Inicie predict y en la opcion [G] configure estos datos.\n"
        raw_input("Pulsa una tecla para continuar o Ctrl+C para salir")
        for x in qth[:]:
            qth.remove(x)
        data=str("GET_QTH")
        s.sendto(data,(addr,port))
        data,addr=s.recvfrom(1024)
        qth = data.split("\n")
    qth.pop(len(qth)-1)
    s.close
    os.system("gnome-terminal -e 'predict -s'")

    # RECOPILAMOS LOS DATOS PARA NOAA15
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    port=1210
    addr="127.0.0.1"
    noaa15 = []
    data=str("PREDICT NOAA-15")
    s.sendto(data,(addr,port))
    while data[0]!=unichr(26):
        data,addr=s.recvfrom(1024)
        noaa15.append(data)
    s.close

    inicio_noaa15 = noaa15[0].split(" ")
    count = len(inicio_noaa15)
    while count >= 0:
        if inicio_noaa15[count-1] == '':
            inicio_noaa15.pop(count-1)
        count -= 1
    inicio_noaa15.pop(len(inicio_noaa15)-1)

    fin_noaa15 = noaa15[len(noaa15)-2].split(" ")
    count = len(fin_noaa15)
    while count >= 0:
        if fin_noaa15[count-1] == '':
            fin_noaa15.pop(count-1)
        count -= 1
    fin_noaa15.pop(len(fin_noaa15)-1)

    # RECOPILAMOS LOS DATOS PARA NOAA18
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    port=1210
    addr="127.0.0.1"
    noaa18 = []
    data=str("PREDICT NOAA-18")
    s.sendto(data,(addr,port))
    while data[0]!=unichr(26):
        data,addr=s.recvfrom(1024)
        noaa18.append(data)
    s.close

    inicio_noaa18 = noaa18[0].split(" ")
    count = len(inicio_noaa18)
    while count >= 0:
        if inicio_noaa18[count-1] == '':
            inicio_noaa18.pop(count-1)
        count -= 1
    inicio_noaa18.pop(len(inicio_noaa18)-1)

    fin_noaa18 = noaa18[len(noaa18)-2].split(" ")
    count = len(fin_noaa18)
    while count >= 0:
        if fin_noaa18[count-1] == '':
            fin_noaa18.pop(count-1)
        count -= 1
    fin_noaa18.pop(len(fin_noaa18)-1)

    # RECOPILAMOS LOS DATOS PARA NOAA19
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    port=1210
    addr="127.0.0.1"
    noaa19 = []
    data=str("PREDICT NOAA-19")
    s.sendto(data,(addr,port))
    while data[0]!=unichr(26):
        data,addr=s.recvfrom(1024)
        noaa19.append(data)
    s.close

    inicio_noaa19 = noaa19[0].split(" ")
    count = len(inicio_noaa19)
    while count >= 0:
        if inicio_noaa19[count-1] == '':
            inicio_noaa19.pop(count-1)
        count -= 1
    inicio_noaa19.pop(len(inicio_noaa19)-1)

    fin_noaa19 = noaa19[len(noaa19)-2].split(" ")
    count = len(fin_noaa19)
    while count >= 0:
        if fin_noaa19[count-1] == '':
            fin_noaa19.pop(count-1)
        count -= 1
    fin_noaa19.pop(len(fin_noaa19)-1)

    print "--------- DATOS LOCALES DE QTH ---------"
    print "         Identificador: "+qth[0]
    print "               Latitud: "+qth[1]
    print "              Longitud: "+qth[2]
    print "               Altitud: "+qth[3]
    print "----------------------------------------"

    dif = datetime.utcnow().strftime('%Y%m%d %H:%M:%S')
    dif1 = time.mktime(time.strptime(dif, "%Y%m%d %H:%M:%S"))

    hinoaa15 = time.mktime(time.strptime(utctolocal(inicio_noaa15[2]+" "+inicio_noaa15[3]), "%Y-%m-%d %H:%M:%S"))
    dpnoaa15 = time.mktime(time.strptime(fin_noaa15[3], "%H:%M:%S"))-time.mktime(time.strptime(inicio_noaa15[3], "%H:%M:%S"))
    hfnoaa15 = time.mktime(time.strptime(utctolocal(fin_noaa15[2]+" "+fin_noaa15[3]), "%Y-%m-%d %H:%M:%S"))
    restante15 = hinoaa15 - dif1

    hinoaa18 = time.mktime(time.strptime(utctolocal(inicio_noaa18[2]+" "+inicio_noaa18[3]), "%Y-%m-%d %H:%M:%S"))
    dpnoaa18 = time.mktime(time.strptime(fin_noaa18[3], "%H:%M:%S"))-time.mktime(time.strptime(inicio_noaa18[3], "%H:%M:%S"))
    hfnoaa18 = time.mktime(time.strptime(utctolocal(fin_noaa18[2]+" "+fin_noaa18[3]), "%Y-%m-%d %H:%M:%S"))
    restante18 = hinoaa18 - dif1

    hinoaa19 = time.mktime(time.strptime(utctolocal(inicio_noaa19[2]+" "+inicio_noaa19[3]), "%Y-%m-%d %H:%M:%S"))
    dpnoaa19 = time.mktime(time.strptime(fin_noaa19[3], "%H:%M:%S"))-time.mktime(time.strptime(inicio_noaa19[3], "%H:%M:%S"))
    hfnoaa19 = time.mktime(time.strptime(utctolocal(fin_noaa19[2]+" "+fin_noaa19[3]), "%Y-%m-%d %H:%M:%S"))
    restante19 = hinoaa19 - dif1

    print "PROXIMAS PASADAS DEFINIDAS EN:"
    print "Inicio NOAA15 "+str(utctolocal(inicio_noaa15[2]+" "+inicio_noaa15[3]))+" LOCAL - "+str(inicio_noaa15[3]+" UTC")
    print "Inicio NOAA18 "+str(utctolocal(inicio_noaa18[2]+" "+inicio_noaa18[3]))+" LOCAL - "+str(inicio_noaa18[3]+" UTC")
    print "Inicio NOAA19 "+str(utctolocal(inicio_noaa19[2]+" "+inicio_noaa19[3]))+" LOCAL - "+str(inicio_noaa19[3]+" UTC")
    print "----------------------------------------"

    sat15 = satl("NOAA15",hinoaa15,hfnoaa15,"137620000")
    sat18 = satl("NOAA18",hinoaa18,hfnoaa18,"137912500")
    sat19 = satl("NOAA19",hinoaa19,hfnoaa19,"137100000")

    l = [sat15,sat18,sat19]
    l.sort()

    programador = sched.scheduler(time.time, time.sleep)

    comienzo = int(l[0].b)
    t1 = comienzo + 1
    t2 = l[0].c

    print "ESPERANDO PARA INICIAR "+l[0].a+" en "+l[0].d+" Hz\n                 "+str(datetime.fromtimestamp(l[0].b).strftime('%H:%M:%S HORA LOCAL del %Y-%m-%d'))+"\nque durara hasta "+str(datetime.fromtimestamp(t2).strftime('%H:%M:%S HORA LOCAL del %Y-%m-%d'))
    print "\n\nEsta es la ejecucion: "+str(ejecuciones)

    programador.enterabs(t1, 1, sintoniza, (1,))
    programador.enterabs(t2, 1, sintoniza, (0,))
    programador.run()

    print "SINTONIZACION FINALIZADA: "+str(time.ctime())

    for x in inicio_noaa15[:]:
        inicio_noaa15.remove(x)
    for x in inicio_noaa18[:]:
        inicio_noaa18.remove(x)
    for x in inicio_noaa19[:]:
        inicio_noaa19.remove(x)

    print "SYS: Esperando a que se cierre completamente la reproduccion"
    nproceso = int(get_pid("play"))
    while nproceso != 0:
        try:
            nproceso = int(get_pid("play"))
        except:
            nproceso = 0
