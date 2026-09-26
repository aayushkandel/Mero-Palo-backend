import secrets
import string


def generate_uid():
    characters = string.ascii_uppercase + string.digits
    value = ''.join(secrets.choice(characters) for _ in range(10))

    return f"{value[:4]}-{value[4:8]}-{value[8:10]}"