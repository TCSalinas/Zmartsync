import json
from playwright.sync_api import sync_playwright

def guardar_json_si_es_workspace(response):
    if "workspace" in response.url and response.status == 200:
        try:
            data = response.json()
            with open('tablero_actualizado.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print("✅ ¡JSON interceptado y guardado como tablero_actualizado.json!")
        except:
            pass

def actualizar_datos():
    with sync_playwright() as p:
        print("🚀 Iniciando navegador de Playwright...")
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./sesion_zmartboard", 
            headless=False # ¡Ya puedes probarlo en True (invisible)!
        )
        
        page = browser.new_page()
        page.on("response", guardar_json_si_es_workspace)
        
        print("🌐 Navegando a ZmartBoard...")
        url_tablero = "https://www.zmartboard.cloud/" 
        page.goto(url_tablero)
        
        # --- INICIO MODO HACKER: Clic automático ---
        print("🤖 Buscando el botón de inicio de sesión...")
        try:
            # Buscamos el texto exacto que descubriste en el HTML
            boton = page.locator("text='Sign in'")
            
            # Forzamos a Playwright a esperar a que el botón aparezca en pantalla (hasta 5 seg)
            boton.wait_for(state="visible", timeout=5000)
            
            # Hacemos el clic
            boton.click()
            print("👆 ¡Clic automático realizado con éxito!")
        except Exception as e:
            print(f"⏭️ No se encontró el botón. Saltando... (Detalle: {e})")
        # --- FIN MODO HACKER ---
        
        print("⏳ Esperando 10 segundos para que cargue el tablero y se intercepte el JSON...")
        # Como ahora es automático, 10 segundos deberían ser suficientes
        page.wait_for_timeout(10000)
        
        print("🛑 Cerrando navegador...")
        browser.close()

if __name__ == "__main__":
    actualizar_datos()  