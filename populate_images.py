import psycopg2
import requests
import os
from dotenv import load_dotenv
import time
import random
from urllib.parse import quote_plus

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path='app/Backend/.env') 

# --- Configurações ---
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

# URLs das APIs de imagens de animais
DOG_API_URL = "https://api.thedogapi.com/v1/images/search"
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"
# A API de raposas será usada para a categoria "outro".
FOX_API_URL = "https://randomfox.ca/floof/"


def get_db_connection():
    """Estabelece e retorna uma conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def get_image_url(api_url, retries=3, delay=1):
    """
    Busca uma URL de imagem de uma API especificada, com um mecanismo de retentativa.
    """
    for attempt in range(retries):
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()  
            data = response.json()

            if not data:
                continue

            # Lida com a estrutura de thedogapi e thecatapi: [{'url': '...'}]
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'url' in data[0]:
                return data[0]['url']
            
            # Lida com a estrutura de randomfox.ca: {'image': '...'}
            elif isinstance(data, dict) and 'image' in data:
                return data.get('image')
            
        except requests.exceptions.RequestException as e:
            print(f"  -> Tentativa {attempt + 1} falhou para {api_url}. Erro: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"  -> Todas as tentativas falharam para {api_url}.")
        except (IndexError, TypeError, KeyError) as e:
            print(f"Erro ao processar a resposta da API ({api_url}): {e}")
            return None
    
    return None

def update_animal_images(conn):
    """Atualiza as imagens dos animais no banco de dados."""
    print("\n--- A iniciar a atualização das imagens de ANIMAIS ---")
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id_animal, tipo, nome FROM animal ORDER BY id_animal;")
            items = cur.fetchall()
            total = len(items)
            print(f"Encontrados {total} animais para processar.")

            for i, (item_id, item_type, item_name) in enumerate(items):
                image_url = None
                print(f"A processar o animal {i + 1}/{total}: ID {item_id} ({item_name})")

                if item_type == 'cachorro':
                    image_url = get_image_url(DOG_API_URL)
                elif item_type == 'gato':
                    image_url = get_image_url(CAT_API_URL)
                else: 
                    # Usa a API de raposas para todos os animais da categoria 'outro'
                    image_url = get_image_url(FOX_API_URL)

                if not image_url:
                    print(f"  -> Falha ao obter imagem real, a usar placeholder.")
                    image_url = f"https://placehold.co/400x300/6C63FF/FFFFFF?text={quote_plus(item_name)}"
                
                cur.execute("UPDATE animal SET imagem = %s WHERE id_animal = %s;", (image_url, item_id))
                #time.sleep(0.3)
            
            conn.commit()
            print("--- Atualização das imagens de ANIMAIS concluída. ---")

    except psycopg2.Error as e:
        print(f"\nOcorreu um erro de banco de dados em ANIMAIS: {e}")
        conn.rollback()

if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        update_animal_images(conn)
        
        if conn:
            conn.close()
            print("\nConexão com o banco de dados fechada.")