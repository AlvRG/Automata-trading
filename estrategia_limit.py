from variables_por_contrato import *

def procesar_doble_top_bottom(swingsy, calswy, umbral, ib, contract, orden_activa, high_barra_actual, low_barra_actual, client_id, cantidad, variacion_minima, R_multiplier, num_decimales, zona_horaria):
    
    
    from ib_insync import StopOrder, LimitOrder
    from datetime import datetime, timedelta
    from datetime import timezone
    from dateutil import tz

    tiempo_max_espera = timedelta(minutes=5)  # Máximo 5 minutos entre detección y entrada


    lsw = len(swingsy)

    if orden_activa.get('entry_order') is not None:
        # Si ya hay una orden enviada, verificamos si fue ejecutada o hay que cancelarla
        if orden_activa.get('entry_order').isActive() == False:
            entry_order = orden_activa.get('entry_order')
            tp_trade = orden_activa.get('tp_order')
            sl_trade = orden_activa.get('sl_order')

            if tp_trade and tp_trade.orderStatus.status == 'Filled':
                print("Take Profit ejecutado.")
                orden_activa.update({'enviada': False, 'entry_order': None, 'tipo': None, 'tp_order': None, 'sl_order': None, 'take_profit_price': None, 'stop_loss_price': None, 'en_espera': False})
               

            elif sl_trade and sl_trade.orderStatus.status == 'Filled':
                print("Stop Loss ejecutado.")
                orden_activa.update({'enviada': False, 'entry_order': None, 'tipo': None, 'tp_order': None, 'sl_order': None, 'take_profit_price': None, 'stop_loss_price': None, 'en_espera': False})

               
            elif entry_order.orderStatus.status == 'Filled':
                print("Entrada ejecutada. Esperando a que se ejecuten TP o SL...")
                return
            

            elif entry_order.orderStatus.status in ('Cancelled', 'Inactive'):
                print("Orden cancelada o inactiva. Se puede buscar nueva entrada.")
                orden_activa.update({'enviada': False, 'entry_order': None, 'tipo': None, 'tp_order': None, 'sl_order': None, 'take_profit_price': None, 'stop_loss_price': None, 'en_espera': False})
           
        else:
            entry_order = orden_activa.get('entry_order')
            try:
                if orden_activa.get('en_espera') == True:
                    print("Orden en espera, no se cancela.")
                    return

                if orden_activa.get('tipo') == 'double_top':
                    if swingsy[-1] > swingsy[-2]:  # posible double top
                        for k in range(1, (lsw - 1) // 2 + 1):
                            dif = swingsy[-1] - swingsy[(-2 * k)-1]
                            if abs(dif) < umbral:
                                print("Cancelando orden anterior que no se ejecutó...")
                                ib.cancelOrder(entry_order.order)
                                orden_activa.update({
                                    'enviada': False, 
                                    'entry_order': None, 
                                    'tipo': None, 
                                    'tp_order': None, 
                                    'sl_order': None,
                                    'take_profit_price': None,
                                    'stop_loss_price': None,
                                    'en_espera': False
                                })
                                break
                            elif dif <= -umbral:
                                orden_activa['en_espera'] = True 
                                return
                            else:
                                orden_activa['en_espera'] = True 
                                return      
                    else:
                        orden_activa['en_espera'] = True 
                        return       


                else:  # posible double bottom
                    if swingsy[-1] < swingsy[-2]:  # posible double bottom
                        for k in range(1, (lsw - 1) // 2 + 1):
                            dif = swingsy[-1] - swingsy[(-2 * k)-1]
                            if abs(dif) < umbral:
                                print("Cancelando orden anterior que no se ejecutó...")
                                ib.cancelOrder(entry_order.order)
                                orden_activa.update({
                                    'enviada': False, 
                                    'entry_order': None, 
                                    'tipo': None, 
                                    'tp_order': None, 
                                    'sl_order': None,
                                    'take_profit_price': None,
                                    'stop_loss_price': None,
                                    'en_espera': False
                                })
                                break
                            elif dif >= umbral:
                                orden_activa['en_espera'] = True  
                                return
                            else:
                                orden_activa['en_espera'] = True  
                                return
                    else:
                        orden_activa['en_espera'] = True  
                        return                   

            except Exception as e:
                print(f"Error durante el proceso de cancelación: {str(e)}")
                # No es crítico si falla la cancelación


    # Si no hay orden activa, buscamos nuevos patrones
    if lsw >= 3:
        tipo = None
        swing_detectado = None
        tiempo_deteccion = None

        if swingsy[-1] < swingsy[-2]:  # posible double bottom
            for k in range(1, (lsw - 1) // 2 + 1):
                dif = swingsy[-1] - swingsy[(-2 * k)-1]
                if abs(dif) < umbral:
                    tipo = 'double_bottom'
                    swing_detectado = swingsy[-1]  # Precio del swing
                    tiempo_deteccion = calswy[-1]  # Hora de detección (datetime)
                    break
                elif dif >= umbral:
                    break

        elif swingsy[-1] > swingsy[-2]:  # posible double top
            for k in range(1, (lsw - 1) // 2 + 1):
                dif = swingsy[-1] - swingsy[(-2 * k)-1]
                if abs(dif) < umbral:
                    tipo = 'double_top'
                    swing_detectado = swingsy[-1]
                    tiempo_deteccion = calswy[-1]
                    break
                elif dif <= -umbral:
                    break

         # --- NUEVAS VALIDACIONES ---
        if tipo and swing_detectado and tiempo_deteccion:
            # 1. Verificar que no hayan pasado más de 5 minutos desde la detección
            tiempo_actual_utc = datetime.now(timezone.utc)
            tiempo_actual_local = tiempo_actual_utc.astimezone(tz.gettz(zona_horaria))  # Ajustar a la zona horaria deseada
            tiempo_transcurrido = tiempo_actual_local - tiempo_deteccion

            if tiempo_transcurrido > tiempo_max_espera:
                print(f"⚠️ {tipo} detectado hace {tiempo_transcurrido}. Demasiado tarde para entrar.")
                return

            # 2. Verificar que el precio actual está dentro del rango permitido
            precio_actual = high_barra_actual if tipo == 'double_bottom' else low_barra_actual
            distancia_al_swing = abs(precio_actual - swing_detectado)

            if distancia_al_swing > umbral:
                print(f"⚠️ {tipo} detectado en {swing_detectado}, pero precio actual ({precio_actual}) está fuera de rango.")
                return

            # --- LÓGICA DE ENTRADA (código existente, ahora con validaciones) ---
            print(f"✅ {tipo.replace('_', ' ')} válido. Swing: {swing_detectado} a las {tiempo_deteccion} y {swingsy[(-2 * k)-1]} a las {calswy[(-2 * k)-1]}, Precio actual: {precio_actual}")
            order_timer = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M:%S")


            if tipo == 'double_top':
                action = 'BUY' 
                quantity = cantidad
                entry_limit_price = round(low_barra_actual - variacion_minima, num_decimales)  # ej: calculado a partir del swing
                take_profit_price = round(swingsy[-1] + variacion_minima, num_decimales)
                stop_loss_price = round(entry_limit_price - (R_multiplier * (take_profit_price - entry_limit_price)), num_decimales)
                # Orden de entrada
                orden_entrada = LimitOrder(
                    action=action,
                    totalQuantity=quantity,
                    lmtPrice=entry_limit_price,
                    tif='GTD',
                    goodTillDate=order_timer,
                    outsideRth=True,
                    transmit=False,
                    orderId=ib.client.getReqId()
                )

            elif tipo == 'double_bottom':
                action = 'SELL' 
                quantity = cantidad
                entry_limit_price = round(high_barra_actual + variacion_minima, num_decimales)
                take_profit_price = round(swingsy[-1] - variacion_minima, num_decimales)
                stop_loss_price = round(entry_limit_price + (R_multiplier * (entry_limit_price - take_profit_price)), num_decimales)
                # Orden de entrada
                orden_entrada = LimitOrder(
                    action=action,
                    totalQuantity=quantity,
                    lmtPrice=entry_limit_price,
                    tif='GTD',
                    goodTillDate=order_timer,
                    outsideRth=True,
                    transmit=False,
                    orderId=ib.client.getReqId()
                )

            tp = LimitOrder(
                action='SELL' if action == 'BUY' else 'BUY',
                totalQuantity=quantity,
                lmtPrice=take_profit_price,  # Precio take-profit
                tif='GTC',
                outsideRth=True,
                parentId=orden_entrada.orderId,
                transmit=False,
                orderId=ib.client.getReqId()
            )

            sl = StopOrder(
                action='SELL' if action == 'BUY' else 'BUY',
                totalQuantity=quantity,
                stopPrice=stop_loss_price,  # Precio stop-loss
                tif='GTC',
                outsideRth=True,
                parentId=orden_entrada.orderId,
                transmit=True,   # Última orden del bracket debe ser True
                orderId=ib.client.getReqId()
            )

            orden_activa.update({
                'enviada': True, 
                'entry_order': ib.placeOrder(contract, orden_entrada), 
                'tipo': tipo, 
                'tp_order': ib.placeOrder(contract, tp), 
                'sl_order': ib.placeOrder(contract, sl),
                'take_profit_price': take_profit_price,
                'stop_loss_price': stop_loss_price,
                'en_espera': False
            })
