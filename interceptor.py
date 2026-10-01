import os
import sys
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from playwright.sync_api import sync_playwright

# Estado global para almacenar los datos interceptados
estado_captura = {
    "workspace_data": None,
    "auth_token": None,
    "listo": False
}

def enriquecer_subtareas(data, auth_token):
    """
    Consulta la API de ZmartBoard para obtener el título y detalle completo
    de cada subtarea en las tarjetas que contengan subtareas.
    """
    columns = data.get("currentBoard", {}).get("columns", [])
    
    # Recolectar todas las tareas que tengan subtareas
    tareas_con_subtareas = []
    for col in columns:
        for task in col.get("tasks", []):
            if task.get("subtasks") and len(task["subtasks"]) > 0:
                tareas_con_subtareas.append(task)
                
    total_tareas = len(tareas_con_subtareas)
    if total_tareas == 0:
        print("ℹ️ No se encontraron tarjetas con subtareas para enriquecer.")
        return data

    print(f"\n🔍 Encontradas {total_tareas} tarjetas con subtareas. Descargando títulos y detalles...")

    if not auth_token.startswith("Bearer "):
        auth_header = f"Bearer {auth_token}"
    else:
        auth_header = auth_token

    headers = {
        "authorization": auth_header,
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.zmartboard.cloud",
        "referer": "https://www.zmartboard.cloud/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    session = requests.Session()
    session.headers.update(headers)

    def fetch_subtasks(task):
        task_id = task["id"]
        url = f"https://api.zmartboard.cloud/api/tasks/{task_id}/subtasks"
        try:
            res = session.get(url, timeout=10)
            if res.status_code == 200:
                return task_id, res.json()
            else:
                return task_id, None
        except Exception:
            return task_id, None

    # Descarga concurrente rápida para optimizar tiempos
    subtareas_por_tarea = {}
    completadas = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_subtasks, t): t for t in tareas_con_subtareas}
        for future in as_completed(futures):
            task_id, subtasks_detalle = future.result()
            completadas += 1
            if subtasks_detalle is not None:
                subtareas_por_tarea[task_id] = subtasks_detalle
            print(f"\r⏳ Progreso subtareas: {completadas}/{total_tareas} tarjetas procesadas", end="", flush=True)

    print()  # Salto de línea

    # Reemplazar las subtareas con los detalles completos (título, estado, fechas, etc.)
    subtareas_totales = 0
    for task in tareas_con_subtareas:
        t_id = task["id"]
        if t_id in subtareas_por_tarea:
            task["subtasks"] = subtareas_por_tarea[t_id]
            subtareas_totales += len(subtareas_por_tarea[t_id])

    print(f"✅ ¡{subtareas_totales} subtareas enriquecidas con éxito con su texto/título!")
    return data

def actualizar_env_token(token):
    """Actualiza el token en el archivo .env local si existe"""
    env_path = ".env"
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "ZMARTBOARD_TOKEN=" in content:
            content = re.sub(r'ZMARTBOARD_TOKEN="[^"]*"', f'ZMARTBOARD_TOKEN="{token}"', content)
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("🔑 Token de sesión actualizado en .env")
    except Exception:
        pass

def capturar_workspace(response):
    if "workspace" in response.url and response.status == 200:
        try:
            data = response.json()
            auth = response.request.headers.get("authorization")
            estado_captura["workspace_data"] = data
            estado_captura["auth_token"] = auth
            estado_captura["listo"] = True
            print("✅ ¡Petición de workspace interceptada!")
        except Exception as e:
            print(f"⚠️ Error al leer respuesta de workspace: {e}")

def imprimir_resumen(data):
    """Imprime un resumen visual del tablero exportado."""
    project_name = data.get("project", {}).get("title") or data.get("project", {}).get("name", "Proyecto")
    board = data.get("currentBoard", {})
    board_title = board.get("title", "Tablero")
    columns = board.get("columns", [])
    
    total_tareas = 0
    tareas_con_asignados = 0
    tareas_con_subtareas = 0
    total_subtareas = 0
    tareas_con_prs = 0
    
    print("\n" + "="*50)
    print(f"📊 RESUMEN: {project_name} - {board_title}")
    print("="*50)
    
    for col in columns:
        col_name = col.get("name", "Columna")
        tasks = col.get("tasks", [])
        total_tareas += len(tasks)
        print(f"  • {col_name}: {len(tasks)} tarjetas")
        for t in tasks:
            if t.get("assignedUsers"):
                tareas_con_asignados += 1
            if t.get("subtasks"):
                tareas_con_subtareas += 1
                total_subtareas += len(t["subtasks"])
            if t.get("pullRequests"):
                tareas_con_prs += 1
                
    print("-"*50)
    print(f"📌 Total de tarjetas: {total_tareas}")
    print(f"👤 Tarjetas con personas asignadas: {tareas_con_asignados}")
    print(f"☑️  Tarjetas con subtareas: {tareas_con_subtareas} ({total_subtareas} subtareas con título)")
    print(f"🔀 Tarjetas con PRs vinculados: {tareas_con_prs}")
    print("="*50)

def actualizar_datos():
    # Soporta modo headless y selección de navegador (--headless, --firefox)
    headless_mode = "--headless" in sys.argv or os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    use_firefox = "--firefox" in sys.argv or os.getenv("BROWSER", "").lower() == "firefox"

    # Detección de entorno gráfico en Linux / WSL
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if sys.platform.startswith("linux") and not has_display and not headless_mode:
        print("⚠️ No se detectó un servidor gráfico ($DISPLAY o Wayland) en este entorno Linux/WSL.")
        print("🔄 Cambiando automáticamente a modo --headless...")
        print("💡 Nota: Si necesitas iniciar sesión por primera vez, consulta la sección de WSL en el README.\n")
        headless_mode = True

    with sync_playwright() as p:
        browser_type_name = "Firefox" if use_firefox else "Chromium"
        print(f"🚀 Iniciando navegador {browser_type_name} (modo {'headless' if headless_mode else 'visible'})...")
        
        # Flags para máxima compatibilidad en WSL, Docker y evitar caídas en CDP
        chromium_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--no-first-run",
            "--disable-blink-features=AutomationControlled",
        ]

        browser_engine = p.firefox if use_firefox else p.chromium
        launch_kwargs = {
            "user_data_dir": "./sesion_zmartboard",
            "headless": headless_mode,
        }
        if not use_firefox:
            launch_kwargs["args"] = chromium_args
        
        try:
            browser = browser_engine.launch_persistent_context(**launch_kwargs)
        except Exception as e:
            err = str(e)
            print("\n" + "!"*65)
            print("❌ ERROR AL INICIAR EL NAVEGADOR DE PLAYWRIGHT:")
            print(f"   {err}\n")
            if any(k in err.lower() for k in ["sigtrap", "trace/breakpoint", "signal 5", "133"]):
                print("💡 SOLUCIÓN PARA ERROR SIGTRAP EN WSL2:")
                print("   1. Aumenta los mapas de memoria del kernel de WSL2 (ejecuta en terminal):")
                print("      👉 sudo sysctl -w vm.max_map_count=1048576")
                print("   2. O ejecuta usando Firefox (no utiliza protocolo CDP vulnerable a SIGTRAP):")
                print("      👉 playwright install firefox")
                print("      👉 python interceptor.py --firefox")
                print("   3. O la opción definitiva: ejecuta el script en PowerShell de Windows directamente.\n")
            elif any(k in err.lower() for k in ["missing dependencies", "host system is missing", "shared object", "cannot open shared"]):
                print("💡 SOLUCIÓN (Faltan librerías del sistema Linux/WSL):")
                print("   Ejecuta en tu terminal de WSL/Linux:")
                print("   👉 sudo playwright install-deps\n")
            elif any(k in err.lower() for k in ["display", "target closed", "context or browser has been closed"]):
                print("💡 SOLUCIÓN PARA WSL (Sin entorno gráfico o WSLg desactualizado):")
                print("   Opción 1: En PowerShell de Windows, actualiza WSL ejecutando:")
                print("             wsl --update")
                print("   Opción 2: Ejecuta este proyecto directamente en Windows (PowerShell/CMD).")
                print("   Opción 3: Ejecuta en modo invisible:")
                print("             python interceptor.py --headless\n")
            print("!"*65 + "\n")
            return
        
        page = browser.new_page()
        page.on("response", capturar_workspace)
        
        print("🌐 Navegando a ZmartBoard...")
        url_tablero = "https://www.zmartboard.cloud/" 
        page.goto(url_tablero)
        
        # Clic automático en Sign in si aparece
        print("🤖 Verificando botón de inicio de sesión...")
        try:
            boton = page.locator("text='Sign in'")
            boton.wait_for(state="visible", timeout=3000)
            boton.click()
            print("👆 ¡Clic automático en 'Sign in' realizado!")
        except Exception:
            print("⏭️ No se requirió clic en Sign in (o ya se encuentra dentro).")
        
        print("⏳ Esperando a que el tablero cargue e intercepte los datos (hasta 90s)...")
        if not headless_mode:
            print("💡 Si es tu primera vez o tu sesión expiró, inicia sesión en la ventana del navegador.")
            
        inicio = time.time()
        timeout_max = 90
        while not estado_captura["listo"] and (time.time() - inicio) < timeout_max:
            page.wait_for_timeout(1000)
            
        if not estado_captura["listo"]:
            print("❌ No se interceptó la petición de workspace en el tiempo límite.")
            print("💡 Asegúrate de iniciar sesión en la ventana del navegador (ejecuta sin --headless).")
            browser.close()
            return
        
        print("🛑 Cerrando navegador...")
        browser.close()

    # Procesar y enriquecer los datos interceptados
    data = estado_captura["workspace_data"]
    auth_token = estado_captura["auth_token"]

    if auth_token:
        actualizar_env_token(auth_token.replace("Bearer ", "").strip())
        data = enriquecer_subtareas(data, auth_token)
    else:
        print("⚠️ No se encontró encabezado Authorization en la petición interceptada. Se guardará sin subtareas enriquecidas.")

    archivo_salida = 'tablero_actualizado.json'
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 ¡Archivo {archivo_salida} guardado exitosamente!")
    imprimir_resumen(data)

if __name__ == "__main__":
    actualizar_datos()