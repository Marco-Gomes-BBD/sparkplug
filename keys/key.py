import keyring


def get_keyring_password(service, email):
    password = keyring.get_password(service, email)
    return password


def set_keyring_password(service, email, password):
    keyring.set_password(service, email, password)
