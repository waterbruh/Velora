"""Generiert VAPID-Keys für Velora Web-Push.

Ausgabe ist direkt als ENV-Block formatiert — einfach in .env umleiten:

    python scripts/generate_vapid.py >> .env

Keys werden nirgends persistiert — nur stdout.
"""

from py_vapid import Vapid01


def main() -> None:
    v = Vapid01()
    v.generate_keys()

    priv_pem = v.private_pem().decode()
    # Escape-Newlines für ENV-File-Format (sonst bricht systemd EnvironmentFile)
    priv_escaped = priv_pem.replace("\n", "\\n").strip("\\n")

    pub = v.public_key_urlsafe_base64()

    print(f'VAPID_PRIVATE_KEY="{priv_escaped}"')
    print(f"VAPID_PUBLIC_KEY={pub}")
    print("VAPID_SUBJECT=mailto:max.lechner06@gmail.com")


if __name__ == "__main__":
    main()
