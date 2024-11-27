from fastapi import FastAPI, File, UploadFile 
from fastapi.middleware.cors import CORSMiddleware 
from keybert import KeyBERT
import networkx as nx

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
    allow_methods=["POST"],
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

def initialize_graph():
  global graph
  # Cargamos una instancia del Graph 
  graph = nx.Graph()
  print("Grafo inicializado")

def copy_lines(contents):
  count = -1
  data_lines = []
  lines = contents.decode('utf-8').splitlines()
  for line in lines:
    if line.startswith(">"):                
      data_lines.append(line)
      count = count + 1
    else:
      data_lines[count] = data_lines[count] + line 
  return data_lines

@app.on_event("startup")
async def startup_event():
  initialize_bert_model()
  initialize_graph()

@app.get('/')
async def index():
  return { "message": "This is a keyword extraction app with linked words from multiple documents!" }

@app.post("/upload_documents_txt/")
async def upload_documents_txt(file: UploadFile = File(...)):
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
      data_lines = copy_lines(contents)

      # procesamos los datos para extraer las keywords
      if kw_model is None:
        return {"error": "El modelo no está inicializado."} 

      key_dict = {}
      for n, line in enumerate(data_lines):
        # stop_words='english' / by default=None 
        # highlight=False, 
        # top_n=10
        # keyphrase_ngram_range=(1, 2), stop_words=None  
        keywords = kw_model.extract_keywords(line, 
                                             keyphrase_ngram_range=(1, 3), 
                                             highlight=False,
                                             #top_n=10,
                                             stop_words='english')  
        key_dict[f"document_{n}"] = keywords    
        # Enlazar keyword que pertenecen a un mismo documento
        for i, a_word in enumerate(keywords):
          for j, b_word in enumerate(keywords):
            if j > i:
              if graph.has_edge(a_word[0], b_word[0]) != True:
                graph.add_edge(a_word[0], b_word[0], document_count=1)
              else:
                try:
                  document_att = nx.get_edge_attributes(graph, "document_count")                  
                  att_count_value = document_att[(a_word[0], b_word[0])]
                  #print(f"{a_word[0]} + {b_word[0]}: {att_count_value}")
                  graph.add_edge(a_word[0], b_word[0], document_count = (att_count_value + 1))                
                except Exception as e:
                  return {"error": f"Procesando atributos de la conexión: {str(e)}"}

      list_edges = list(graph.edges(data=True))
      return {"Keywords": key_dict, "Graph": list_edges}
    except Exception as e:
        return {"error": f"No se pudo procesar el archivo: {str(e)}"}