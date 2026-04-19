from sqlalchemy.orm import Session
from db_models import Package, PackageLog

def procesar_escaneo(db: Session, guia: str, operario_id: str, modo: str, mensajero_id=None, causal=None):
    """
    Modos permitidos: 'INGRESO', 'DESPACHO', 'RETORNO'
    """
    # 1. Buscar el paquete en el precargue (Excel)
    package = db.query(Package).filter(Package.tracking_number == guia).first()

    if not package:
        return {
            "status": "ERROR", 
            "message": f"Guía {guia} NO encontrada en el sistema.", 
            "sound": "ALERTA_CRITICA"
        }

    # 2. LÓGICA DE INGRESO A BODEGA
    if modo == "INGRESO":
        package.status = "EN_BODEGA"
        nuevo_log = PackageLog(
            package_id=package.id, 
            action="INGRESO_BODEGA", 
            operator_id=operario_id,
            observation="Ingreso físico a bodega central"
        )
        db.add(nuevo_log)
        db.commit()
        return {"status": "OK", "message": "Ingreso Exitoso", "sound": "BEEP_CORTO"}

    # 3. LÓGICA DE DESPACHO A MENSAJERO (SEGURIDAD DE INVENTARIO)
    elif modo == "DESPACHO":
        # REGLA DE ORO: Si no se pistoleó al entrar, no sale.
        if package.status != "EN_BODEGA":
            return {
                "status": "ERROR", 
                "message": "¡BLOQUEO! Este paquete no registra ingreso a bodega.", 
                "sound": "ALERTA_CRITICA"
            }
        
        package.status = "EN_REPARTO"
        package.courier_id = mensajero_id
        nuevo_log = PackageLog(
            package_id=package.id, 
            action="SALIDA_A_RUTA", 
            courier_id=mensajero_id, 
            operator_id=operario_id
        )
        db.add(nuevo_log)
        db.commit()
        return {"status": "OK", "message": "Asignado a mensajero", "sound": "BEEP_CORTO"}

    # 4. LÓGICA DE RETORNO (DEVOLUCIONES / REINTENTOS)
    elif modo == "RETORNO":
        package.status = "EN_BODEGA"
        package.delivery_attempts += 1 # Sumamos el intento (Max 3)
        nuevo_log = PackageLog(
            package_id=package.id, 
            action=f"INTENTO_{package.delivery_attempts}_FALLIDO", 
            observation=causal, 
            operator_id=operario_id
        )
        db.add(nuevo_log)
        db.commit()
        return {"status": "OK", "message": f"Retorno grabado (Intento {package.delivery_attempts})", "sound": "BEEP_CORTO"}
