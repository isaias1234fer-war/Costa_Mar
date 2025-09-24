def autenticar_usuario(tipo_usuario, usuario, password):
    """
    Sistema de autenticación mejorado
    """
    credenciales = {
        "Administrador": [
            {"usuario": "admin", "password": "admin123", "nombre": "Administrador Principal"}
        ],
        "Mozo": [
            {"usuario": "mozo01", "password": "mozo123", "nombre": "Carlos Rodríguez"},
            {"usuario": "mozo02", "password": "mozo123", "nombre": "María González"},
            {"usuario": "mozo03", "password": "mozo123", "nombre": "Pedro López"}
        ],
        "Cliente": {"usuario": "", "password": ""}
    }
    
    if tipo_usuario == "Cliente":
        return bool(usuario.strip()), usuario.title()
    
    if tipo_usuario in credenciales:
        for cred in credenciales[tipo_usuario]:
            if usuario.lower() == cred["usuario"].lower() and password == cred["password"]:
                return True, cred["nombre"]
    
    return False, ""