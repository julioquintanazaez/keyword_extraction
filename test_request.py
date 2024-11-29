import requests
from pathlib import Path

# Nombre del archivo
fileurl = "D:\\DESARROLLO\\PYTHON\\keyword_extraction\\"
filename = fileurl + "datos_text.txt"

# Crear un objeto Path
file_path = Path(filename)

# Obtener la ruta absoluta
absolute_path = file_path.resolve()

print("Ruta absoluta:", absolute_path)

url = "https://keyword-extraction-graph.onrender.com/upload_documents_txt/"
localurl = "http://127.0.0.1:8000/upload_documents_txt/"

with open(absolute_path, 'rb') as file:
    # Prepare the files and data for the request  
    print(absolute_path)  
    #files_ = {'file': open(absolute_path, 'rb')}
    files_ = {'file': file}
    data = {'description': 'Some file'}
    # Send the POST request
    response = requests.post(localurl, files=files_, data=data)

if response.status_code == 200:
    print("Existe un resultado positivo")
else:
    print("Existe un resultado negativo")
    

