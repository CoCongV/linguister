
def generate_ph(en=None, us=None):
    if not en:
        en = str([])
    else:
        en = str([en])
    if not us:
        us = str([])
    else:
        us = str([us])
    return 'US ' + us + ' UK ' + en