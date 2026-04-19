def procesar_escaneo(db, guia, operario_id, modo="INGRESO", mensajero_id=None, causal=None):
    """
    Modos: 'INGRESO' (a bodega), 'DESPACHO' (a mensajero), 'RETORNO' (de mensajero)
    """
    package = db.query(Package).filter(Package.tracking_number == guia).first()

    # 1. VALIDACIÓN: ¿Existe el paquete en el precargue?
    if not package:
        return {"status": "ERROR", "message": "Guía no registrada en sistema", "sound": "ALERTA_CRITICA"}

    # 2. LÓGICA DE INGRESO A BODEGA
    if modo == "INGRESO":
        package.status = "EN_BODEGA"
        nuevo_log = PackageLog(package_id=package.id, action="INGRESO_BODEGA", operator_id=operario_id)
        db.add(nuevo_log)
        db.commit()
        return {"status": "OK", "message": "Ingreso Exitoso", "sound": "BEEP_CORTO"}

    # 3. LÓGICA DE DESPACHO A MENSAJERO
    elif modo == "DESPACHO":
        # SEGURIDAD: Solo puede salir si entró a bodega primero
        if package.status != "EN_BODEGA":
            return {"status": "ERROR", "message": "¡ALERTA! El paquete no registra ingreso a bodega", "sound": "ALERTA_CRITICA"}
        
        package.status = "EN_REPARTO"
        package.courier_id = mensajero_id
        nuevo_log = PackageLog(package_id=package.id, action="SALIDA_A_RUTA", courier_id=mensajero_id, operator_id=operario_id)
        db.add(nuevo_log)
        db.commit()
        return {"status": "OK", "message": f"Asignado a mensajero", "sound": "BEEP_CORTO"}

    # 4. LÓGICA DE RETORNO (GESTIÓN DE FALLIDOS)
    elif modo == "RETORNO":
        package.status = "EN_BODEGA"
        package.attempts += 1
        nuevo_log = PackageLog(package_id=package.id, action="INTENTO_FALLIDO", observation=causal, operator_id=operario_id)
        db.add(nuevo_log)
        db.commit()
        return {"status": "OK", "message": f"Retorno registrado. Intento: {package.attempts}", "sound": "BEEP_CORTO"}
