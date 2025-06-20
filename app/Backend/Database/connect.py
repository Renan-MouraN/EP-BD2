import os 
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

def connect_db():
    
    # Constrói a string de conexão com os dados do PostgreSQL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # Cria a engine do SQLAlchemy
    engine = create_engine(DATABASE_URL)

    # Opcional: Testar a conexão (exemplo)
    try:
        with engine.connect() as connection:
            print("Conexão com o banco de dados PostgreSQL estabelecida com sucesso!")
        
        return engine
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados PostgreSQL: {e}")
        raise