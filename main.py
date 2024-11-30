from fastapi import FastAPI, File, UploadFile 
from fastapi.middleware.cors import CORSMiddleware 
from keybert import KeyBERT
import networkx as nx
from fastapi.responses import JSONResponse

import sys
if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO

# Create an instance for the app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initializate KeyBERT instance
kw_model = None
graph = None

def initialize_bert_model():
  global kw_model 
  # Cargamos una instancia del modelo BERT  
  # kw_model = KeyBERT(model="all-mpnet-base-v2")  # Instantiate KeyBERT model
  kw_model = KeyBERT()
  print("Modelo inicializado")

def copy_lines(contents):
  count = -1
  data_lines = []
  lines = contents.decode('utf-8').splitlines()
  flag_first_line = True
  columns_info = ""
  for line in lines:
    if flag_first_line:  #To skip the first line that contains the columns names
      columns_info = line
      flag_first_line = False
    else:
      if line.startswith(">"):   
        # Split to capture the columns info                    
        data_lines.append(line)
        count = count + 1
      else:
        data_lines[count] = data_lines[count] + line 
  return data_lines, columns_info

def get_attributes(data, columns, ini):
  attributes = {}         
  for i in range(ini, len(data)):
    col = columns[i].strip()
    try:      
      if data[i] == " ":
        attributes[col] = "?"
      else:
        attributes[col] = data[i].strip()
    except:
        attributes[col] = "?"

  return attributes

@app.on_event("startup")
async def startup_event():
  initialize_bert_model()

@app.get('/')
async def index():
  info = """
    This is a keyword extraction app with linked words from multiple documents!
    Also, it is capable of handle multiple attributes to add more information to
    the links. As input the api recieve a csv file with a foxed structure (>, text, from, location).
    The file used this (>) symbol to especifies the starting point of an line.
    Example: 
    >text, from, location
    >Class overlapping has long been regarded as one of the toughest pervasive 
    problems in classification. When it is combined with class imbalance problem the situation
    becomes even more complicated with few works in the literature addressing this combinative 
    effect., Telegram, Spain

    Also: you can add more atributes, always folowing the csv restrictions.

    {"keywords":
      {
      "document_0": [
        [
          "grouping large",
          0.5263
        ]
      },
      "graph": [
          [
            "grouping large",
            "data critical",
            {
              "from": "Facebook",
              "location": "Cuba",
              "Time": "3",
              "document_count": 1
            }
          ]
      ]
    }

  """
  return {"message": info}

@app.post("/upload_documents/")
async def upload_documents_txt(file: UploadFile = File(...)):
    graph = nx.Graph()
    # Obtener el nombre del archivo
    filename = file.filename    
    # Extraer la extensión
    extension = filename.split('.')[-1] if '.' in filename else ''
    # Verificamos que el archivo sea un fichero TXT  
    if extension != 'txt':
        return {"error": f"El archivo debe ser un fichero de texto. {file.content_type}"}
    # Leemos el archivo CSV en un DataFrame de pandas  
    try:
      contents = await file.read()
      data_lines, columns = copy_lines(contents)
      
      # procesamos los datos para extraer las keywords
      if kw_model is None:
        return {"error": "El modelo no está inicializado."} 

      key_dict = {}
      columns = columns.split(",") # Line: ["text", "from", "localization"]  
      
      for n, line in enumerate(data_lines):
        data_ = line.split(",")
        keywords = kw_model.extract_keywords(data_[0], 
                                             keyphrase_ngram_range=(1, 2), 
                                             highlight=False,
                                             stop_words='english')  
        key_dict[f"document_{n}"] = keywords
        attributes = get_attributes(data_, columns, 1)   
      
        # Enlazar keyword que pertenecen a un mismo documento
        for i, a_word in enumerate(keywords):
          for j, b_word in enumerate(keywords):
            if j > i:              
              if graph.has_edge(a_word[0], b_word[0]) != True:
                attributes["document_count"] = 1
                graph.add_edge(a_word[0], b_word[0], **attributes)
              else:
                try:
                  document_att = nx.get_edge_attributes(graph, "document_count")                  
                  att_count_value = document_att[(a_word[0], b_word[0])]
                  #print(f"{a_word[0]} + {b_word[0]}: {att_count_value}")
                  attributes["document_count"] = (att_count_value + 1)
                  graph.add_edge(a_word[0], b_word[0], **attributes)
                except Exception as e:
                  return {"error": f"Procesando atributos de la conexión: {str(e)}"}              
      
      list_edges = list(graph.edges(data=True))
      return {"keywords": key_dict, "graph": list_edges}
      
    except Exception as e:
        return {"error": f"No se pudo procesar el archivo: {str(e)}"}
    
@app.post("/check_uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    # Aquí puedes procesar el archivo como desees
    return JSONResponse(content={"filename": file.filename, "size": len(content)})

# Run the main app.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)