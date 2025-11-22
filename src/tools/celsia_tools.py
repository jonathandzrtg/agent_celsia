"""
Tools para el Agente de Celsia
Versión académica - Simulación de funcionalidades básicas
"""

from langchain.tools import tool
from datetime import datetime, timedelta
import random
from pydantic import BaseModel, Field
from enum import Enum

# Base de datos simulada en memoria
reportes_db = {}

# ==================== TOOLS INFORMATIVAS (las que ya tenías) ====================

@tool
def get_telefono_celsia():
    """Funcion para obtener el telefono de celsia. 
    Usar SÓLO si el usuario pide explícitamente el número de teléfono."""
    return "Linea Colombia: 01 8000 112 115, Línea Panamá: 00 800 2262591 y (507) 832 7907"


@tool
def get_social_media_celsia():
    """Funcion para obtener las redes sociales de celsia. 
    Usar SÓLO si el usuario pide explícitamente las redes sociales."""
    return "X: @Celsia_Energia, Facebook: Celsia Energía, Instagram: celsia_enegia, TikTok: @celsia_energia"


@tool
def get_pqr_celsia():
    """Funcion para obtener el PQR de celsia. 
    Usar SÓLO si el usuario pide explícitamente el PQR."""
    return "Para PQR, por favor entra al siguiente enlace: [PQR Celsia](https://clientes.celsia.com/clientes/home-pqr)"


@tool
def get_direccion_celsia():
    """Funcion para obtener la direccion de celsia. 
    Usar SÓLO si el usuario pide explícitamente la dirección."""
    message = """Celsia Yumbo: CALLE 15 # 29B-30 AUTOPISTA, Autopista Cali - Yumbo, Yumbo, Valle del Cauca
Celsia Ibagué: Calle 39A No. 5-15 Restrepo, Ibagué, Tolima"""
    return message


@tool
def get_pago_de_factura_celsia():
    """Funcion para obtener el pago de factura de celsia. 
    Usar SÓLO si el usuario pide explícitamente el pago de factura."""
    return "Para pagar tu factura de Celsia, por favor visita el siguiente enlace: [Pago de Factura Celsia](https://clientes.celsia.com/clientes/login), deberás iniciar sesión o crear un usuario si eres cliente nuevo."


# ==================== TOOLS FUNCIONALES (nuevas) ====================

class GenerarFacturaSimuladaInput(BaseModel):
    numero_cuenta: str = Field(..., description="Número de cuenta de 8 dígitos (ej: '12345678')")
    mes: str = Field(..., description="Mes a consultar (ej: 'octubre', 'noviembre')")

@tool(args_schema=GenerarFacturaSimuladaInput)
def generar_factura_simulada(numero_cuenta: str, mes: str) -> str:
    """Genera una factura simulada con consumo y valor a pagar.
    
    Args:
        numero_cuenta: Número de cuenta de 8 dígitos (ej: "12345678")
        mes: Mes a consultar (ej: "octubre", "noviembre")
    """
    
    # Validación básica
    if len(numero_cuenta) != 8 or not numero_cuenta.isdigit():
        return "❌ Error: El número de cuenta debe tener 8 dígitos."
    
    # Generar consumo aleatorio pero consistente
    random.seed(int(numero_cuenta) + hash(mes.lower()))
    consumo = random.randint(120, 350)
    tarifa = 550  # pesos por kWh
    valor_consumo = consumo * tarifa
    otros_cargos = int(valor_consumo * 0.08)  # 8% adicional
    total = valor_consumo + otros_cargos
    
    fecha_vencimiento = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
    
    return f"""
📄 **FACTURA DE ENERGÍA - {mes.upper()}**

Cuenta: {numero_cuenta}
Período: {mes.capitalize()} 2025

⚡ Consumo: {consumo} kWh
💵 Valor consumo: ${valor_consumo:,} COP
📊 Otros cargos: ${otros_cargos:,} COP

💰 **TOTAL A PAGAR: ${total:,} COP**
📅 Vence: {fecha_vencimiento}

Paga en: https://clientes.celsia.com
"""


class VerificarEstadoServicioInput(BaseModel):
    ciudad: str = Field(..., description="Ciudad a consultar (Palmira, Tuluá, Ibagué, Buenaventura)")

@tool(args_schema=VerificarEstadoServicioInput)
def verificar_estado_servicio(ciudad: str) -> str:
    """Verifica si hay interrupciones del servicio en una ciudad.
    
    Args:
        ciudad: Ciudad a consultar (Palmira, Tuluá, Ibagué, Buenaventura)
    """
    
    # Interrupciones simuladas
    interrupciones = {
        "buenaventura": "Hay mantenimiento programado en la red eléctrica el 09/11 de 10:00 a 12:00",
        "tulua": "Hay mantenimiento programado en el 08/11 de 14:00 a 17:00",
        "tuluá": "Hay mantenimiento programado en el 08/11 de 14:00 a 17:00",
        "ibague": "Reparación en el Centro el 07/11 de 08:00 a 12:00",
        "ibagué": "Reparación en el Centro el 07/11 de 08:00 a 12:00",
    }
    
    ciudad_lower = ciudad.lower()
    
    if ciudad_lower in interrupciones:
        return f"""
⚠️ **INTERRUPCIÓN PROGRAMADA EN {ciudad.upper()}**

{interrupciones[ciudad_lower]}

Recomendaciones:
• Desconecta equipos sensibles
• Ten cargado tu celular

📞 Más info: 01 8000 112 115
"""
    else:
        return f"""
✅ **SERVICIO NORMAL EN {ciudad.upper()}**

No hay interrupciones programadas.
El servicio opera con normalidad.

Si tienes problemas, repórtalos al: 01 8000 112 115
"""


class CalcularInstalacionSolarInput(BaseModel):
    consumo_mensual_kwh: int = Field(..., description="Consumo mensual en kWh (ej: 200, 350)")
    ciudad: str = Field(..., description="Ciudad donde instalar")

@tool(args_schema=CalcularInstalacionSolarInput)
def calcular_instalacion_solar(consumo_mensual_kwh: int, ciudad: str) -> str:
    """Calcula el costo de instalación de paneles solares.
    
    Args:
        consumo_mensual_kwh: Consumo mensual en kWh (ej: 200, 350)
        ciudad: Ciudad donde instalar
    """
    
    if consumo_mensual_kwh <= 0 or consumo_mensual_kwh > 5000:
        return "❌ Error: El consumo debe estar entre 1 y 5000 kWh"
    
    # Cálculos simplificados
    potencia_sistema = consumo_mensual_kwh / 120  # kWp aprox
    num_paneles = int(potencia_sistema / 0.45) + 1
    costo_instalacion = int(potencia_sistema * 3500000)  # COP por kWp
    
    ahorro_mensual = int(consumo_mensual_kwh * 600 * 0.8)  # 80% ahorro
    ahorro_anual = ahorro_mensual * 12
    roi_anos = round(costo_instalacion / ahorro_anual, 1)
    
    return f"""
☀️ **INSTALACIÓN SOLAR EN {ciudad.upper()}**

📊 Sistema recomendado:
• Paneles de 450W: {num_paneles} unidades
• Potencia: {potencia_sistema:.1f} kWp

💰 Inversión: ${costo_instalacion:,} COP
💵 Ahorro mensual: ${ahorro_mensual:,} COP
💵 Ahorro anual: ${ahorro_anual:,} COP

📈 Recuperas tu inversión en: {roi_anos} años

Para cotización: 01 8000 112 115
Web: https://www.celsia.com/es/soluciones-en-eficiencia-energetica-para-empresas-y-constructoras/
"""


from enum import Enum # Add this import at the top

class TipoDano(str, Enum):
    APAGON = "apagon"
    POSTE_DANADO = "poste_dañado"
    CABLE_CAIDO = "cable_caido"
    FLUCTUACION = "fluctuacion"

class ReportarDanoServicioInput(BaseModel):
    tipo_dano: TipoDano = Field(..., description="Tipo (apagon, poste_dañado, cable_caido, fluctuacion)")
    direccion: str = Field(..., description="Dirección donde ocurre")
    telefono: str = Field(..., description="Teléfono de contacto")

@tool(args_schema=ReportarDanoServicioInput)
def reportar_dano_servicio(tipo_dano: TipoDano, direccion: str, telefono: str) -> str:
    """Reporta un daño en el servicio eléctrico y genera un ticket.
    
    Args:
        tipo_dano: Tipo (apagon, poste_dañado, cable_caido, fluctuacion)
        direccion: Dirección donde ocurre
        telefono: Teléfono de contacto
    """
    
    # Validar tipo
    tipos_validos = ["apagon", "poste_dañado", "poste_danado", "cable_caido", "fluctuacion"]
    if tipo_dano.lower() not in tipos_validos:
        return f"❌ Tipo inválido. Usa: apagon, poste_dañado, cable_caido, fluctuacion"
    
    # Generar ticket
    ticket_id = f"TKT-{len(reportes_db) + 1001}"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Guardar en memoria
    reportes_db[ticket_id] = {
        "tipo": tipo_dano,
        "direccion": direccion,
        "telefono": telefono,
        "fecha": fecha,
        "estado": "En proceso"
    }
    
    tiempos = {
        "apagon": "2-4 horas",
        "poste_dañado": "4-8 horas",
        "poste_danado": "4-8 horas",
        "cable_caido": "1-3 horas (URGENTE)",
        "fluctuacion": "8-24 horas"
    }
    
    return f"""
✅ **REPORTE CREADO**

🎫 Ticket: {ticket_id}
📋 Tipo: {tipo_dano}
📍 Dirección: {direccion}
📞 Contacto: {telefono}
📅 Fecha: {fecha}

⏱️ Tiempo estimado: {tiempos.get(tipo_dano.lower(), '4-8 horas')}

Guarda tu número de ticket para seguimiento.
Línea de ayuda: 01 8000 112 115
"""


class ConsultarEstadoReporteInput(BaseModel):
    ticket_id: str = Field(..., description="Número de ticket (ej: 'TKT-1001')")

@tool(args_schema=ConsultarEstadoReporteInput)
def consultar_estado_reporte(ticket_id: str) -> str:
    """Consulta el estado de un reporte creado previamente.
    
    Args:
        ticket_id: Número de ticket (ej: "TKT-1001")
    """
    
    if ticket_id not in reportes_db:
        return f"""
❌ **TICKET NO ENCONTRADO**

El ticket '{ticket_id}' no existe.
Verifica el número (formato: TKT-XXXX)

📞 Ayuda: 01 8000 112 115
"""
    
    reporte = reportes_db[ticket_id]
    
    return f"""
🎫 **ESTADO DEL TICKET: {ticket_id}**

📊 Estado: {reporte['estado']}
📋 Tipo: {reporte['tipo']}
📍 Dirección: {reporte['direccion']}
📅 Reportado: {reporte['fecha']}

💡 Un técnico se comunicará contigo pronto.

📞 Seguimiento: 01 8000 112 115
"""
