# ZmartSync 📋⚡

Herramienta de automatización en Python para iniciar sesión en [ZmartBoard](https://www.zmartboard.cloud/) e interceptar las tarjetas y datos del tablero (workspace) para exportarlos automáticamente en formato JSON.

---

## 📌 ¿Cómo funciona?

El script principal (`interceptor.py`) utiliza **Playwright** para:
1. Iniciar un contexto de navegador persistente (`sesion_zmartboard/`), guardando cookies y credenciales locales para no tener que iniciar sesión manualmente cada vez.
2. Navegar automáticamente a ZmartBoard y autenticarse.
3. Interceptar en tiempo real las respuestas de red dirigidas al endpoint `workspace`.
4. Extraer la información completa del tablero y guardarla en `tablero_actualizado.json`.

---

## 🚀 Requisitos Previos

- **Python 3.10+**
- **Git**

---

## 🛠️ Instalación

1. **Clonar el repositorio** (o situarte en la carpeta del proyecto):
   ```bash
   git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
   cd zmartsync
   ```

2. **Crear y activar un entorno virtual**:
   - En Linux / macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - En Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar los navegadores de Playwright**:
   ```bash
   playwright install chromium
   ```

---

## 💻 Uso

### 1. Primer uso (Guardar sesión inicial)
La primera vez que ejecutes el script, es recomendable que el navegador esté visible (`headless=False`) para verificar o completar el inicio de sesión:

1. Ejecuta:
   ```bash
   python interceptor.py
   ```
2. Si es necesario, inicia sesión con tu cuenta de ZmartBoard en la ventana del navegador.
3. Una vez autenticado, la sesión quedará guardada en la carpeta `sesion_zmartboard/`. Las próximas ejecuciones mantendrán tu cuenta iniciada sin pedir credenciales.

### 2. Extracción automática
Una vez guardada la sesión:
1. Ejecuta:
   ```bash
   python interceptor.py
   ```
2. El script abrirá el tablero, interceptará la petición del espacio de trabajo y creará/actualizará el archivo:
   ```text
   tablero_actualizado.json
   ```

> [!TIP]
> **Modo invisible (Headless):**
> Puedes cambiar `headless=True` en la línea 20 de `interceptor.py` para que el script se ejecute en segundo plano sin levantar la ventana del navegador.

---

## 📁 Estructura del Proyecto

```text
zmartsync/
├── interceptor.py            # Script principal con Playwright (interceptor de peticiones)
├── zmartsync.py              # Script alternativo para peticiones directas vía API REST
├── requirements.txt          # Dependencias de Python
├── .env.example              # Plantilla de variables de entorno
├── .gitignore                # Reglas para excluir sesiones, datos privados y venv
└── README.md                 # Documentación del proyecto
```

---

## 🔒 Seguridad y Privacidad

El archivo `.gitignore` incluido en este repositorio está configurado para **proteger tus datos sensibles**:
- `sesion_zmartboard/`: Contiene las cookies y tokens de tu sesión activa. **Nunca debe subirse a Git.**
- `*.json`: Evita subir los datos y tarjetas privadas extraídas de tu tablero.
- `.venv/`: Ignora el entorno virtual.

> [!CAUTION]
> Si utilizas `zmartsync.py`, ten cuidado de **no quemar tokens JWT o correos personales directamente en el código**. Se recomienda usar variables de entorno (`.env`).
