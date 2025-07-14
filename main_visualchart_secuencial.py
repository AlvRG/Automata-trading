import time
from ib_insync import *
import variables_por_contrato
from procesado import *
from estrategia_limit import procesar_doble_top_bottom

CONTRATOS = [
    {'symbol': 'ES', 'expiry': '202506', 'exchange': 'CME', 'client_id': 1},
    {'symbol': 'NQ', 'expiry': '202506', 'exchange': 'CME', 'client_id': 2},
    {'symbol': 'CL', 'expiry': '202507', 'exchange': 'NYMEX', 'client_id': 3},
    {'symbol': 'GC', 'expiry': '202506', 'exchange': 'COMEX', 'client_id': 4},
    {'symbol': 'IBEX35', 'expiry': '202506', 'exchange': 'MEFFRV', 'client_id': 5},
    {'symbol': 'HG', 'expiry': '202506', 'exchange': 'COMEX', 'client_id': 6},
    {'symbol': 'NG', 'expiry': '202506', 'exchange': 'NYMEX', 'client_id': 7},
    {'symbol': 'HO', 'expiry': '202506', 'exchange': 'NYMEX', 'client_id': 8},
    {'symbol': 'YM', 'expiry': '202506', 'exchange': 'CBOT', 'client_id': 9},
    {'symbol': 'RTY', 'expiry': '202506', 'exchange': 'CME', 'client_id': 10},
    {'symbol': 'JPY', 'expiry': '202506', 'exchange': 'CME', 'client_id': 11},
    {'symbol': 'EUR', 'expiry': '202506', 'exchange': 'CME', 'client_id': 12},
    {'symbol': 'GBP', 'expiry': '202506', 'exchange': 'CME', 'client_id': 13},
    {'symbol': 'AUD', 'expiry': '202506', 'exchange': 'CME', 'client_id': 14},
    {'symbol': 'CHF', 'expiry': '202506', 'exchange': 'CME', 'client_id': 15},
    {'symbol': 'PA', 'expiry': '202506', 'exchange': 'NYMEX', 'client_id': 16},
    {'symbol': 'PL', 'expiry': '202507', 'exchange': 'NYMEX', 'client_id': 17},
    {'symbol': 'ZS', 'expiry': '202506', 'exchange': 'CBOT', 'client_id': 18},
    {'symbol': 'ZM', 'expiry': '202506', 'exchange': 'CBOT', 'client_id': 19},
    {'symbol': 'ZC', 'expiry': '202506', 'exchange': 'CBOT', 'client_id': 20},
    {'symbol': 'ZW', 'expiry': '202506', 'exchange': 'CBOT', 'client_id': 21},
]

def configurar_contrato(symbol):
    # Diccionario completo con configuración por contrato
    config = {
        'ES': {'umbral': 2.5, 'margen': 20000, 'contratos_orden': 2, 'variacion_minima': 0.25, 'R': 3, 'num_decimales': 2, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'ES.min'},
        'NQ': {'umbral': 10.0, 'margen': 40000, 'contratos_orden': 1, 'variacion_minima': 0.25, 'R': 3, 'num_decimales': 2, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'NQ.min'},
        'YM': {'umbral': 20.0, 'margen': 13000, 'contratos_orden': 3, 'variacion_minima': 1.0, 'R': 3, 'num_decimales': None, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'YM.min'},
        'RTY': {'umbral': 1.0, 'margen': 10000, 'contratos_orden': 4, 'variacion_minima': 0.1, 'R': 3, 'num_decimales': 1, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'RTY.min'},
        'JPY': {'umbral': 1.0, 'margen': 4000, 'contratos_orden': 10, 'variacion_minima': 0.000001, 'R': 3, 'num_decimales': 6, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'JPY.min'},
        'EUR': {'umbral': 0.0002, 'margen': 5000, 'contratos_orden': 8, 'variacion_minima': 0.00005, 'R': 3, 'num_decimales': 5, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'EUR.min'},
        'GBP': {'umbral': 0.0002, 'margen': 2500, 'contratos_orden': 16, 'variacion_minima': 0.0001, 'R': 3, 'num_decimales': 4, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'GBP.min'}, 
        'AUD': {'umbral': 0.0002, 'margen': 2500, 'contratos_orden': 16, 'variacion_minima': 0.00005, 'R': 3, 'num_decimales': 5, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'AUD.min'},
        'CHF': {'umbral': 0.0002, 'margen': 5000, 'contratos_orden': 8, 'variacion_minima': 0.00005, 'R': 3, 'num_decimales': 5, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'CHF.min'},
        'CL': {'umbral': 0.03, 'margen': 20000, 'contratos_orden': 2, 'variacion_minima': 0.01, 'R': 3, 'num_decimales': 2, 'zona_horaria': 'America/New_York', 'ruta_archivo': 'CL.min'},
        'NG': {'umbral': 0.002, 'margen': 11000, 'contratos_orden': 3, 'variacion_minima': 0.001, 'R': 3, 'num_decimales': 3, 'zona_horaria': 'America/New_York', 'ruta_archivo': 'NG.min'},
        'HO': {'umbral': 0.0002, 'margen': 26000, 'contratos_orden': 1, 'variacion_minima': 0.0001, 'R': 3, 'num_decimales': 4, 'zona_horaria': 'America/New_York', 'ruta_archivo': 'HO.min'},
        'GC': {'umbral': 15.0, 'margen': 20000, 'contratos_orden': 2, 'variacion_minima': 0.1, 'R': 3, 'num_decimales': 1, 'zona_horaria': 'America/New_York', 'ruta_archivo': 'GC.min'},
        'PA': {'umbral': 5.0, 'margen': 20000, 'contratos_orden': 2, 'variacion_minima': 0.5, 'R': 3, 'num_decimales': 1, 'zona_horaria': 'America/New_York', 'ruta_archivo': 'PA.min'},
        'PL': {'umbral': 5.0, 'margen': 6000, 'contratos_orden': 6, 'variacion_minima': 0.1, 'R': 3, 'num_decimales': 1, 'zona_horaria': 'America/New_York', 'ruta_archivo': 'PL.min'},
        'HG': {'umbral': 0.02, 'margen': 13000, 'contratos_orden': 3, 'variacion_minima': 0.0005, 'R': 3, 'num_decimales': 4, 'zona_horaria': 'America/New_York', 'ruta_archivo': 'HG.min'},
        'ZS': {'umbral': 5.0, 'margen': 3500, 'contratos_orden': 10, 'variacion_minima': 0.25, 'R': 3, 'num_decimales': 2, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'ZS.min'},
        'ZM': {'umbral': 1.0, 'margen': 3200, 'contratos_orden': 11, 'variacion_minima': 0.1, 'R': 3, 'num_decimales': 1, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'ZM.min'},
        'ZC': {'umbral': 2.0, 'margen': 2200, 'contratos_orden': 18, 'variacion_minima': 0.25, 'R': 3, 'num_decimales': 2, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'ZC.min'},
        'ZW': {'umbral': 2.0, 'margen': 3300, 'contratos_orden': 11, 'variacion_minima': 0.25, 'R': 3, 'num_decimales': 2, 'zona_horaria': 'America/Chicago', 'ruta_archivo': 'ZW.min'},
        'IBEX35': {'umbral': 30.0, 'margen': 13000, 'contratos_orden': 3, 'variacion_minima': 1.0, 'R': 3, 'num_decimales': None, 'zona_horaria': 'Europe/Madrid', 'ruta_archivo': 'IBEX35.min'},
    }
    
    # Obtenemos la configuración o valores por defecto si el símbolo no existe
    contrato = config.get(symbol, {
        'umbral': 1.0, 
        'margen': 10000, 
        'contratos_orden': 1, 
        'variacion_minima': 0.01,  # Valor por defecto para variación mínima
        'R': 3,
        'num_decimales': 2,  # Valor por defecto para número de decimales
        'zona_horaria': 'America/New_York',  # Valor por defecto para zona horaria
        'ruta_archivo': f'{symbol}.min'  # Ruta por defecto para el archivo
    })
    
    # Devolvemos todos los parámetros necesarios
    return (
        contrato['umbral'],
        contrato['contratos_orden'],
        contrato['variacion_minima'],
        contrato['R'],
        contrato['num_decimales'],
        contrato['zona_horaria'],
        contrato['ruta_archivo']
    )

def recuperar_trade_por_id(ib, order_id: int) -> Trade:
    
    for trade in ib.trades():
        if trade.order.permId == order_id:
            return trade
    
    return None


def main():
    max_reintentos = 20  # Máximo de intentos de reconexión
    reintentos = 0
    primera_conexion = True
    ib = None
    
    while reintentos < max_reintentos:  # Bucle externo para controlar reintentos
        try:
            if ib is None or not ib.isConnected():
                ib = IB()
                ib.connect('127.0.0.1', 7497, clientId=1)
                print("✅ Conexión IB establecida")
                reintentos = 0

            if primera_conexion:
                # Prepara todos los contratos
                contratos_ib = [Future(c['symbol'], c['expiry'], c['exchange']) for c in CONTRATOS]
                vars_contratos = {c['symbol']: variables_por_contrato.obtener_variables(c['symbol']) for c in CONTRATOS}

                for config, contract in zip(CONTRATOS, contratos_ib):
                    symbol = config['symbol']
                    umbral, cantidad, variacion_minima, r, num_decimales, zona_horaria, ruta_archivo = configurar_contrato(config['symbol'])
                    vars_contratos[symbol].update({'umbral': umbral, 'quantity': cantidad, 'variacion_minima': variacion_minima, 'R': r, 'num_decimales': num_decimales, 'zona_horaria': zona_horaria, 'ruta_archivo': ruta_archivo})
                    file_path = vars_contratos[symbol]['ruta_archivo']

                primera_conexion = False

            else:
                for config, contract in zip(CONTRATOS, contratos_ib):
                    symbol = config['symbol']
                    vars_contrato = vars_contratos[symbol]

                    # RECONSTRUCCIÓN POST-RECONEXIÓN
                   
                    print("Entrando en reconstrucción post-reconexión")  # Debug
                    if vars_contrato['orden_activa']['entry_order'] and hasattr(vars_contrato['orden_activa']['entry_order'].order, 'permId'):
                        vars_contrato['orden_activa']['entry_order'] = recuperar_trade_por_id(ib, vars_contrato['orden_activa']['entry_order'].order.permId)
                        
                    
                    if vars_contrato['orden_activa']['tp_order'] and hasattr(vars_contrato['orden_activa']['tp_order'].order, 'permId'):
                        vars_contrato['orden_activa']['tp_order'] = recuperar_trade_por_id(ib, vars_contrato['orden_activa']['tp_order'].order.permId)
                       
                    
                    if vars_contrato['orden_activa']['sl_order'] and hasattr(vars_contrato['orden_activa']['sl_order'].order, 'permId'):
                        vars_contrato['orden_activa']['sl_order'] = recuperar_trade_por_id(ib, vars_contrato['orden_activa']['sl_order'].order.permId)
                         
                     

            while True:
                for config, contract in zip(CONTRATOS, contratos_ib):
                     # Verificar conexión antes de cada operación
                    if not ib.isConnected():
                        raise ConnectionError("Conexión perdida con IB")
                    
                    try:
                        # Procesamiento por contrato
                        symbol = config['symbol']
                        file_path = vars_contratos[symbol]['ruta_archivo']

                        caldayi, _, hii, loi, cli, opi, voli = leer_min(file_path, vars_contratos[symbol]['zona_horaria'])
                        caldayi = np.array(caldayi)
                        hii = np.array(hii)
                        loi = np.array(loi)
                        cli = np.array(cli)
                        opi = np.array(opi)
                        voli = np.array(voli)
                        hi_agrupacion, lo_agrupacion, _, _, _, _ = dividir_min_en_grupos_para_swings(caldayi, hii, loi, cli, opi, voli, 3, 1, len(caldayi)-1)
                       

                        # 2. Calcular en swings
                        hi, lo, cl, op, dhi, dlo = dividir_min_en_grupos_para_swings(caldayi, hii, loi, cli, opi, voli, 2, 80, len(caldayi)-1)
                        swings, tiempos, _ = swing1(hi, lo, cl, op, dhi, dlo)
                        

                        # 3. Ejecutar estrategia
                        procesar_doble_top_bottom(
                            swings, tiempos, vars_contratos[symbol]['umbral'], ib, contract,
                            vars_contratos[symbol]["orden_activa"], hi_agrupacion[0], lo_agrupacion[0],
                            config['client_id'], vars_contratos[symbol]['quantity'], vars_contratos[symbol]['variacion_minima'], vars_contratos[symbol]['R'], vars_contratos[symbol]['num_decimales'], vars_contratos[symbol]['zona_horaria'],
                        )
                        

                    except ConnectionError as e:
                        print(f"⚠️ {config['symbol']}: Error de conexión - {str(e)}")
                        if ib.isConnected():
                            ib.disconnect()
                        time.sleep(10)
                        break  # Sale del bucle interno para reintentar conexión

                    except Exception as e:
                        print(f"⚠️ Error en {symbol}: {str(e)}")

                # Pausa principal del bucle (con ib.sleep())
                #ib.sleep(50)  # ✅ Mantiene la conexión activa

        except KeyboardInterrupt:
            print("\n🔴 Interrupción por usuario")
            break

        except Exception as e:
            reintentos += 1
            print(f"🔴 {config['symbol']}: Error crítico (intento {reintentos}/{max_reintentos}) - {str(e)}")
            time.sleep(10)

    # --- Limpieza Final ---
    if ib and ib.isConnected():
        ib.disconnect()
    print("🔌 Programa terminado")

if __name__ == '__main__':
    print("""
    ====================================
    🚀 BOT MULTICONTRATO (ÚNICA INSTANCIA IB)
    ====================================
    """)
    main()