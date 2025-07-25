import datetime

def reset_state_if_timeout(state, timeout_seconds=1800):
    """Resetea el estado si han pasado más de timeout_seconds desde last_ts."""
    now_ts = datetime.datetime.utcnow().timestamp()
    last_ts = state.get('last_ts')
    if last_ts and now_ts - last_ts > timeout_seconds:
        # Reinicia todo el flujo excepto el nivel (para no tener que leer la hoja de nuevo)
        return {'data': {}, 'step': 0, 'level': state.get('level'), 'flight_options': [], 'hotel_options': [], 'last_ts': now_ts}
    if not last_ts:
        state['last_ts'] = now_ts
    return state
