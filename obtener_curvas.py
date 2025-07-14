import pandas as pd
import struct
from datetime import datetime, timezone, timedelta
import numpy as np
from variables_backtest import variables_backtest

def curva(file_path, umbral, variacion_minima, R, swing_largo, swing_corto, n_grupos, numero_decimales):

    
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
    

    def leer_min(file_path):
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

                fecha_datetime = datetime(año, mes, dia, hour, minute, tzinfo=timezone.utc)
                caldayi.append(fecha_datetime)
                tradayi.append(len(caldayi))
                opi.append(op)
                hii.append(hi)
                loi.append(lo)
                cli.append(cl)
                voli.append(vol)

        return caldayi, tradayi, hii, loi, cli, opi, voli
    
    
    def dividir_min_en_grupos_para_swings(caldayi, hii, loi, cli, opi, voli, n_min_barras, n_grupos, inicio_relativo):
        
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
        
        grupos = []
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
    
    def backtest_doble_top_bottom_limit(swings, swing_times, high_actual, low_actual, umbral, variacion_minima, R_multiplier, num_decimales, i):
        # Configuración del archivo de log
        log_file = "backtest_traces.log"
        
        # Función auxiliar para escribir en el log
        def write_log(message):
            with open(log_file, 'a') as f:
                f.write(f"{caldayi[i]}: {message}\n")
        
        tiempo_max_espera = timedelta(minutes=5)
        RESET_VALUES_LIMIT = {
            'tipo': None,
            'swing_detectado': None,
            'tiempo_deteccion': None,
            'entry_limit_price': 0.0,
            'stop_loss_price': 0.0,
            'take_profit_price': 0.0,
            'en_espera': False,
            'tiempo_orden': 0,
            'entry_limit_pendiente': False,
            'entry_limit_ejecutada': False
        }

        lsw = len(swings)

        if variables_backtest['entry_limit_pendiente'] is True:
            if variables_backtest['tipo'] == 'double_top':
                if loi[i] <= variables_backtest['entry_limit_price']:
                    write_log(f"ENTRADA EJECUTADA - Double Top. Precio: {variables_backtest['entry_limit_price']}")
                    variables_backtest['entry_limit_pendiente'] = False
                    variables_backtest['entry_limit_ejecutada'] = True
                    return
                else:
                    if variables_backtest['en_espera'] is True:
                        if variables_backtest['tiempo_orden'] > 0:
                            variables_backtest['tiempo_orden'] -= 1
                            return
                        write_log("RESET - Tiempo de espera agotado (Double Top)")
                        variables_backtest.update(RESET_VALUES_LIMIT)
                    elif variables_backtest['en_espera'] is False:    
                        if swings[-1] > swings[-2]:  # posible double top
                            for k in range(1, (lsw - 1) // 2 + 1):
                                dif = swings[-1] - swings[(-2 * k)-1]
                                if abs(dif) < umbral:
                                    write_log("NO SE EJECUTO LA ORDEN, CANCELANDO")
                                    variables_backtest.update(RESET_VALUES_LIMIT)
                                    break
                                elif dif <= -umbral:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5  
                                    return
                                else:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5  
                                    return
                        else:
                            write_log("EN ESPERA 5 MIN MÁS")
                            variables_backtest['en_espera'] = True
                            variables_backtest['tiempo_orden'] = 5  
                            return


            elif variables_backtest['tipo'] == 'double_bottom':
                if hii[i] >= variables_backtest['entry_limit_price']:
                    write_log(f"ENTRADA EJECUTADA - Double Bottom. Precio: {variables_backtest['entry_limit_price']}")
                    variables_backtest['entry_limit_pendiente'] = False
                    variables_backtest['entry_limit_ejecutada'] = True
                    return
                else:
                    if variables_backtest['en_espera'] is True:
                        if variables_backtest['tiempo_orden'] > 0:
                            variables_backtest['tiempo_orden'] -= 1
                            return
                        write_log("RESET - Tiempo de espera agotado (Double Bottom)")
                        variables_backtest.update(RESET_VALUES_LIMIT)
                    elif variables_backtest['en_espera'] is False:    
                        if swings[-1] < swings[-2]:  # posible double bottom
                            for k in range(1, (lsw - 1) // 2 + 1):
                                dif = swings[-1] - swings[(-2 * k)-1]
                                if abs(dif) < umbral:
                                    write_log("NO SE EJECUTO LA ORDEN, CANCELANDO")
                                    variables_backtest.update(RESET_VALUES_LIMIT)
                                    break
                                elif dif >= umbral:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5   
                                    return
                                else:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5   
                                    return
                        else:
                            write_log("EN ESPERA 5 MIN MÁS")
                            variables_backtest['en_espera'] = True
                            variables_backtest['tiempo_orden'] = 5   
                            return         

        if variables_backtest['entry_limit_ejecutada'] is True:
            if variables_backtest['tipo'] == 'double_top':
                if hii[i] >= variables_backtest['take_profit_price']:
                    write_log(f"SALIDA POR STOP LOSS - Double Top. Precio: {variables_backtest['take_profit_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['take_profit_price'] - variables_backtest['entry_limit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['take_profit_price'] - variables_backtest['entry_limit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT)

                elif loi[i] <= variables_backtest['stop_loss_price']:
                    write_log(f"SALIDA POR TAKE PROFIT - Double Top. Precio: {variables_backtest['stop_loss_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['stop_loss_price'] - variables_backtest['entry_limit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['stop_loss_price'] - variables_backtest['entry_limit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT)

                else:
                    return        

            elif variables_backtest['tipo'] == 'double_bottom':
                if loi[i] <= variables_backtest['take_profit_price']:
                    write_log(f"SALIDA POR STOP LOSS - Double Bottom. Precio: {variables_backtest['take_profit_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_limit_price'] - variables_backtest['take_profit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_limit_price'] - variables_backtest['take_profit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT) 

                elif hii[i] >= variables_backtest['stop_loss_price']:
                    write_log(f"SALIDA POR TAKE PROFIT - Double Bottom. Precio: {variables_backtest['stop_loss_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_limit_price'] - variables_backtest['stop_loss_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_limit_price'] - variables_backtest['stop_loss_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES_LIMIT)

                else:
                    return        

        if swings[-1] < swings[-2]:  # posible double bottom
            for k in range(1, (lsw - 1) // 2 + 1):
                dif = swings[-1] - swings[(-2 * k)-1]
                if abs(dif) < umbral:
                    write_log(f"PATRÓN DETECTADO - Double Bottom. Swing: {swings[-1]}, Tiempo: {swing_times[-1]}")
                    variables_backtest['tipo'] = 'double_bottom'
                    variables_backtest['swing_detectado'] = swings[-1]
                    variables_backtest['tiempo_deteccion'] = swing_times[-1]
                    break
                elif dif >= umbral:
                    break

        elif swings[-1] > swings[-2]:  # posible double top
            for k in range(1, (lsw - 1) // 2 + 1):
                dif = swings[-1] - swings[(-2 * k)-1]
                if abs(dif) < umbral:
                    write_log(f"PATRÓN DETECTADO - Double Top. Swing: {swings[-1]}, Tiempo: {swing_times[-1]}")
                    variables_backtest['tipo'] = 'double_top'
                    variables_backtest['swing_detectado'] = swings[-1]
                    variables_backtest['tiempo_deteccion'] = swing_times[-1]
                    break
                elif dif <= -umbral:
                    break

        # --- NUEVAS VALIDACIONES ---
        if variables_backtest['tipo'] and variables_backtest['swing_detectado'] and variables_backtest['tiempo_deteccion']:
            # 1. Verificar que no hayan pasado más de 5 minutos desde la detección
            tiempo_actual = caldayi[i]
            tiempo_transcurrido = tiempo_actual - variables_backtest['tiempo_deteccion']

            if tiempo_transcurrido > tiempo_max_espera:
                write_log("RESET - Tiempo máximo de espera excedido")
                variables_backtest.update(RESET_VALUES_LIMIT)
                return
            
            # 2. Verificar que el precio actual está dentro del rango permitido
            precio_actual = high_actual if variables_backtest['tipo'] == 'double_bottom' else low_actual
            distancia_al_swing = abs(precio_actual - variables_backtest['swing_detectado'])

            if distancia_al_swing > umbral:
                write_log(f"RESET - Distancia al swing excedida. Distancia: {distancia_al_swing}, Umbral: {umbral}")
                variables_backtest.update(RESET_VALUES_LIMIT)
                return
            
            if variables_backtest['tipo'] == 'double_top':
                variables_backtest['entry_limit_price'] = round(low_actual - variacion_minima, num_decimales)
                variables_backtest['take_profit_price'] = round(swings[-1] + variacion_minima, num_decimales)
                variables_backtest['stop_loss_price'] = round(variables_backtest['entry_limit_price'] - (R_multiplier * (variables_backtest['take_profit_price'] - variables_backtest['entry_limit_price'])), num_decimales)
                variables_backtest['entry_limit_pendiente'] = True
                write_log(f"ORDEN CONFIGURADA - Double Top. Entry: {variables_backtest['entry_limit_price']}, SL: {variables_backtest['stop_loss_price']}, TP: {variables_backtest['take_profit_price']}")

            elif variables_backtest['tipo'] == 'double_bottom':
                variables_backtest['entry_limit_price'] = round(high_actual + variacion_minima, num_decimales)
                variables_backtest['take_profit_price'] = round(swings[-1] - variacion_minima, num_decimales)
                variables_backtest['stop_loss_price'] = round(variables_backtest['entry_limit_price'] + (R_multiplier * (variables_backtest['entry_limit_price'] - variables_backtest['take_profit_price'])), num_decimales)
                variables_backtest['entry_limit_pendiente'] = True
                write_log(f"ORDEN CONFIGURADA - Double Bottom. Entry: {variables_backtest['entry_limit_price']}, SL: {variables_backtest['stop_loss_price']}, TP: {variables_backtest['take_profit_price']}")
   
    

    def backtest_doble_top_bottom_stop(swings, swing_times, high_actual, low_actual, umbral, variacion_minima, R_multiplier, num_decimales, i):
        # Configuración del archivo de log
        log_file = "backtest_traces.log"
        
        # Función auxiliar para escribir en el log
        def write_log(message):
            with open(log_file, 'a') as f:
                f.write(f"{caldayi[i]}: {message}\n")
        
        tiempo_max_espera = timedelta(minutes=5)
        RESET_VALUES = {
            'tipo': None,
            'swing_detectado': None,
            'tiempo_deteccion': None,
            'entry_stop_price': 0.0,
            'stop_loss_price': 0.0,
            'take_profit_price': 0.0,
            'en_espera': False,
            'tiempo_orden': 0,
            'entry_stop_pendiente': False,
            'entry_stop_ejecutada': False
        }

        lsw = len(swings)

        if variables_backtest['entry_stop_pendiente'] is True:
            if variables_backtest['tipo'] == 'double_top':
                if loi[i] <= variables_backtest['entry_stop_price']:
                    write_log(f"ENTRADA EJECUTADA - Double Top. Precio: {variables_backtest['entry_stop_price']}")
                    variables_backtest['entry_stop_pendiente'] = False
                    variables_backtest['entry_stop_ejecutada'] = True
                    return
                else:
                    if variables_backtest['en_espera'] is True:
                        if variables_backtest['tiempo_orden'] > 0:
                            variables_backtest['tiempo_orden'] -= 1
                            return
                        write_log("RESET - Tiempo de espera agotado (Double Top)")
                        variables_backtest.update(RESET_VALUES)
                    elif variables_backtest['en_espera'] is False:    
                        if swings[-1] > swings[-2]:  # posible double top
                            for k in range(1, (lsw - 1) // 2 + 1):
                                dif = swings[-1] - swings[(-2 * k)-1]
                                if abs(dif) < umbral:
                                    write_log("NO SE EJECUTO LA ORDEN, CANCELANDO")
                                    variables_backtest.update(RESET_VALUES)
                                    break
                                elif dif <= -umbral:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5  
                                    return
                                else:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5  
                                    return
                        else:
                            write_log("EN ESPERA 5 MIN MÁS")
                            variables_backtest['en_espera'] = True
                            variables_backtest['tiempo_orden'] = 5  
                            return


            elif variables_backtest['tipo'] == 'double_bottom':
                if hii[i] >= variables_backtest['entry_stop_price']:
                    write_log(f"ENTRADA EJECUTADA - Double Bottom. Precio: {variables_backtest['entry_stop_price']}")
                    variables_backtest['entry_stop_pendiente'] = False
                    variables_backtest['entry_stop_ejecutada'] = True
                    return
                else:
                    if variables_backtest['en_espera'] is True:
                        if variables_backtest['tiempo_orden'] > 0:
                            variables_backtest['tiempo_orden'] -= 1
                            return
                        write_log("RESET - Tiempo de espera agotado (Double Bottom)")
                        variables_backtest.update(RESET_VALUES)
                    elif variables_backtest['en_espera'] is False:    
                        if swings[-1] < swings[-2]:  # posible double bottom
                            for k in range(1, (lsw - 1) // 2 + 1):
                                dif = swings[-1] - swings[(-2 * k)-1]
                                if abs(dif) < umbral:
                                    write_log("NO SE EJECUTO LA ORDEN, CANCELANDO")
                                    variables_backtest.update(RESET_VALUES)
                                    break
                                elif dif >= umbral:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5   
                                    return
                                else:
                                    write_log("EN ESPERA 5 MIN MÁS")
                                    variables_backtest['en_espera'] = True
                                    variables_backtest['tiempo_orden'] = 5   
                                    return
                        else:
                            write_log("EN ESPERA 5 MIN MÁS")
                            variables_backtest['en_espera'] = True
                            variables_backtest['tiempo_orden'] = 5   
                            return         

        if variables_backtest['entry_stop_ejecutada'] is True:
            if variables_backtest['tipo'] == 'double_top':
                if hii[i] >= variables_backtest['stop_loss_price']:
                    write_log(f"SALIDA POR STOP LOSS - Double Top. Precio: {variables_backtest['stop_loss_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_stop_price'] - variables_backtest['stop_loss_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_stop_price'] - variables_backtest['stop_loss_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES)

                elif loi[i] <= variables_backtest['take_profit_price']:
                    write_log(f"SALIDA POR TAKE PROFIT - Double Top. Precio: {variables_backtest['take_profit_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_stop_price'] - variables_backtest['take_profit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['entry_stop_price'] - variables_backtest['take_profit_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES)

                else:
                    return        

            elif variables_backtest['tipo'] == 'double_bottom':
                if loi[i] <= variables_backtest['stop_loss_price']:
                    write_log(f"SALIDA POR STOP LOSS - Double Bottom. Precio: {variables_backtest['stop_loss_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['stop_loss_price'] - variables_backtest['entry_stop_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['stop_loss_price'] - variables_backtest['entry_stop_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES) 

                elif hii[i] >= variables_backtest['take_profit_price']:
                    write_log(f"SALIDA POR TAKE PROFIT - Double Bottom. Precio: {variables_backtest['take_profit_price']}")
                    if len(variables_backtest['curva']) == 0:
                        variables_backtest['curva'].append(0.0)
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['take_profit_price'] - variables_backtest['entry_stop_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES)    
                    else:
                        variables_backtest['curva'].append((variables_backtest['curva'][-1]) + (variables_backtest['take_profit_price'] - variables_backtest['entry_stop_price']))
                        variables_backtest['tiempo_trades'].append(caldayi[i])
                        variables_backtest.update(RESET_VALUES)

                else:
                    return        

        if swings[-1] < swings[-2]:  # posible double bottom
            for k in range(1, (lsw - 1) // 2 + 1):
                dif = swings[-1] - swings[(-2 * k)-1]
                if abs(dif) < umbral:
                    write_log(f"PATRÓN DETECTADO - Double Bottom. Swing: {swings[-1]}, Tiempo: {swing_times[-1]}")
                    variables_backtest['tipo'] = 'double_bottom'
                    variables_backtest['swing_detectado'] = swings[-1]
                    variables_backtest['tiempo_deteccion'] = swing_times[-1]
                    break
                elif dif >= umbral:
                    break

        elif swings[-1] > swings[-2]:  # posible double top
            for k in range(1, (lsw - 1) // 2 + 1):
                dif = swings[-1] - swings[(-2 * k)-1]
                if abs(dif) < umbral:
                    write_log(f"PATRÓN DETECTADO - Double Top. Swing: {swings[-1]}, Tiempo: {swing_times[-1]}")
                    variables_backtest['tipo'] = 'double_top'
                    variables_backtest['swing_detectado'] = swings[-1]
                    variables_backtest['tiempo_deteccion'] = swing_times[-1]
                    break
                elif dif <= -umbral:
                    break

        # --- NUEVAS VALIDACIONES ---
        if variables_backtest['tipo'] and variables_backtest['swing_detectado'] and variables_backtest['tiempo_deteccion']:
            # 1. Verificar que no hayan pasado más de 5 minutos desde la detección
            tiempo_actual = caldayi[i]
            tiempo_transcurrido = tiempo_actual - variables_backtest['tiempo_deteccion']

            if tiempo_transcurrido > tiempo_max_espera:
                write_log("RESET - Tiempo máximo de espera excedido")
                variables_backtest.update(RESET_VALUES)
                return
            
            # 2. Verificar que el precio actual está dentro del rango permitido
            precio_actual = high_actual if variables_backtest['tipo'] == 'double_bottom' else low_actual
            distancia_al_swing = abs(precio_actual - variables_backtest['swing_detectado'])

            if distancia_al_swing > umbral:
                write_log(f"RESET - Distancia al swing excedida. Distancia: {distancia_al_swing}, Umbral: {umbral}")
                variables_backtest.update(RESET_VALUES)
                return
            
            if variables_backtest['tipo'] == 'double_top':
                variables_backtest['entry_stop_price'] = round(low_actual - variacion_minima, num_decimales)
                variables_backtest['stop_loss_price'] = round(swings[-1] + variacion_minima, num_decimales)
                variables_backtest['take_profit_price'] = round(variables_backtest['entry_stop_price'] - (R_multiplier * (variables_backtest['stop_loss_price'] - variables_backtest['entry_stop_price'])), num_decimales)
                variables_backtest['entry_stop_pendiente'] = True
                write_log(f"ORDEN CONFIGURADA - Double Top. Entry: {variables_backtest['entry_stop_price']}, SL: {variables_backtest['stop_loss_price']}, TP: {variables_backtest['take_profit_price']}")

            elif variables_backtest['tipo'] == 'double_bottom':
                variables_backtest['entry_stop_price'] = round(high_actual + variacion_minima, num_decimales)
                variables_backtest['stop_loss_price'] = round(swings[-1] - variacion_minima, num_decimales)
                variables_backtest['take_profit_price'] = round(variables_backtest['entry_stop_price'] + (R_multiplier * (variables_backtest['entry_stop_price'] - variables_backtest['stop_loss_price'])), num_decimales)
                variables_backtest['entry_stop_pendiente'] = True
                write_log(f"ORDEN CONFIGURADA - Double Bottom. Entry: {variables_backtest['entry_stop_price']}, SL: {variables_backtest['stop_loss_price']}, TP: {variables_backtest['take_profit_price']}")
   
       
    
    caldayi, tradayi, hii, loi, cli, opi, voli = leer_min(file_path)
   
    total_registros = len(caldayi)


    caldayi = np.array(caldayi)
    hii = np.array(hii)
    loi = np.array(loi)
    cli = np.array(cli)
    opi = np.array(opi)
    voli = np.array(voli)



    for i in range(57600, total_registros):
        if i % 1000 == 0:  # Mostrar progreso cada 1000 registros
             print(f"Procesando {i}/{total_registros} ({(i-57600)/(total_registros-57600)*100:.1f}%)")
        try:

            hi_agrupacion, lo_agrupacion,_, _, _, _ = dividir_min_en_grupos_para_swings(caldayi, hii, loi, cli, opi, voli, swing_corto, 1, i)

            hi, lo, cl, op, dhi, dlo = dividir_min_en_grupos_para_swings(caldayi, hii, loi, cli, opi, voli, swing_largo, n_grupos, i)
            
            swings, tiempos, _ = swing1(hi, lo, cl, op, dhi, dlo)
            backtest_doble_top_bottom_stop(swings, tiempos, hi_agrupacion[0], lo_agrupacion[0], umbral, variacion_minima, R, numero_decimales, i)



        
        except IndexError:
            print(f"Error: No hay suficientes datos para formar {n_grupos} grupos de {swing_largo} minutos desde el registro {i}")
            continue
        except ValueError as e:
            print(f"Error: {e}")
            continue
        
            
    df = pd.DataFrame(variables_backtest['curva'])
    df_times = pd.DataFrame(variables_backtest['tiempo_trades'])
    df_combinado = pd.concat([df_times, df], axis=1)
    df_combinado.to_csv(
        'curva_y_tiempos_combinados.csv',
        sep=';',
        decimal=',',
        float_format='%.5f',
        index=False,
        date_format='%Y-%m-%d %H:%M:%S'  # Formato de timestamps
    )
    #df.to_csv('curva_backtest.csv', sep=';', decimal=',', float_format='%.5f', index=False)
curva("010020SF.min", 2 ,0.00005, 1.5, 60, 3, 100, 5)
