import sqlite3
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

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

import getpass
import os

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: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")

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

toolkit.get_tools()

from langchain import hub

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")

assert len(prompt_template.messages) == 1
print(prompt_template.input_variables)
system_message = prompt_template.format(dialect="SQLite", top_k=5)

from langgraph.prebuilt import create_react_agent

agent_executor = create_react_agent(
    llm, toolkit.get_tools(), state_modifier=system_message
)

example_query = "lista los tres artistas con mas ventas"

events = agent_executor.stream(
    {"messages": [("user", example_query)]},
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()