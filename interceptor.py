import os
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

    # Descarga concurrente rápida para no demorar
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

    print()  # Salto de línea al terminar el progreso

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
            print("🔑 Token de sesión actualizado automáticamente en .env")
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

def actualizar_datos():
    with sync_playwright() as p:
        print("🚀 Iniciando navegador de Playwright...")
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./sesion_zmartboard", 
            headless=False # Cambiar a True una vez confirmada la sesión
        )
        
        page = browser.new_page()
        page.on("response", capturar_workspace)
        
        print("🌐 Navegando a ZmartBoard...")
        url_tablero = "https://www.zmartboard.cloud/" 
        page.goto(url_tablero)
        
        # Clic automático en Sign in si aparece
        print("🤖 Verificando botón de inicio de sesión...")
        try:
            boton = page.locator("text='Sign in'")
            boton.wait_for(state="visible", timeout=5000)
            boton.click()
            print("👆 ¡Clic automático en 'Sign in' realizado!")
        except Exception:
            print("⏭️ No se requirió clic en Sign in (o ya se encuentra dentro).")
        
        print("⏳ Esperando a que el tablero cargue e intercepte los datos (hasta 45s)...")
        inicio = time.time()
        while not estado_captura["listo"] and (time.time() - inicio) < 45:
            page.wait_for_timeout(1000)
            
        if not estado_captura["listo"]:
            print("❌ No se interceptó la petición de workspace en el tiempo límite.")
            print("💡 Si tu sesión expiró, inicia sesión en la ventana del navegador y vuelve a ejecutar.")
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

    with open('tablero_actualizado.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("🎉 ¡Archivo tablero_actualizado.json guardado exitosamente con todas las tarjetas y subtareas completas!")

if __name__ == "__main__":
    actualizar_datos()