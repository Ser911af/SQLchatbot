import streamlit as st
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
import sqlite3
import os
from dotenv import load_dotenv  # Para cargar variables desde .env
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain import hub

# Cargar variables desde el archivo .env
load_dotenv()

headers = {
"authorization": st.secrets["OPENAI_API_KEY"],
"content-type": "application/json"
}

# Obtener la clave de la API de OpenAI desde las variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("La clave API de OpenAI no se encontró. Asegúrate de que esté configurada en el archivo .env.")

# Función para obtener el motor de la base de datos SQLite
def get_engine_for_local_db(file_path):
    with open(file_path, 'r') as file:
        sql_script = file.read()
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.executescript(sql_script)
    return create_engine(
        "sqlite://",
        creator=lambda: connection,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

# Función de inicio de sesión
def login():
    st.sidebar.title("Inicio de sesión")
    username = st.sidebar.text_input("Usuario", "")
    password = st.sidebar.text_input("Contraseña", type="password")
    
    if username == "admin" and password == "1234":
        return True
    elif username and password:
        st.sidebar.error("Usuario o contraseña incorrectos.")
        return False
    return None

# Verificar si el usuario ha iniciado sesión
if login():
    # Crear el motor y la base de datos SQL
    local_file_path = "/workspaces/codespaces-blank/Chinook_Sqlite.sql"
    engine = get_engine_for_local_db(local_file_path)
    db = SQLDatabase(engine)

    # Crear el modelo de lenguaje
    llm = ChatOpenAI(model="gpt-4", openai_api_key=OPENAI_API_KEY)

    # Configurar el toolkit SQL para interactuar con la base de datos
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    toolkit.get_tools()

    # Cargar el template de prompt para el agente
    prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
    system_message = prompt_template.format(dialect="SQLite", top_k=5)

    # Crear el agente con React
    agent_executor = create_react_agent(
        llm, toolkit.get_tools(), state_modifier=system_message
    )

    # Interfaz de usuario con Streamlit
    st.title("💼 Asistente Contable y Financiero con LangChain 📊")
    st.subheader("🔍 Consulta y gestiona tu base de datos de manera fácil y rápida 💡")

    # Caja de texto para que el usuario ingrese una consulta
    user_query = st.text_input("Ingrese su consulta SQL (por ejemplo, 'ventas del ultimo año'): ")

    # Ejecutar la consulta
    if user_query:
        st.write(f"Consultando: {user_query}")
        
        # Obtener la respuesta del agente
        events = agent_executor.stream(
            {"messages": [("user", user_query)]},
            stream_mode="values",
        )

        # Capturar solo el último mensaje (la respuesta humanizada)
        final_response = None
        for event in events:
            final_response = event["messages"][-1].content

        # Mostrar solo la respuesta final
        if final_response:
            st.write(final_response)
else:
    st.write("Por favor, inicie sesión para acceder a la aplicación.")
