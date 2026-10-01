# ZmartSync 📋⚡

Herramienta en Python para automatizar el inicio de sesión en [ZmartBoard](https://www.zmartboard.cloud/) y extraer todas las tarjetas, subtareas, personas asignadas, fechas y pull requests en un archivo JSON unificado y listo para usar (`tablero_actualizado.json`).

---

## 🌟 Características

- 🤖 **Sesión persistente con Playwright**: Guarda localmente la sesión de navegación (`sesion_zmartboard/`) para no tener que ingresar credenciales en cada ejecución.
- 📥 **Extracción completa del tablero**: Obtiene todas las columnas (Backlog, To Do, In Progress, Review, Done, Blocked, etc.) y todas las tarjetas asociadas.
- ☑️ **Subtareas con títulos completos**: ZmartBoard solo envía IDs en la vista general del tablero; ZmartSync consulta concurrentemente la API para descargar el texto, estado y fechas de cada subtarea.
- 👤 **Integrantes asignados**: Extrae el nombre, apellido, correo institucional (`@uc.cl`) e identificadores de cada responsable.
- 🔀 **Pull Requests de GitHub vinculados**: Incluye número de PR, enlace directo a GitHub (`htmlUrl`), estado (`OPEN`, `MERGED`, `CLOSED`) y estado de revisión.
- 📅 **Fechas y plazos**: Registra `deadline` (fecha límite), `startedAt`, `doneAt`, fechas de creación/actualización y el ciclo o sprint activo (`activeCycle`).
- 📝 **Descripciones y etiquetas**: Preserva el texto completo de las especificaciones y todos los labels de cada tarea.
- 📊 **Resumen automático en consola**: Muestra un panel informativo con el conteo de tarjetas por columna y métricas del tablero.
- 🕶️ **Modo invisible (Headless)**: Permite ejecutarse en segundo plano con el parámetro `--headless`.

---

## 🚀 Requisitos Previos

- **Python 3.10** o superior.
- **Git**.

---

## 🛠️ Instalación Rápida

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/TCSalinas/Zmartsync.git
   cd Zmartsync
   ```

2. **Crear y activar un entorno virtual**:
   - **En Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **En Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar el navegador de Playwright con dependencias del sistema**:
   - En Windows (PowerShell) o macOS:
     ```bash
     playwright install chromium
     ```
   - En Linux o WSL (instala Chromium y las librerías del sistema necesarias):
     ```bash
     playwright install --with-deps chromium
     ```
     *(O si ya lo tienes instalado: `sudo playwright install-deps`).*

---

## 🐧 ¿Usas WSL (Windows Subsystem for Linux)?

En entornos WSL son muy comunes dos situaciones:

1. **Error de librerías del sistema (`Host system is missing dependencies` o error de `.so`)**:
   - Solución rápida en tu terminal WSL:
     ```bash
     sudo playwright install-deps
     ```

2. **Error al abrir la ventana gráfica (`Target closed` o falta de `$DISPLAY`)**:
   - **Opción recomendada (más simple)**: Clona y corre el proyecto directamente desde **PowerShell o CMD de Windows** (sin entrar a WSL). Windows abrirá la ventana del navegador de forma 100% nativa sin necesidad de configurar pantallas virtuales.
   - **Opción WSLg**: Si usas Windows 10/11, abre PowerShell en Windows como Administrador y actualiza WSL:
     ```powershell
     wsl --update
     ```
     Luego reinicia WSL con `wsl --shutdown`.
   - **Opción Headless**: Si ya tienes la sesión iniciada o no necesitas ventana gráfica:
     ```bash
     python interceptor.py --headless
     ```

3. **Crasheo de Chromium con `SIGTRAP` al conectar el protocolo de depuración (CDP)**:
   Ocurre porque el kernel de WSL2 por defecto restringe la cantidad de mapas de memoria virtual (`vm.max_map_count`) que el depurador V8 de Chromium necesita:
   - **Solución A (Aumentar memoria de mapas en WSL)**:
     ```bash
     sudo sysctl -w vm.max_map_count=1048576
     ```
     *(Para hacerlo permanente: `echo "vm.max_map_count=1048576" | sudo tee -a /etc/sysctl.conf`)*.
   - **Solución B (Usar Firefox en vez de Chromium)**:
     Firefox no usa el protocolo CDP y evita por completo este fallo:
     ```bash
     playwright install firefox
     python interceptor.py --firefox
     ```
   - **Solución C**: Correr en Windows PowerShell directamente (no sufre de límites de kernel virtualizado).

---

## 💻 Guía de Uso

### 1. Primer uso (Autenticación y guardado de sesión)

La primera vez debes ejecutar el script en modo visible para iniciar sesión:

```bash
python interceptor.py
```

1. Se abrirá una ventana de Chromium en ZmartBoard.
2. Si aparece el botón **Sign in**, el script intentará hacer clic automáticamente o podrás pulsar en iniciar sesión con tu cuenta / Google.
3. Una vez dentro del tablero, el script:
   - Detectará e interceptará automáticamente los datos del espacio de trabajo.
   - Extraerá el token de autorización temporal.
   - Descargará en paralelo los títulos y detalles de las subtareas.
   - Guardará la sesión en la carpeta local `sesion_zmartboard/`.
   - Generará el archivo `tablero_actualizado.json` e imprimirá el resumen en la terminal.

---

### 2. Siguientes ejecuciones

Dado que tu sesión ya quedó guardada localmente:

- **Modo normal**:
  ```bash
  python interceptor.py
  ```
- **Modo en segundo plano (sin abrir ventana de navegador)**:
  ```bash
  python interceptor.py --headless
  ```

---

## 📊 Ejemplo del Resumen en Terminal

Al finalizar la extracción, verás un reporte como este:

```text
==================================================
📊 RESUMEN: IIC2154.2026-2.S2.Grupo2 - Board
==================================================
  • Backlog: 1 tarjetas
  • Blocked: 0 tarjetas
  • To Do: 7 tarjetas
  • In Progress: 16 tarjetas
  • Review: 3 tarjetas
  • Done: 28 tarjetas
--------------------------------------------------
📌 Total de tarjetas: 55
👤 Tarjetas con personas asignadas: 54
☑️  Tarjetas con subtareas: 17 (70 subtareas con título)
🔀 Tarjetas con PRs vinculados: 14
==================================================
```

---

## 📄 Estructura de cada Tarjeta en `tablero_actualizado.json`

El archivo exportado contiene el tablero completo con la siguiente estructura por cada tarjeta:

```json
{
  "id": "cmtdo4bmy001jjp02p5dhzuli",
  "publicId": "IIC2-22",
  "title": "Configuración inicial Mobile",
  "description": "Texto completo con requerimientos, dependencias y notas...",
  "deadline": "2026-09-10T23:00:00.000Z",
  "assignedUsers": [
    {
      "user": {
        "firstName": "Luis",
        "lastName": "Reyes",
        "email": "luisreyes@uc.cl"
      }
    }
  ],
  "subtasks": [
    {
      "id": "cmuolr2mh0003jk02j7kyqrwo",
      "title": "Crear migración de base de datos",
      "done": false
    }
  ],
  "pullRequests": [
    {
      "number": 15,
      "htmlUrl": "https://github.com/mi-org/mi-repo/pull/15",
      "state": "MERGED",
      "reviewStatus": "APPROVED"
    }
  ],
  "labels": [
    { "label": "Desarrollo Mobile" }
  ]
}
```

---

## 📁 Estructura del Repositorio

```text
Zmartsync/
├── interceptor.py            # Script principal extractor y enriquecedor
├── requirements.txt          # Dependencias de Python (playwright, requests, etc.)
├── .env.example              # Plantilla para variables de entorno opcionales
├── .gitignore                # Protege cookies, datos del tablero y entornos virtuales
└── README.md                 # Documentación e instrucciones
```

---

## 🔒 Privacidad y Seguridad

El archivo `.gitignore` ya viene configurado para que **nunca se suban datos confidenciales**:
- `sesion_zmartboard/`: Contiene las cookies y tokens de tu sesión de navegador.
- `*.json`: Evita subir accidentalmente las tarjetas, descripciones y datos privados de tu equipo.
- `.venv/`: Excluye el entorno virtual.

---

## 🔗 Repositorio

Encuentra el código fuente y novedades en:  
👉 **[https://github.com/TCSalinas/Zmartsync](https://github.com/TCSalinas/Zmartsync)**
