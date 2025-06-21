import sqlite3
import requests
import time
import os
from dotenv import load_dotenv
import psycopg2

# Código que trunca as tabelas e as repopula usando Fake

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

DATABASE_NAME = 'petmatch' # Note: This variable isn't used with psycopg2
TABLE_NAME = 'animal'
DOG_API_URL = 'https://dog.ceo/api/breeds/image/random'
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

def get_random_dog_image_url():
    """Busca uma URL de imagem de cachorro aleatória da API Dog.ceo."""
    try:
        response = requests.get(DOG_API_URL)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
        data = response.json()
        return data.get('message')
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar URL da imagem de cachorro: {e}")
        return None

def main():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # 3. Iterar sobre todos os elementos e ajustar a URL
        print("\nIniciando o ajuste das URLs...")
        cursor.execute(f"SELECT id_animal, imagem FROM {TABLE_NAME}")
        rows = cursor.fetchall()

        for row in rows:
            record_id, old_url = row
            new_dog_url = get_random_dog_image_url()

            if new_dog_url:
                # CORREÇÃO AQUI: Use %s para placeholders no psycopg2
                cursor.execute(f"UPDATE {TABLE_NAME} SET imagem = %s WHERE id_animal = %s", (new_dog_url, record_id))
                conn.commit()
                print(f"ID {record_id}: URL ajustada de '{old_url}' para '{new_dog_url}'")
            else:
                print(f"ID {record_id}: Não foi possível obter uma nova URL, pulando.")

            # Pequena pausa para evitar sobrecarregar a API
            time.sleep(0.1)

        print("\nProcesso de ajuste de URLs concluído.")

    except psycopg2.Error as e: # Altere para psycopg2.Error para um tratamento mais específico
        print(f"Erro no banco de dados PostgreSQL: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    main()