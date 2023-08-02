import keyring


def get_keyring_password(service, email):
    password = keyring.get_password(service, email)
    return password
