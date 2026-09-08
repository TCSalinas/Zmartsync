import os
import json
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

TOKEN = os.getenv("ZMARTBOARD_TOKEN")
PROJECT_ID = os.getenv("ZMARTBOARD_PROJECT_ID")

if not TOKEN or not PROJECT_ID:
    print("⚠️ Por favor configura ZMARTBOARD_TOKEN y ZMARTBOARD_PROJECT_ID en un archivo .env")

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'es-419,es;q=0.9,en;q=0.8,it;q=0.7,de;q=0.6,ca;q=0.5',
    'authorization': f'Bearer {TOKEN}',
    'cache-control': 'no-cache',
    'origin': 'https://www.zmartboard.cloud',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.zmartboard.cloud/',
    'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Opera GX";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 OPR/134.0.0.0 (Edition std-1)',
}

url = f'https://api.zmartboard.cloud/api/projects/{PROJECT_ID}/workspace'
response = requests.get(url, headers=headers)

try:
    data = response.json()
    if isinstance(data, dict):
        print("Llaves principales del JSON:", data.keys())

    # Guardarlo en un archivo bonito y ordenado
    with open('tablero_zmartboard.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("✅ ¡JSON guardado exitosamente como tablero_zmartboard.json!")
except Exception as e:
    print(f"❌ Error al procesar respuesta: {e} (Status code: {response.status_code})")