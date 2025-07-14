from ib_insync import *
from datetime import datetime, timezone, timedelta
from dateutil import tz
import struct
import numpy as np
import os
import csv


def borrar_ultimas_n_lineas_min(nombre_archivo, n_lineas):
    TAM_REGISTRO = struct.calcsize("ii f f f f ii")  # 32 bytes por registro
    """
    Borra las últimas `n_lineas` de un archivo .min manteniendo la estructura binaria.

    Parámetros:
        nombre_archivo (str): Ruta del archivo .min.
        n_lineas (int): Número de registros a eliminar (los más recientes).
    """
    try:
        with open(nombre_archivo, "rb") as f:
            datos = f.read()  # Leer todo el archivo en memoria
        
        total_registros = len(datos) // TAM_REGISTRO  # Calcular cuántos registros hay

        if total_registros == 0:
            print("El archivo está vacío, no hay nada que borrar.")
            return

        if n_lineas >= total_registros:
            print("Intentaste borrar más registros de los que existen. Se eliminará todo el archivo.")
            os.remove(nombre_archivo)  # Borra completamente el archivo
            return

        # Obtener solo la parte inicial (excluyendo los últimos `n_lineas` registros)
        datos_restantes = datos[: (total_registros - n_lineas) * TAM_REGISTRO]

        # Sobrescribir el archivo con los datos restantes
        with open(nombre_archivo, "wb") as f:
            f.write(datos_restantes)

        #print(f"Se eliminaron las últimas {n_lineas} líneas de {nombre_archivo} correctamente.")

    except Exception as e:
        print(f"Error al borrar líneas: {e}")


def leer_min(file_path, zona_horaria):
    TAM_REGISTRO = struct.calcsize("ii f f f f ii")  # 32 bytes
    caldayi = []
    tradayi = []
    hora = []
    hii = []
    loi = []
    cli = []
    opi = []
    voli = []

    with open(file_path, "rb") as f:
        f.seek(0, 0)  # Asegurar que leemos desde el principio real

        while True:
            data = f.read(TAM_REGISTRO)
            if len(data) < TAM_REGISTRO:
                break  # Evita errores si el archivo termina antes

            # Desempaquetar datos
            fecha, time, op, hi, lo, cl, vol, _ = struct.unpack("ii f f f f ii", data)

            # Convertir la fecha al formato datetime
            año = fecha // 500
            aux = fecha % 500
            mes = aux // 32
            dia = aux % 32
            hour = time // 3600
            minute = (time % 3600) // 60

            fecha_datetime = datetime(año, mes, dia, hour, minute, tzinfo=tz.gettz(zona_horaria))
            caldayi.append(fecha_datetime)
            tradayi.append(len(caldayi))
            opi.append(op)
            hii.append(hi)
            loi.append(lo)
            cli.append(cl)
            voli.append(vol)

    return caldayi, tradayi, hii, loi, cli, opi, voli


def swing1(hi, lo, cl, op, dhi, dlo):
    dias = len(hi)
    swings = []
    trasw = []
    calsw = []
    
    if op[0] < cl[0]:
        swings.extend([lo[0], hi[0]])
        trasw.extend([1, 1])
        calsw.extend([dlo[0], dhi[0]])
        direccion = 1
    else:
        swings.extend([hi[0], lo[0]])
        trasw.extend([1, 1])
        calsw.extend([dhi[0], dlo[0]])
        direccion = -1
    
    indiceswing = 1
    
    for i in range(dias - 1):
        if (hi[i + 1] > hi[i]) and (lo[i + 1] < lo[i]):  # outside day
            if dlo[i + 1] < dhi[i + 1]:
                if (direccion == 1 and lo[i + 1] < swings[indiceswing]):
                    direccion = -1
                    swings.append(lo[i + 1])
                    trasw.append(i + 1)
                    calsw.append(dlo[i + 1])
                    indiceswing += 1
                elif (direccion == -1 and lo[i + 1] < swings[indiceswing]):
                    swings[indiceswing] = lo[i + 1]
                    trasw[indiceswing] = i + 1
                    calsw[indiceswing] = dlo[i + 1]
                
                direccion = 1
                swings.append(hi[i + 1])
                trasw.append(i + 1)
                calsw.append(dhi[i + 1])
                indiceswing += 1
            else:
                if (direccion == -1 and hi[i + 1] > swings[indiceswing]):
                    direccion = 1
                    swings.append(hi[i + 1])
                    trasw.append(i + 1)
                    calsw.append(dhi[i + 1])
                    indiceswing += 1
                elif (direccion == 1 and hi[i + 1] > swings[indiceswing]):
                    swings[indiceswing] = hi[i + 1]
                    trasw[indiceswing] = i + 1
                    calsw[indiceswing] = dhi[i + 1]
                
                direccion = -1
                swings.append(lo[i + 1])
                trasw.append(i + 1)
                calsw.append(dlo[i + 1])
                indiceswing += 1
        elif hi[i + 1] > hi[i]:
            if (direccion == -1 and hi[i + 1] > swings[indiceswing]):
                direccion = 1
                swings.append(hi[i + 1])
                trasw.append(i + 1)
                calsw.append(dhi[i + 1])
                indiceswing += 1
            elif (direccion == 1 and hi[i + 1] > swings[indiceswing]):
                swings[indiceswing] = hi[i + 1]
                trasw[indiceswing] = i + 1
                calsw[indiceswing] = dhi[i + 1]
        elif lo[i + 1] < lo[i]:
            if (direccion == 1 and lo[i + 1] < swings[indiceswing]):
                direccion = -1
                swings.append(lo[i + 1])
                trasw.append(i + 1)
                calsw.append(dlo[i + 1])
                indiceswing += 1
            elif (direccion == -1 and lo[i + 1] < swings[indiceswing]):
                swings[indiceswing] = lo[i + 1]
                trasw[indiceswing] = i + 1
                calsw[indiceswing] = dlo[i + 1]
    
    return np.array(swings), np.array(calsw), np.array(trasw)


def dividir_min_en_grupos_para_swings(caldayi, hii, loi, cli, opi, voli, n_min_barras, n_grupos, inicio_relativo):
        """
        Divide los datos en grupos hacia atrás y calcula métricas de swing simultáneamente.
        
        Devuelve:
        - grupos: Lista de diccionarios con los datos crudos de cada grupo
        - hi_swings: Array con los máximos high de cada grupo
        - lo_swings: Array con los mínimos low de cada grupo
        - op_swings: Array con los opens más antiguos (primer elemento)
        - cl_swings: Array con los closes más recientes (último elemento)
        - dhi_swings: Array con las fechas donde ocurrieron los máximos
        - dlo_swings: Array con las fechas donde ocurrieron los mínimos
        """

        num_barras = len(caldayi)
        total_min_deseados = n_min_barras * n_grupos

        # Validaciones
        if num_barras < total_min_deseados:
            raise ValueError("No hay suficientes datos para formar los grupos especificados.")
        
        if inicio_relativo is None:
            inicio_relativo = num_barras
            
        if inicio_relativo < total_min_deseados:
            raise ValueError(f"El inicio_relativo ({inicio_relativo}) es insuficiente para {n_grupos} grupos de {n_min_barras} mins.")

        # Inicializamos arrays para los resultados
        hi_swings = np.empty(n_grupos)
        lo_swings = np.empty(n_grupos)
        op_swings = np.empty(n_grupos)
        cl_swings = np.empty(n_grupos)
        dhi_swings = np.empty(n_grupos, dtype=caldayi.dtype)
        dlo_swings = np.empty(n_grupos, dtype=caldayi.dtype)
        
        fin_segmento = inicio_relativo + 1
        inicio_segmento = fin_segmento - total_min_deseados

        for i in range(n_grupos):
            # Calculamos los índices del grupo actual
            
            grupo_inicio = i * n_min_barras
            grupo_fin = grupo_inicio + n_min_barras
            # Extraemos el grupo
            hi_grupo = hii[inicio_segmento + grupo_inicio : inicio_segmento + grupo_fin]
            loi_grupo = loi[inicio_segmento + grupo_inicio : inicio_segmento + grupo_fin]
            
            # Calculamos métricas
            max_hi_idx = np.argmax(hi_grupo)
            min_loi_idx = np.argmin(loi_grupo)
            
            # Almacenamos resultados
            hi_swings[i] = hi_grupo[max_hi_idx]
            lo_swings[i] = loi_grupo[min_loi_idx]
            op_swings[i] = opi[inicio_segmento + grupo_inicio]  # Primer open
            cl_swings[i] = cli[inicio_segmento + grupo_fin - 1]  # Último close
            dhi_swings[i] = caldayi[inicio_segmento + grupo_inicio + max_hi_idx]
            dlo_swings[i] = caldayi[inicio_segmento + grupo_inicio + min_loi_idx]
           
        return hi_swings, lo_swings, cl_swings, op_swings, dhi_swings, dlo_swings


def actualizar_archivo_min(ib, file_path, contract, zona_horaria):
    """Actualiza el archivo .min con nuevos datos."""

    # Guardar barras_totales en un CSV
    def guardar_barras_csv(barras_totales, nombre_archivo="barras_totales.csv"):
        with open(nombre_archivo, mode='w', newline='') as archivo_csv:
            writer = csv.writer(archivo_csv)
            
            # Escribir encabezados (ajusta según los campos de tus barras)
            writer.writerow(["Fecha", "Apertura", "Máximo", "Mínimo", "Cierre", "Volumen"])
            
            # Escribir cada barra (ajusta según la estructura de tus objetos `bar`)
            for bar in barras_totales:
                writer.writerow([
                    bar.date.strftime("%Y-%m-%d %H:%M:%S"),  # Formatear fecha
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume
                ])

    def leer_min(file_path):
        """Lee el último registro del archivo .min y devuelve la fecha más reciente."""
        try:
            with open(file_path, "rb") as f:
                f.seek(-32, 2)
                data = f.read(32)
                if len(data) < 32:
                    return None
                
                fecha, tiempo, *_ = struct.unpack("ii f f f f ii", data)
                ano = fecha // 500
                aux = fecha % 500
                mes = aux // 32
                dia = aux % 32
                hour = tiempo // 3600
                minute = (tiempo % 3600) // 60
                return datetime(ano, mes, dia, hour, minute, tzinfo=tz.gettz(zona_horaria))  
        except FileNotFoundError:
            return None
    
    def escribir_min(file_path, barras):
        """Escribe nuevas barras en el archivo .min evitando duplicados."""
        with open(file_path, "ab") as f:
            for bar in barras:
                dt = bar.date
                fecha = dt.year * 500 + dt.month * 32 + dt.day
                tiempo = dt.hour * 3600 + dt.minute * 60

                data = struct.pack("ii f f f f ii", fecha, tiempo, bar.open, bar.high, bar.low, bar.close, int(bar.volume), 0)
                f.write(data)
    
    ultima_fecha = leer_min(file_path)
    print(f"Última fecha en el archivo de {contract.symbol}: {ultima_fecha}")
    if ultima_fecha is None:
        print(f"Error al leer el archivo {file_path}")
        return

    ahora_utc = datetime.now(timezone.utc)
    diferencia_segundos = int(round((ahora_utc - ultima_fecha.astimezone(timezone.utc)).total_seconds()))
    dias = diferencia_segundos // 86400
    segundos_restantes = diferencia_segundos % 86400
    barras_totales = []
    
    def filtrar_nuevas_barras(barras, fecha):
        return [bar for bar in barras if bar.date > fecha]

    # **Solicitar datos históricos**
    if dias > 0:
        bars = ib.reqHistoricalData(
            contract,
            endDateTime= '',
            durationStr= f"{dias + 1} D",
            barSizeSetting='1 min',
            whatToShow='TRADES',
            useRTH=False,
            formatDate=1
        )
        if bars:
            barras_totales.extend(filtrar_nuevas_barras(bars, ultima_fecha))

        #guardar_barras_csv(bars)
    
    if segundos_restantes > 0:
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=f"{segundos_restantes} S",
            barSizeSetting='1 min',
            whatToShow='TRADES',
            useRTH=False,
            formatDate=1
        )
        if bars:
            barras_totales.extend(filtrar_nuevas_barras(bars, barras_totales[-1].date if barras_totales else ultima_fecha))
    
    if barras_totales:
        escribir_min(file_path, barras_totales)
        borrar_ultimas_n_lineas_min(file_path, 1)  
        print(f"Se han agregado {len(barras_totales)} registros al archivo .min de {contract.symbol}.")
    else:
        print(f"No hay nuevos registros para agregar en {contract.symbol}.")