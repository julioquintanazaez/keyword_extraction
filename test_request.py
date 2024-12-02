import requests
from pathlib import Path

# Nombre del archivo
fileurl = "D:\\DESARROLLO\\PYTHON\\keyword_extraction\\"
filename = fileurl + "datos_text.txt"

# Crear un objeto Path
file_path = Path(filename)

# Obtener la ruta absoluta
file_path = file_path.resolve()

print("Ruta absoluta:", file_path)

run_local = False
if run_local:
    url = "http://127.0.0.1:8000/app/v1/upload_documents/"
else:
    url = "https://keyword-extraction-graph.onrender.com/app/v1/upload_documents/"

headers = {
    "Accept": "application/json",
    #"Content-Type": "multipart/form-data"
}

with open(str(file_path), 'rb') as f:  # Convertir a string
    files = {'file': (file_path.name, f, 'text/plain')}  # Usar file_path.name para el nombre
    response = requests.post(url, files=files, headers=headers)

if response.status_code == 200:
    print(f"Existe un resultado positivo, Run from: {run_local}")
    response_data = response.json()
    print("Datos de la respuesta:", response_data)
else:
    print("Existe un resultado negativo")
    

