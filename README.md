# 🌐 Actualizador de DNS Dinámico en OVH


![Name](https://img.shields.io/badge/Name-OVHDNSUpdaterScript-red)
[![Version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/codeforusers/ovh-dns-updater/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](https://opensource.org/licenses/Apache-2.0)


Este script permite actualizar automáticamente los registros DNS de tipo **A** y **AAAA** en OVH, asegurando que tu dominio o subdominio siempre apunte a la IP pública actual de tu servidor. Ideal para conexiones con IP dinámica.

---

## 📋 Requisitos Previos

Asegúrate de contar con los siguientes requisitos antes de comenzar:

- **Servidor o equipo con Linux** (probado en Debian/Ubuntu, pero debería funcionar en otras distribuciones).
- **Python 3.x** instalado.
- **Acceso SSH** al servidor.
- **Credenciales API de OVH** (`APP_KEY`, `APP_SECRET` y `CONSUMER_KEY`).
- **Acceso al panel de OVH** para gestionar la zona DNS de tu dominio.

---

## 🚀 Instalación de Dependencias

1. **Instalar Python 3 y pip** (si no los tienes):

    ```bash
    sudo apt update
    sudo apt install python3 python3-pip -y
    ```

2. **Instalar la librería oficial de OVH para Python**:

    ```bash
    pip3 install ovh
    ```

---

## 🗂️ Crear Directorios Necesarios

1. Crear un directorio para almacenar el estado de las actualizaciones:

    ```bash
    sudo mkdir -p /var/lib/ovh_dns_updater
    sudo chown <usuario>:<grupo> /var/lib/ovh_dns_updater
    sudo chmod 700 /var/lib/ovh_dns_updater
    ```

   **Nota**: Sustituye `<usuario>` y `<grupo>` por el usuario que ejecutará el script.

---

## 🔧 Configuración del Archivo `.env`

1. Crear el archivo de configuración en `/etc/ovh-dns-updater.env` con el siguiente contenido:

    ```env
    OVH_ENDPOINT=ovh-eu
    OVH_APP_KEY=xxxxxxxxxxxxxxxx
    OVH_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
    OVH_CONSUMER_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
    OVH_ZONE=midominio.com
    # OVH_SUBDOMAIN=casa      # Descomentar si quieres un subdominio
    OVH_TTL=300
    WANT_IPV6=0
    FORCE_REMOTE_CHECK=0
    IP_SERVICE_V4=https://api.ipify.org
    IP_SERVICE_V6=https://api6.ipify.org
    STATE_FILE=/var/lib/ovh_dns_updater/state.json
    ```

2. **Dar permisos seguros** al archivo `.env`:

    ```bash
    sudo chmod 600 /etc/ovh-dns-updater.env
    ```

---

## ⚡ Ejecución Manual del Script

1. Para probar que todo funciona correctamente, ejecuta el script manualmente:

    ```bash
    OVH_ENV_FILE=/etc/ovh-dns-updater.env python3 /usr/local/bin/ovh_dns_update.py
    ```

    Si todo está bien, el script actualizará el registro **A** (y **AAAA** si `WANT_IPV6=1`).

---

## ⏰ Automatización con Cron

1. Editar el cron del usuario que ejecutará el script:

    ```bash
    crontab -e
    ```

2. Añadir la siguiente línea para ejecutar el script cada **5 minutos**:

    ```bash
    */5 * * * * OVH_ENV_FILE=/etc/ovh-dns-updater.env python3 /usr/local/bin/ovh_dns_update.py >> /var/log/ovh_dns_updater.log 2>&1
    ```

    Esto redirige la salida estándar y de errores a un archivo de log (`/var/log/ovh_dns_updater.log`).

---

## 🔒 Seguridad

- **NO compartas el archivo `.env`** ni lo subas a repositorios públicos.
- Asegúrate de que **solo el usuario autorizado** tenga acceso de lectura al archivo `.env`:

    ```bash
    sudo chmod 600 /etc/ovh-dns-updater.env
    ```

---

## ✅ Verificación

1. Puedes comprobar tu IP pública utilizando:

    ```bash
    curl https://api.ipify.org
    ```

2. Verifica que la IP pública obtenida coincida con la configurada en tu registro DNS después de ejecutar el script.

---

## 📅 Autor

**David C.G. (CodeForUsers)**


---

## 📜 Licencia

Este proyecto está licenciado bajo la **Apache License 2.0**.  
Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 🔗 Enlaces

- **GitHub**: [https://github.com/codeforusers/ovh-dns-updater](https://github.com/codeforusers/ovh-dns-updater)
