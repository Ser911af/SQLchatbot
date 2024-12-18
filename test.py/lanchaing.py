import os
import sqlite3
from dotenv import load_dotenv  # Para cargar variables de entorno desde .env
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain import hub
from langgraph.prebuilt import create_react_agent

# Cargar variables desde el archivo .env
load_dotenv()

# Obtener la clave API de OpenAI desde las variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("La clave API de OpenAI no se encontró. Asegúrate de que esté configurada en el archivo .env.")

# Función para crear el motor SQLite en memoria
def get_engine_for_local_db(file_path):
    """Leer archivo SQL local, poblar base de datos en memoria y crear el motor."""
    # Leer el contenido del archivo SQL local
    with open(file_path, 'r') as file:
        sql_script = file.read()

    # Crear conexión SQLite en memoria y ejecutar el script
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.executescript(sql_script)

    # Retornar un motor SQLAlchemy conectado a la base de datos en memoria
    return create_engine(
        "sqlite://",
        creator=lambda: connection,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

# Especificar la ruta del archivo local
local_file_path = "/workspaces/codespaces-blank/Chinook_Sqlite.sql"

# Crear el motor utilizando el archivo local
engine = get_engine_for_local_db(local_file_path)

# Crear instancia de SQLDatabase
db = SQLDatabase(engine)

# Crear el modelo de lenguaje
llm = ChatOpenAI(model="gpt-4", openai_api_key=OPENAI_API_KEY)

# Configurar el toolkit SQL para interactuar con la base de datos
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
toolkit.get_tools()

# Crear un prompt personalizado
custom_prompt = """
Eres un asistente contable y financiero experto en SQL. Tienes amplios conocimientos sobre cómo interactuar con bases de datos relacionales y generar consultas SQL precisas y optimizadas. 
Tu tarea es proporcionar análisis claros, consultas detalladas y respuestas útiles basadas en los datos proporcionados.

Al trabajar con la base de datos:
1. Utiliza siempre un lenguaje claro y conciso para explicar tus consultas y respuestas.
2. Si te piden realizar una consulta, estructura la consulta SQL y describe lo que hace antes de ejecutarla.
3. Prioriza la precisión y el contexto en todas tus respuestas.

Tienes acceso a una base de datos SQLite con el dialecto correspondiente.
"""

# Usar el prompt personalizado con el agente
system_message = custom_prompt

# Crear el agente con React
agent_executor = create_react_agent(
    llm, toolkit.get_tools(), state_modifier=system_message
)

# Ejemplo de consulta
example_query = "Lista los tres artistas con más ventas"

# Ejecutar la consulta con el agente
events = agent_executor.stream(
    {"messages": [("user", example_query)]},
    stream_mode="values",
)

# Mostrar los eventos resultantes
for event in events:
    event["messages"][-1].pretty_print()
