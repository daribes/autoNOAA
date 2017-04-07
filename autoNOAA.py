#!/usr/bin/env python

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
    print "Intente instalarlo usando: \"sudo apt install predict\"\n"
    sys.exit(1)

os.system("nohup gnome-terminal -e 'predict -s' &")

# Hacemos que cuando acabe se vuelva a repetir
while True:
    def signal_handler(signal, frame):
        print(' SALIDA CORRECTA')
        nproceso = int(get_pid("predict"))
        if nproceso:
            os.system("kill "+str(nproceso))
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    ruta = os.environ['HOME']+'/.predict/predict.qth'
    if not os.path.isfile(ruta):
        print('ERROR: NO EXISTEN DATOS PARA LA ESTACION LOCAL (QTH) EN PREDICT. CONFIGURELO PRIMERO.')
        sys.exit(0)

    ruta = os.environ['HOME']+'/.predict/predict.tle'
    #if not os.path.isfile(ruta):
    #    print('ERROR: NO EXISTEN DATOS DE CORRECCIONES DE TELEMETRIA.')
    #    sys.exit(0)

    def crea_tle(ruta):
        print 'ATENCION: El archivo predict.tle no es correcto, SE RECONSTRUYE'
        print 'SYS: Descargando datos de telemetria'
        os.system(str(os.getcwd()+'/actu_tle'))
        print 'SYS: Datos de telemetria descargados'
        print 'SYS: Reconstruyendo archivo predict.tle'
        rarchivo = str(os.getcwd()+'/weather.txt')
        archivo = open(rarchivo, "r")
        if os.path.isfile(ruta):
            os.remove(ruta)
        tarchivo = open(ruta, "w")
        activado = False
        for linea in archivo.readlines():
            tlinea = linea[0]+linea[1]+linea[2]+linea[3]+linea[4]+linea[5]+linea[6]
            if not activado:
                if tlinea == 'NOAA 15':
                    tarchivo.write('NOAA-15\n')
                    activado = True
                    cuenta = 1
                elif tlinea == 'NOAA 18':
                    tarchivo.write('NOAA-18\n')
                    activado = True
                    cuenta = 1
                elif tlinea == 'NOAA 19':
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

    if not os.path.isfile(ruta):
        #print "SYS: Creamos tle proque no existe el archivo"
        crea_tle(ruta)
    else:
        lineas = len(open(ruta).readlines())
        if lineas != 9:
            #print "SYS: Creamos tle porque no coincide el numero de lineas"
            crea_tle(ruta)


    def get_pid(name):
        return check_output(["pidof",name])

    # Ejecutamos predict en modo servidor en un terminal a parte
    """def daemon_predict():
        os.system("gnome-terminal -e 'predict -s'")

    def server_predict(estado):
        if estado:
            d = threading.Thread(target=daemon_predict, name='daemon_predict')
            d.setDaemon(True)
            d.start()
        else:
            nproceso = int(get_pid("predict"))
            os.system("kill "+str(nproceso))

    #os.system("gnome-terminal -e 'predict -s'")
    server_predict(1)"""

    # Recogemos el identificador de proceso de predict para luego cerrarlo
    # y comprobamos que se ha iniciado
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
    noaa15 = []
    data=str("GET_QTH")
    s.sendto(data,(addr,port))
    data,addr=s.recvfrom(1024)
    qth = data.split("\n")
    qth.pop(len(qth)-1)
    s.close

    # Realizamos la conexion al servidor de predict
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    port=1210
    addr="127.0.0.1"
    # Recogemos los datos de prediccion de pasadas de satelite NOAA15
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
    #print "Proximo pase NOAA-15"
    #print "Dia: "+inicio_noaa15[2]+" Inicio: "+inicio_noaa15[3]+"UTC Fin: "+fin_noaa15[3]+"UTC"

    # Realizamos la misma operacion que con el NOAA15 pero para el NOAA18
    # SEGURAMENTE ESTA OPERACION SE PUEDA OPTIMIZAR EN UNA FUNCION
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
    #print "Proximo pase NOAA-18"
    #print "Dia: "+inicio_noaa18[2]+" Inicio: "+inicio_noaa18[3]+"UTC Fin: "+fin_noaa18[3]+"UTC"

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
    #print "Proximo pase NOAA-19"
    #print "Dia: "+inicio_noaa19[2]+" Inicio: "+inicio_noaa19[3]+"UTC Fin: "+fin_noaa19[3]+"UTC"

    #server_predict(0)
    #os.system("kill "+str(nproceso))
    print "--------- DATOS LOCALES DE QTH ---------"
    print "         Identificador: "+qth[0]
    print "               Latitud: "+qth[1]
    print "              Longitud: "+qth[2]
    print "               Altitud: "+qth[3]
    print "----------------------------------------"

    def utctolocal(dato):
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()
        # utc = datetime.utcnow()
        utc = datetime.strptime(dato, '%d%b%y %H:%M:%S')
        # Tell the datetime object that it's in UTC time zone since
        # datetime objects are 'naive' by default
        utc = utc.replace(tzinfo=from_zone)
        # Convert time zone
        central = utc.astimezone(to_zone)
        central = str(central)
        central = central[:len(central)-6]
        return central

    dif = datetime.utcnow().strftime('%Y%m%d %H:%M:%S')
    dif1 = time.mktime(time.strptime(dif, "%Y%m%d %H:%M:%S"))

    hinoaa15 = time.mktime(time.strptime(utctolocal(inicio_noaa15[2]+" "+inicio_noaa15[3]), "%Y-%m-%d %H:%M:%S"))
    dpnoaa15 = time.mktime(time.strptime(fin_noaa15[3], "%H:%M:%S"))-time.mktime(time.strptime(inicio_noaa15[3], "%H:%M:%S"))
    restante15 = hinoaa15 - dif1

    hinoaa18 = time.mktime(time.strptime(utctolocal(inicio_noaa18[2]+" "+inicio_noaa18[3]), "%Y-%m-%d %H:%M:%S"))
    dpnoaa18 = time.mktime(time.strptime(fin_noaa18[3], "%H:%M:%S"))-time.mktime(time.strptime(inicio_noaa18[3], "%H:%M:%S"))
    restante18 = hinoaa18 - dif1

    hinoaa19 = time.mktime(time.strptime(utctolocal(inicio_noaa19[2]+" "+inicio_noaa19[3]), "%Y-%m-%d %H:%M:%S"))
    dpnoaa19 = time.mktime(time.strptime(fin_noaa19[3], "%H:%M:%S"))-time.mktime(time.strptime(inicio_noaa19[3], "%H:%M:%S"))
    restante19 = hinoaa19 - dif1

    print "PROXIMAS PASADAS DEFINIDAS EN:"
    print "Inicio NOAA15 "+str(utctolocal(inicio_noaa15[2]+" "+inicio_noaa15[3]))+" LOCAL - "+str(inicio_noaa15[3]+" UTC")
    print "Inicio NOAA18 "+str(utctolocal(inicio_noaa18[2]+" "+inicio_noaa18[3]))+" LOCAL - "+str(inicio_noaa18[3]+" UTC")
    print "Inicio NOAA19 "+str(utctolocal(inicio_noaa19[2]+" "+inicio_noaa19[3]))+" LOCAL - "+str(inicio_noaa19[3]+" UTC")

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

    sat15 = satl("NOAA15",hinoaa15,dpnoaa15,"137620000")
    sat18 = satl("NOAA18",hinoaa18,dpnoaa18,"137912500")
    sat19 = satl("NOAA19",hinoaa19,dpnoaa19,"137100000")

    """sat15 = satl("NOAA15",hinoaa15,dpnoaa15,"88900000")
    sat18 = satl("NOAA18",hinoaa18,dpnoaa18,"92500000")
    sat19 = satl("NOAA19",hinoaa19,dpnoaa19,"102200000")"""

    l = [sat15,sat18,sat19]
    l.sort()

    def daemon(frq):
        #os.system("rtl_fm -M wbfm -f "+frq+" -s 200000 -r 48k - | aplay -r 48k -f S16_LE")
        os.system("rtl_fm -M fm -f "+frq+" -s 200000 -r 48k - | aplay -r 11025 -f S16_LE")

    def abrir_cerrar(estado):
        if estado:
            print("Sintonizamos "+l[0].a+" en "+l[0].d)
            d = threading.Thread(target=daemon, args=(l[0].d,))
            d.setDaemon(True)
            d.start()
        else:
            print("Paramos...")
            nproceso = int(get_pid("rtl_fm"))
            print "kill "+str(nproceso)+" -9"
            os.system("kill "+str(nproceso))

    programador = sched.scheduler(time.time, time.sleep)

    comienzo = int(l[0].b)
    t1 = comienzo + 1
    t2 = t1 + l[0].c
    """comienzo = int(time.time()+4)
    t1 = comienzo + 1
    t2 = t1 + 4"""
    print "ESPERANDO PARA INICIAR EN: "+str(datetime.fromtimestamp(l[0].b).strftime('%Y-%m-%d %H:%M:%S'))+" para "+l[0].a+" que durara hasta "+str(datetime.fromtimestamp(t2).strftime('%Y-%m-%d %H:%M:%S'))+" en "+l[0].d

    programador.enterabs(t1, 1, abrir_cerrar, (1,))
    programador.enterabs(t2, 1, abrir_cerrar, (0,))

    programador.run()
    print "SINTONIZACION FINALIZADA: "+str(time.ctime())

    for x in inicio_noaa15[:]:
        inicio_noaa15.remove(x)
    for x in inicio_noaa18[:]:
        inicio_noaa18.remove(x)
    for x in inicio_noaa19[:]:
        inicio_noaa19.remove(x)
