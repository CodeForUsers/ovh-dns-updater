#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2025 David C.G. (CodeForUsers)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Requisitos del script:
# pip install ovh requests

# INFO:
# Titulo: OVH DNS Updater Script
# Versión: 25.08.15
# Github: https://github.com/codeforusers


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualiza el registro A (y opcionalmente AAAA) de un dominio/subdominio en OVH
cuando cambia la IP pública, usando credenciales guardadas en un archivo .env.
"""

import json
import os
import sys
import time
from typing import Dict, Optional

import requests
import ovh
from dotenv import load_dotenv


# === 1. Acceso a la configuración y datos de usuario

# Carpeta donde está este script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Lee variable de entorno OVH_ENV_FILE, o por defecto usa el .env en la misma carpeta
ENV_PATH = os.getenv("OVH_ENV_FILE", os.path.join(SCRIPT_DIR, "configuracion_ovh.env"))

if not os.path.exists(ENV_PATH):
    print(f"No se encontró el archivo de entorno: {ENV_PATH}", file=sys.stderr)
    sys.exit(2)

load_dotenv(dotenv_path=ENV_PATH)

# === 2. Funciones auxiliares ===

def getenv_bool(name: str, default: bool = False) -> bool:
    """Lee booleanos desde entorno (1/true/yes/on)."""
    val = os.getenv(name, "").strip().lower()
    return val in {"1", "true", "yes", "y", "on"} if val else default

def getenv_int(name: str, default: int) -> int:
    """Lee enteros desde entorno, con valor por defecto."""
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default

def get_env_or_exit(name: str) -> str:
    """Obtiene una variable obligatoria o sale."""
    val = os.getenv(name)
    if not val:
        print(f"Falta variable requerida: {name}", file=sys.stderr)
        sys.exit(2)
    return val

def get_public_ip(url: str, family: str) -> Optional[str]:
    """Devuelve la IP pública consultando un servicio HTTP."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        ip = r.text.strip()
        if family == "ipv4":
            if all(p.isdigit() and 0 <= int(p) <= 255 for p in ip.split(".")):
                return ip
        else:
            if ":" in ip and len(ip) <= 45:
                return ip
        print(f"IP {family} no válida: {ip}", file=sys.stderr)
    except Exception as e:
        print(f"No se pudo obtener IPv{family[-1]}: {e}", file=sys.stderr)
    return None

def load_state(path: str) -> Dict[str, str]:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(path: str, state: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f)

def fqdn(zone: str, sub: Optional[str]) -> str:
    return f"{sub}.{zone}" if sub else zone

def ovh_client_from_env() -> ovh.Client:
    return ovh.Client(
        endpoint=os.getenv("OVH_ENDPOINT", "ovh-eu"),
        application_key=get_env_or_exit("OVH_APP_KEY"),
        application_secret=get_env_or_exit("OVH_APP_SECRET"),
        consumer_key=get_env_or_exit("OVH_CONSUMER_KEY"),
    )

def upsert_record(client: ovh.Client, zone: str, sub: Optional[str], field_type: str, target_ip: str, ttl: int) -> str:
    """Crea o actualiza un registro DNS A/AAAA."""
    params = {"fieldType": field_type}
    if sub:
        params["subDomain"] = sub
    ids = client.get(f"/domain/zone/{zone}/record", **params)
    changed = False
    if ids:
        for rec_id in ids:
            rec = client.get(f"/domain/zone/{zone}/record/{rec_id}")
            if rec.get("target") != target_ip or int(rec.get("ttl", ttl)) != ttl:
                payload = {"fieldType": field_type, "target": target_ip, "ttl": ttl}
                if sub:
                    payload["subDomain"] = sub
                client.put(f"/domain/zone/{zone}/record/{rec_id}", **payload)
                changed = True
        return "updated" if changed else "unchanged"
    else:
        payload = {"fieldType": field_type, "target": target_ip, "ttl": ttl}
        if sub:
            payload["subDomain"] = sub
        client.post(f"/domain/zone/{zone}/record", **payload)
        return "created"


# === 3. Lógica principal ===

def main():
    zone = get_env_or_exit("OVH_ZONE")
    subdomain = os.getenv("OVH_SUBDOMAIN", "").strip() or None
    ttl = getenv_int("OVH_TTL", 300)
    want_ipv6 = getenv_bool("WANT_IPV6", False)
    force_remote_check = getenv_bool("FORCE_REMOTE_CHECK", False)
    state_path = os.getenv("STATE_FILE", "/var/lib/ovh_dns_updater/state.json")

    ip_service_v4 = os.getenv("IP_SERVICE_V4", "https://api.ipify.org")
    ip_service_v6 = os.getenv("IP_SERVICE_V6", "https://api6.ipify.org")

    try:
        client = ovh_client_from_env()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error creando cliente OVH: {e}", file=sys.stderr)
        sys.exit(5)

    ipv4 = get_public_ip(ip_service_v4, "ipv4")
    if ipv4 is None:
        sys.exit(3)

    ipv6 = get_public_ip(ip_service_v6, "ipv6") if want_ipv6 else None

    state = load_state(state_path)
    last_v4 = state.get("last_ipv4")
    last_v6 = state.get("last_ipv6")

    fqdn_name = fqdn(zone, subdomain)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    actions = []
    did_change = False

    if not force_remote_check:
        if ipv4 == last_v4 and ((not want_ipv6) or ipv6 == last_v6):
            print(f"[{now}] Sin cambios: {fqdn_name} A={ipv4}"
                  + (f" AAAA={ipv6}" if ipv6 else ""))
            sys.exit(0)

    try:
        act4 = upsert_record(client, zone, subdomain, "A", ipv4, ttl)
        actions.append(f"A:{act4}")
        if act4 in {"created", "updated"}:
            did_change = True

        if want_ipv6 and ipv6:
            act6 = upsert_record(client, zone, subdomain, "AAAA", ipv6, ttl)
            actions.append(f"AAAA:{act6}")
            if act6 in {"created", "updated"}:
                did_change = True

        if did_change:
            client.post(f"/domain/zone/{zone}/refresh")

    except ovh.APIError as e:
        print(f"Error OVH: {e}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"Error actualización: {e}", file=sys.stderr)
        sys.exit(5)

    state["last_ipv4"] = ipv4
    if want_ipv6:
        state["last_ipv6"] = ipv6 or ""
    state["last_run"] = now
    save_state(state_path, state)

    print(f"[{now}] {fqdn_name} -> A {ipv4}"
          + (f", AAAA {ipv6}" if ipv6 else "")
          + f" | TTL {ttl} | {', '.join(actions)}")


if __name__ == "__main__":
    main()
