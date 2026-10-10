from slowapi import Limiter
from slowapi.util import get_remote_address

# Limitador basado en IP de origen. Se usa sobre todo en /auth/login y
# /auth/register para dificultar ataques de fuerza bruta / credential
# stuffing (probar muchas contraseñas o crear muchas cuentas rapido).
limiter = Limiter(key_func=get_remote_address)
