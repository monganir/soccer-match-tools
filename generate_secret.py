from cryptography.fernet import Fernet

# Generate and save key once
key = Fernet.generate_key()
with open("secret.key", "wb") as f:
    f.write(key)

fernet = Fernet(key)

# Encrypt passwords
teams = {
    "T1": {
        "email": "<email for yrsl team management login>",
        "password": fernet.encrypt(b"pwd").decode()
    },
    "T2": {
        "email": "<email for yrsl team management login>",
        "password": fernet.encrypt(b"pwd").decode()
    },
    "T3": {
        "email": "<email for yrsl team management login>",
        "password": fernet.encrypt(b"pwd").decode()
    },
    "T4": {
        "email": "<email for yrsl team management login>",
        "password": fernet.encrypt(b"pwd").decode()
    }
}

import json
with open("secure_config.json", "w") as f:
    json.dump(teams, f, indent=2)
