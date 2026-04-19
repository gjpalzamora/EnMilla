def registrar_movimiento(db, barcode, operario, modo, mensajero_id=None, motivo=None):
    # Buscar el paquete
    pkg = db.query(Package).filter(Package.guide_number == barcode).first()
    
    if not pkg:
        return {"alert": "ERROR_CRITICO", "msg": "GUÍA NO EXISTE EN SISTEMA"}

    # REGLA 1: INGRESO A BODEGA
    if modo == "INGRESO":
        pkg.status = "EN_BODEGA"
        nuevo_log = PackageLog(package_id=pkg.id, action="INGRESO_BODEGA", operator_name=operario)
        db.add(nuevo_log)
        db.commit()
        return {"alert": "EXITO", "msg": "Ingreso registrado"}

    # REGLA 2: SALIDA A MENSAJERO (SEGURIDAD)
    elif modo == "DESPACHO":
        if pkg.status != "EN_BODEGA":
            return {"alert": "ERROR_CRITICO", "msg": "¡ALERTA! Paquete no registra ingreso previo"}
        
        pkg.status = "EN_RUTA"
        pkg.courier_id = mensajero_id
        nuevo_log = PackageLog(package_id=pkg.id, action="CARGUE_MENSAJERO", operator_name=operario)
        db.add(nuevo_log)
        db.commit()
        return {"alert": "EXITO", "msg": "Asignado correctamente"}

    # REGLA 3: RETORNO / FALLIDO (CONTADOR DE INTENTOS)
    elif modo == "RETORNO":
        pkg.status = "EN_BODEGA"
        pkg.attempts += 1
        nuevo_log = PackageLog(package_id=pkg.id, action=f"INTENTO_{pkg.attempts}", observation=motivo, operator_name=operario)
        db.add(nuevo_log)
        db.commit()
        return {"alert": "ADVERTENCIA", "msg": f"Retorno grabado. Intento #{pkg.attempts}"}
