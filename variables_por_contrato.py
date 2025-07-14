import numpy as np
from collections import defaultdict
from ib_insync import Trade

variables_por_contrato = defaultdict(lambda: {
    'orden_activa': {
        'enviada': False,
        'entry_order': None, 
        'tipo': None,
        'tp_order': None,  
        'sl_order': None,  
        'take_profit_price': None,
        'stop_loss_price': None,
        'en_espera': False,
    },
    'quantity': 0,
    'umbral': 0.0,
    'variacion_minima': 0.0,
    'R': 0.0,
    'num_decimales': 0,
    'zona_horaria': None,
    'ruta_archivo': None,
})

def obtener_variables(identificador):
    return variables_por_contrato[identificador]

