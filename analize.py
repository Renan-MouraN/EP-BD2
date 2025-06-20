import psycopg2
from psycopg2 import Error
import time
import random
import string
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np

load_dotenv()

# Código para análise de desempenho de inserção e consulta em um banco de dados PostgreSQL, cria uma base teste para testar inserções e 
# testa consultas com e sem índices adicionais na base original.


# --- Configurações do Banco de Dados ---
DB_NAME = "bd2_teste123"  
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

# --- Dados de Teste ---
NUM_USUARIOS_INSERT = 150000  # Número de usuários para inserir em cada fase
NUM_ANIMAIS_INSERT = 200000  # Número de animais para inserir em cada fase
NUM_CONSULTAS_TESTE = 100    # Número de vezes para rodar cada consulta para média


# --- Função para gerar dados aleatórios (mantida) ---
def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def generate_random_email():
    return f"{generate_random_string(10)}@{generate_random_string(5)}.com"

def generate_random_phone():
    return f"({random.randint(11,99)})9{random.randint(1000,9999)}-{random.randint(1000,9999)}"

def generate_random_city():
    cities = ["Sao Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Porto Alegre", "Brasilia", "Salvador", "Fortaleza", "Recife", "Goiania"]
    return random.choice(cities)

def generate_random_state():
    states = ["SP", "RJ", "MG", "PR", "RS", "DF", "BA", "CE", "PE", "GO"]
    return random.choice(states)

def generate_random_animal_name():
    names = ["Rex", "Miau", "Buddy", "Nina", "Luna", "Mel", "Thor", "Zeus", "Apollo", "Bella"]
    return random.choice(names)

def generate_random_animal_type():
    types = ["cachorro", "gato", "outro"]
    return random.choice(types)

def generate_random_animal_size():
    sizes = ["pequeno", "medio", "grande"]
    return random.choice(sizes)

def generate_random_animal_sex():
    sexes = ["macho", "femea"]
    return random.choice(sexes)

def generate_random_animal_status():
    statuses = ["disponivel", "adotado", "em_tratamento"]
    return random.choice(statuses)

# --- Funções de Conexão e Gerenciamento do BD ---

# Conecta ao banco de dados padrão para criar/dropar 'bd2'
def connect_to_default_db():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres", # Conecta ao banco padrão para criar/dropar outros bancos
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True # Autocommit para operações de CREATE/DROP DATABASE
        return conn
    except Error as e:
        print(f"Erro ao conectar ao banco padrão para gerenciamento: {e}")
        return None

# Conecta ao banco de dados de teste
def connect_to_test_db():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Error as e:
        print(f"Erro ao conectar ao banco de dados '{DB_NAME}': {e}")
        return None

def create_database(db_name):
    print(f"Criando banco de dados '{db_name}'...")
    conn = connect_to_default_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name};")
            print(f"Banco de dados '{db_name}' criado com sucesso.")
        except Error as e:
            if "already exists" in str(e):
                print(f"Banco de dados '{db_name}' já existe. Prosseguindo.")
            else:
                print(f"Erro ao criar banco de dados '{db_name}': {e}")
        finally:
            if conn:
                conn.close()

def drop_database(db_name):
    print(f"Removendo banco de dados '{db_name}' (se existir)...")
    conn = connect_to_default_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Termina todas as conexões ativas com o banco antes de dropar
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                  AND pid <> pg_backend_pid();
            """)
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
            print(f"Banco de dados '{db_name}' removido com sucesso.")
        except Error as e:
            print(f"Erro ao remover banco de dados '{db_name}': {e}")
        finally:
            if conn:
                conn.close()

def drop_tables_if_exists(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DROP TABLE IF EXISTS itens_pedido CASCADE;
            DROP TABLE IF EXISTS pedidos CASCADE;
            DROP TABLE IF EXISTS adocao CASCADE;
            DROP TABLE IF EXISTS depoimentos CASCADE;
            DROP TABLE IF EXISTS produtos CASCADE;
            DROP TABLE IF EXISTS pedidos_servico CASCADE;
            DROP TABLE IF EXISTS prestador_servicos CASCADE;
            DROP TABLE IF EXISTS prestadores CASCADE;
            DROP TABLE IF EXISTS servicos CASCADE;
            DROP TYPE IF EXISTS status_pedido; -- Dropar tipo ENUM antes da tabela
            DROP TABLE IF EXISTS animal CASCADE;
            DROP TABLE IF EXISTS usuarios CASCADE;
        """)
        conn.commit()
        print("Tabelas existentes (e tipos ENUM) removidas do DB de teste.")
    except Error as e:
        print(f"Erro ao remover tabelas: {e}")
        conn.rollback()

def create_tables(conn):
    try:
        # Conteúdo do seu schema.sql
        schema_sql = """
        -- Tabela de usuários
        CREATE TABLE usuarios (
            id_usuario SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            senha VARCHAR(100) NOT NULL,
            telefone VARCHAR(50),
            endereco TEXT,
            cidade VARCHAR(50),
            estado CHAR(2),
            is_admin BOOLEAN DEFAULT FALSE,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabela de animais
        CREATE TABLE animal (
            id_animal SERIAL PRIMARY KEY,
            nome VARCHAR(50) NOT NULL,
            idade INT,
            porte VARCHAR(20) CHECK (porte IN ('pequeno', 'medio', 'grande')),
            tipo VARCHAR(20) CHECK (tipo IN ('cachorro', 'gato', 'outro')),
            sexo VARCHAR(10) CHECK (sexo IN ('macho', 'femea')),
            descricao TEXT,
            status VARCHAR(20) DEFAULT 'disponivel' CHECK (status IN ('disponivel', 'adotado', 'em_tratamento')),
            imagem VARCHAR(255),
            data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabela de adoções
        CREATE TABLE adocao (
            id_adocao SERIAL PRIMARY KEY,
            id_usuario INT REFERENCES usuarios(id_usuario),
            id_animal INT REFERENCES animal(id_animal),
            data_adocao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovada', 'rejeitada')),
            observacoes TEXT
        );

        -- Tabela de produtos
        CREATE TABLE produtos (
            id_produto SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            preco DECIMAL(10, 2) NOT NULL,
            descricao TEXT,
            categoria VARCHAR(50),
            estoque INT DEFAULT 0,
            imagem VARCHAR(255),
            destaque BOOLEAN DEFAULT FALSE
        );

        -- Tabela de pedidos
        CREATE TABLE pedidos (
            id_pedido SERIAL PRIMARY KEY,
            id_usuario INT REFERENCES usuarios(id_usuario),
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valor_total DECIMAL(10, 2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'pago', 'enviado', 'entregue', 'cancelado'))
        );

        -- Tabela de itens de pedido
        CREATE TABLE itens_pedido (
            id_item SERIAL PRIMARY KEY,
            id_pedido INT REFERENCES pedidos(id_pedido),
            id_produto INT REFERENCES produtos(id_produto),
            quantidade INT NOT NULL,
            preco_unitario DECIMAL(10, 2) NOT NULL
        );

        -- Tabela de depoimentos
        CREATE TABLE depoimentos (
            id_depoimento SERIAL PRIMARY KEY,
            id_usuario INT REFERENCES usuarios(id_usuario),
            id_animal INT REFERENCES animal(id_animal),
            texto TEXT NOT NULL,
            aprovado BOOLEAN DEFAULT FALSE,
            data_depoimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );


        /* ---------- 1. Catálogo de serviços ---------- */
        CREATE TABLE servicos (
            id_servico        SERIAL PRIMARY KEY,
            nome              TEXT        NOT NULL,
            descricao         TEXT,
            preco_base        NUMERIC(10,2),
            duracao_minutos   INTEGER,
            ativo             BOOLEAN     DEFAULT TRUE,
            criado_em         TIMESTAMP   DEFAULT NOW(),
            categoria         VARCHAR(50)
        );

        /* ---------- 2. Prestadores de serviço ---------- */
        CREATE TABLE prestadores (
            id_prestador      SERIAL PRIMARY KEY,
            id_usuario        INTEGER     REFERENCES usuarios(id_usuario),
            nome_completo     TEXT        NOT NULL,
            bio               TEXT,
            telefone          TEXT,
            cidade            TEXT,
            estado            CHAR(2),
            avaliacao_media   NUMERIC(2,1),
            verificado        BOOLEAN     DEFAULT FALSE,
            criado_em         TIMESTAMP   DEFAULT NOW()
        );

        /* ---------- 3. Relação Prestador × Serviço (N:N) ---------- */
        CREATE TABLE prestador_servicos (
            id_prestador_serv SERIAL PRIMARY KEY,
            id_prestador      INTEGER REFERENCES prestadores(id_prestador)   ON DELETE CASCADE,
            id_servico        INTEGER REFERENCES servicos(id_servico)        ON DELETE CASCADE,
            preco             NUMERIC(10,2),
            raio_atendimento_km INTEGER,
            tempo_estimado_min INTEGER,
            ativo             BOOLEAN     DEFAULT TRUE,
            UNIQUE (id_prestador, id_servico)
        );

        /* ---------- 4. Pedidos / agendamentos de serviço ---------- */
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_pedido') THEN
                CREATE TYPE status_pedido AS ENUM ('pendente','confirmado','concluido','cancelado');
            END IF;
        END
        $$;

        CREATE TABLE pedidos_servico (
            id_pedido_servico SERIAL PRIMARY KEY,
            id_animal         INTEGER REFERENCES animal(id_animal)                     ON DELETE CASCADE,
            id_prestador_serv INTEGER REFERENCES prestador_servicos(id_prestador_serv),
            id_tutor          INTEGER REFERENCES usuarios(id_usuario),
            inicio            TIMESTAMP NOT NULL,
            fim               TIMESTAMP,
            status            status_pedido DEFAULT 'pendente',
            observacoes       TEXT,
            criado_em         TIMESTAMP DEFAULT NOW()
        );
        """
        cursor = conn.cursor()
        cursor.execute(schema_sql)
        conn.commit()
        print("Tabelas criadas com sucesso (apenas PKs e UNIQUEs implícitas).")
    except Error as e:
        print(f"Erro ao criar tabelas: {e}")
        conn.rollback()

def add_indexes(conn):
    try:
        cursor = conn.cursor()
        indexes_sql = """
        -- Tabela: usuarios
        CREATE INDEX idx_usuarios_cidade_estado ON usuarios (cidade, estado);
        CREATE INDEX idx_usuarios_is_admin ON usuarios (is_admin);

        -- Tabela: animal
        CREATE INDEX idx_animal_status ON animal (status);
        CREATE INDEX idx_animal_tipo ON animal (tipo);
        CREATE INDEX idx_animal_porte ON animal (porte);
        CREATE INDEX idx_animal_data_entrada ON animal (data_entrada);

        -- Tabela: adocao
        CREATE INDEX idx_adocao_status ON adocao (status);
        CREATE INDEX idx_adocao_data_adocao ON adocao (data_adocao);
        CREATE INDEX idx_adocao_id_usuario ON adocao (id_usuario);
        CREATE INDEX idx_adocao_id_animal ON adocao (id_animal);

        -- Tabela: pedidos
        CREATE INDEX idx_pedidos_id_usuario ON pedidos (id_usuario);
        CREATE INDEX idx_pedidos_status ON pedidos (status);
        CREATE INDEX idx_pedidos_data_pedido ON pedidos (data_pedido);

        -- Tabela: depoimentos
        CREATE INDEX idx_depoimentos_id_usuario ON depoimentos (id_usuario);
        CREATE INDEX idx_depoimentos_id_animal ON depoimentos (id_animal);
        CREATE INDEX idx_depoimentos_aprovado ON depoimentos (aprovado);
        CREATE INDEX idx_depoimentos_data_depoimento ON depoimentos (data_depoimento);

        -- Tabela: prestadores
        CREATE INDEX idx_prestadores_cidade_estado ON prestadores (cidade, estado);
        CREATE INDEX idx_prestadores_verificado ON prestadores (verificado);
        CREATE INDEX idx_prestadores_id_usuario ON prestadores (id_usuario);

        -- Tabela: prestador_servicos
        CREATE INDEX idx_prestador_servicos_ativo ON prestador_servicos (ativo);

        -- Tabela: pedidos_servico
        CREATE INDEX idx_pedidos_servico_id_tutor ON pedidos_servico (id_tutor);
        CREATE INDEX idx_pedidos_servico_id_prestador_serv ON pedidos_servico (id_prestador_serv);
        CREATE INDEX idx_pedidos_servico_status ON pedidos_servico (status);
        CREATE INDEX idx_pedidos_servico_inicio ON pedidos_servico (inicio);
        """
        cursor.execute(indexes_sql)
        conn.commit()
        print("Índices adicionados com sucesso.")
    except Error as e:
        print(f"Erro ao adicionar índices: {e}")
        conn.rollback()

def populate_usuarios(conn, num_usuarios):
    print(f"\nPopulando {num_usuarios} usuários...")
    cursor = conn.cursor()
    start_time = time.time()
    for _ in range(num_usuarios):
        nome = generate_random_string(random.randint(5, 15)).capitalize()
        email = generate_random_email()
        senha = generate_random_string(10) # Senha fictícia
        telefone = generate_random_phone()
        endereco = f"{random.randint(1,999)} {generate_random_string(10)} St"
        cidade = generate_random_city()
        estado = generate_random_state()
        is_admin = random.choice([True, False])

        try:
            cursor.execute(
                """
                INSERT INTO usuarios (nome, email, senha, telefone, endereco, cidade, estado, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (nome, email, senha, telefone, endereco, cidade, estado, is_admin)
            )
        except Error as e:
            # Em testes de volume, email único pode ser um problema, ignorar ou gerar novo
            if "duplicate key value violates unique constraint" in str(e):
                pass
            else:
                raise e
    conn.commit()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Inserção de {num_usuarios} usuários concluída em {elapsed_time:.4f} segundos.")
    return elapsed_time

def populate_animal(conn, num_animais):
    print(f"\nPopulando {num_animais} animais...")
    cursor = conn.cursor()
    start_time = time.time()
    for _ in range(num_animais):
        nome = generate_random_animal_name()
        idade = random.randint(1, 15)
        porte = generate_random_animal_size()
        tipo = generate_random_animal_type()
        sexo = generate_random_animal_sex()
        descricao = f"Um animal {tipo} muito {random.choice(['amigável', 'brincalhão', 'calmo'])}."
        status = generate_random_animal_status()
        imagem = f"http://example.com/images/{generate_random_string(5)}.jpg"

        cursor.execute(
            """
            INSERT INTO animal (nome, idade, porte, tipo, sexo, descricao, status, imagem)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (nome, idade, porte, tipo, sexo, descricao, status, imagem)
        )
    conn.commit()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Inserção de {num_animais} animais concluída em {elapsed_time:.4f} segundos.")
    return elapsed_time

def drop_custom_indexes(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT indexname FROM pg_indexes WHERE schemaname = 'public'
            AND indexname LIKE 'idx_%';
        """)
        indexes_to_drop = cursor.fetchall()
        for index_name in indexes_to_drop:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {index_name[0]};")
                conn.commit()
            except Error as e:
                print(f"Erro ao remover índice {index_name[0]}: {e}")
                conn.rollback()
        print("Todos os índices customizados removidos.")
    except Error as e:
        print(f"Erro ao tentar remover índices: {e}")
        conn.rollback()

def measure_query_performance(conn, query_name, query_sql, num_runs=NUM_CONSULTAS_TESTE):
    cursor = conn.cursor()
    total_execution_time = 0
    print(f"\nExecutando {query_name} ({num_runs} vezes)...")

    # Limpar cache da sessão (para PostgreSQL, não é tão direto, mas executar VACUUM pode ajudar em testes isolados)
    # ou simplesmente descartar a primeira execução
    # cursor.execute("VACUUM ANALYZE;") # Pode ser lento para tabelas muito grandes

    # Warm-up run (descartar a primeira execução para pré-carregar caches)
    cursor.execute(query_sql)


    for i in range(num_runs):
        start_time = time.time()
        cursor.execute(query_sql)
        end_time = time.time()
        total_execution_time += (end_time - start_time)

        # Opcional: printar o plano de EXPLAIN ANALYZE para uma das execuções
        if i == 0: # Printar apenas a primeira vez para não poluir
            print(f"--- EXPLAIN ANALYZE para {query_name} (primeira execução) ---")
            explain_cursor = conn.cursor()
            explain_cursor.execute("EXPLAIN ANALYZE " + query_sql)
            for row in explain_cursor.fetchall():
                print(row[0])
            print("-------------------------------------------------------------------")


    avg_time = total_execution_time / num_runs
    print(f"Tempo médio para {query_name}: {avg_time:.6f} segundos.")
    return avg_time


def analyze_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("ANALYZE usuarios;")
        cursor.execute("ANALYZE animal;")
        conn.commit()
        print("Tabelas analisadas para atualizar estatísticas.")
    except Error as e:
        print(f"Erro ao analisar tabelas: {e}")
        conn.rollback()

# --- Fluxo Principal ---
if __name__ == "__main__":
    # Garante que o banco de dados de teste exista para podermos conectar a ele
    create_database(DB_NAME)

    # --- Fase 1: Teste SEM Índices Adicionais ---
    print("\n--- Fase 1: Teste de INSERÇÃO SEM Índices Adicionais ---")
    conn_no_index = connect_to_test_db()
    if conn_no_index:
        try:
            drop_tables_if_exists(conn_no_index)
            create_tables(conn_no_index)
            analyze_tables(conn_no_index) # Garante estatísticas atualizadas para o planejador

            print("\n>> Medindo tempo de INSERÇÃO sem índices adicionais...")
            insert_time_usuarios_no_index = populate_usuarios(conn_no_index, NUM_USUARIOS_INSERT)
            insert_time_animal_no_index = populate_animal(conn_no_index, NUM_ANIMAIS_INSERT)

        except Exception as e:
            print(f"Ocorreu um erro na Fase 1: {e}")
        finally:
            if conn_no_index:
                conn_no_index.close()
                print("Conexão da Fase 1 fechada.")
    else:
        print("Não foi possível estabelecer conexão para a Fase 1.")
        exit() # Sair se a conexão falhar

    # --- Fase 2: Teste COM Índices Adicionais ---
    print("\n--- Fase 2: Teste de INSERÇÃO COM Índices Adicionais ---")
    conn_with_index = connect_to_test_db()
    if conn_with_index:
        try:
            drop_tables_if_exists(conn_with_index) # Limpa o DB para esta fase
            create_tables(conn_with_index)       # Recria as tabelas
            add_indexes(conn_with_index)         # Adiciona os índices
            analyze_tables(conn_with_index)      # Atualiza as estatísticas

            print("\n>> Medindo tempo de INSERÇÃO com índices adicionados...")
            insert_time_usuarios_with_index = populate_usuarios(conn_with_index, NUM_USUARIOS_INSERT)
            insert_time_animal_with_index = populate_animal(conn_with_index, NUM_ANIMAIS_INSERT)

        except Exception as e:
            print(f"Ocorreu um erro na Fase 2: {e}")
        finally:
            if conn_with_index:
                conn_with_index.close()
                print("Conexão da Fase 2 fechada.")
    else:
        print("Não foi possível estabelecer conexão para a Fase 2.")
        exit() # Sair se a conexão falhar


    # --- Fase 3: Teste de Consulta (Query) com e sem Índices ---
    print("\n--- Fase 3: Teste de CONSULTA (Query) com e sem Índices ---")
    conn_phase3 = psycopg2.connect(
            dbname="petmatch", # Conecta ao banco padrão para criar/dropar outros bancos
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    if conn_phase3:
        try:
            print("\n>> Medindo tempo de CONSULTA COM índices...")
            analyze_tables(conn_phase3) # Atualiza as estatísticas

            query1 = "SELECT id_usuario, nome, email FROM usuarios WHERE cidade = 'Sao Paulo' AND estado = 'SP';"
            query2 = "SELECT id_animal, nome, idade, porte, tipo, sexo, descricao, status, imagem, data_entrada FROM animal  where status = 'disponivel' and tipo = 'cachorro';"
            query3 = "SELECT id_usuario, nome FROM usuarios WHERE is_admin = TRUE;"
            query4 = """
                SELECT u.nome AS usuario_nome, a.nome AS animal_nome, ad.data_adocao
                FROM adocao ad
                JOIN usuarios u ON ad.id_usuario = u.id_usuario
                JOIN animal a ON ad.id_animal = a.id_animal
                WHERE a.data_entrada >= '2025-04-01' and ad.status = 'pendente';
            """

            avg_query1_with_index = measure_query_performance(conn_phase3, "Q1 (Usuarios Cidade/Estado) COM Índice", query1)
            avg_query2_with_index = measure_query_performance(conn_phase3, "Q2 (Animal Status) COM Índice", query2)
            avg_query3_with_index = measure_query_performance(conn_phase3, "Q3 (Usuarios IsAdmin) COM Índice", query3)
            avg_query4_with_index = measure_query_performance(conn_phase3, "Q4 (Adocao com JOIN) COM Índice", query4)

            # 3. Testar consultas SEM índices (removendo-os e reanalisando)
            print("\n>> Medindo tempo de CONSULTA SEM índices (removendo e retestando)...")
            drop_custom_indexes(conn_phase3) # Remove apenas os índices customizados
            analyze_tables(conn_phase3)      # Atualiza as estatísticas para o planejador

            avg_query1_no_index = measure_query_performance(conn_phase3, "Q1 (Usuarios Cidade/Estado) SEM Índice", query1)
            avg_query2_no_index = measure_query_performance(conn_phase3, "Q2 (Animal Status) SEM Índice", query2)
            avg_query3_no_index = measure_query_performance(conn_phase3, "Q3 (Usuarios IsAdmin) SEM Índice", query3)
            avg_query4_no_index = measure_query_performance(conn_phase3, "Q4 (Adocao com JOIN) SEM Índice", query4)

            add_indexes(conn_phase3) # Adiciona os indexes novamente

            # 4. Comparar resultados da Fase 3
            print("\n--- Resultados da Análise de Desempenho de CONSULTA ---")

            print("\nConsulta 1: SELECT id_usuario, nome, email FROM usuarios WHERE cidade = 'Sao Paulo' AND estado = 'SP';")
            if avg_query1_with_index is not None and avg_query1_no_index is not None:
                print(f"  COM Índices: {avg_query1_with_index:.6f} segundos.")
                print(f"  SEM Índices: {avg_query1_no_index:.6f} segundos.")
                if avg_query1_no_index > 0:
                    improvement = ((avg_query1_no_index - avg_query1_with_index) / avg_query1_no_index) * 100
                    print(f"  Ganho de Desempenho: {improvement:.2f}% (positivo = melhoria)")
            else:
                print("  Dados insuficientes para comparação da Q1.")


            print("\nConsulta 2: SELECT id_animal, nome, tipo FROM animal WHERE status = 'disponivel';")
            if avg_query2_with_index is not None and avg_query2_no_index is not None:
                print(f"  COM Índices: {avg_query2_with_index:.6f} segundos.")
                print(f"  SEM Índices: {avg_query2_no_index:.6f} segundos.")
                if avg_query2_no_index > 0:
                    improvement = ((avg_query2_no_index - avg_query2_with_index) / avg_query2_no_index) * 100
                    print(f"  Ganho de Desempenho: {improvement:.2f}% (positivo = melhoria)")
            else:
                print("  Dados insuficientes para comparação da Q2.")

            print("\nConsulta 3: SELECT id_usuario, nome FROM usuarios WHERE is_admin = TRUE;")
            if avg_query3_with_index is not None and avg_query3_no_index is not None:
                print(f"  COM Índices: {avg_query3_with_index:.6f} segundos.")
                print(f"  SEM Índices: {avg_query3_no_index:.6f} segundos.")
                if avg_query3_no_index > 0:
                    improvement = ((avg_query3_no_index - avg_query3_with_index) / avg_query3_no_index) * 100
                    print(f"  Ganho de Desempenho: {improvement:.2f}% (positivo = melhoria)")
            else:
                print("  Dados insuficientes para comparação da Q3.")

            if 'avg_query4_with_index' in locals() and avg_query4_with_index is not None and \
               'avg_query4_no_index' in locals() and avg_query4_no_index is not None:
                print("\nConsulta 4: Adocao com JOIN")
                print(f"  COM Índices: {avg_query4_with_index:.6f} segundos.")
                print(f"  SEM Índices: {avg_query4_no_index:.6f} segundos.")
                if avg_query4_no_index > 0:
                    improvement = ((avg_query4_no_index - avg_query4_with_index) / avg_query4_no_index) * 100
                    print(f"  Ganho de Desempenho: {improvement:.2f}% (positivo = melhoria)")
            else:
                print("  Dados insuficientes para comparação da Q4 ou query omitida.")


        except Exception as e:
            print(f"Ocorreu um erro na Fase 3: {e}")
        finally:
            if conn_phase3:
                conn_phase3.close()
                print("Conexão da Fase 3 fechada.")
    else:
        print("Não foi possível estabelecer conexão para a Fase 3.")
        exit()


    # --- Resultados Finais Consolidados (Fase 1 e 2) ---
    print("\n--- Resultados Finais Consolidados da Análise de Desempenho ---")

    print("\nTempo de Inserção (USUARIOS):")
    print(f"  Sem Índices Adicionais: {insert_time_usuarios_no_index:.4f} segundos para {NUM_USUARIOS_INSERT} registros.")
    print(f"  Com Índices Adicionais: {insert_time_usuarios_with_index:.4f} segundos para {NUM_USUARIOS_INSERT} registros.")
    diff_usuarios_insert = insert_time_usuarios_with_index - insert_time_usuarios_no_index
    if insert_time_usuarios_no_index > 0:
        percent_change_usuarios_insert = (diff_usuarios_insert / insert_time_usuarios_no_index) * 100
        print(f"  Piora/Melhora: {'+' if diff_usuarios_insert > 0 else ''}{diff_usuarios_insert:.4f} segundos ({percent_change_usuarios_insert:.2f}%)")


    print("\nTempo de Inserção (ANIMAL):")
    print(f"  Sem Índices Adicionais: {insert_time_animal_no_index:.4f} segundos para {NUM_ANIMAIS_INSERT} registros.")
    print(f"  Com Índices Adicionais: {insert_time_animal_with_index:.4f} segundos para {NUM_ANIMAIS_INSERT} registros.")
    diff_animal_insert = insert_time_animal_with_index - insert_time_animal_no_index
    if insert_time_animal_no_index > 0:
        percent_change_animal_insert = (diff_animal_insert / insert_time_animal_no_index) * 100
        print(f"  Piora/Melhora: {'+' if diff_animal_insert > 0 else ''}{diff_animal_insert:.4f} segundos ({percent_change_animal_insert:.2f}%)")

    # Limpeza final do banco de dados de teste (opcional, descomente para limpar)
    drop_database("bd2_teste123")
    print(f"\nBanco de dados '{"bd2_teste123"}' removido para limpeza.")

    import csv

    # Prepare dados para CSV e gráficos
    csv_rows = [
        ["Teste", "Sem Índices (s)", "Com Índices (s)", "Diferença (s)", "Variação (%)"]
    ]

    # Inserção USUARIOS
    diff_usuarios_insert = insert_time_usuarios_with_index - insert_time_usuarios_no_index
    percent_change_usuarios_insert = (diff_usuarios_insert / insert_time_usuarios_no_index) * 100 if insert_time_usuarios_no_index > 0 else 0
    csv_rows.append([
        "Inserção Usuarios",
        f"{insert_time_usuarios_no_index:.4f}",
        f"{insert_time_usuarios_with_index:.4f}",
        f"{diff_usuarios_insert:.4f}",
        f"{percent_change_usuarios_insert:.2f}"
    ])

    # Inserção ANIMAL
    diff_animal_insert = insert_time_animal_with_index - insert_time_animal_no_index
    percent_change_animal_insert = (diff_animal_insert / insert_time_animal_no_index) * 100 if insert_time_animal_no_index > 0 else 0
    csv_rows.append([
        "Inserção Animal",
        f"{insert_time_animal_no_index:.4f}",
        f"{insert_time_animal_with_index:.4f}",
        f"{diff_animal_insert:.4f}",
        f"{percent_change_animal_insert:.2f}"
    ])

    # Consultas
    def add_query_result_to_csv(label, with_idx, no_idx):
        diff = with_idx - no_idx
        percent = (diff / no_idx) * 100 if no_idx > 0 else 0
        csv_rows.append([
            label,
            f"{no_idx:.6f}",
            f"{with_idx:.6f}",
            f"{diff:.6f}",
            f"{percent:.2f}"
        ])

    add_query_result_to_csv("Consulta 1", avg_query1_with_index, avg_query1_no_index)
    add_query_result_to_csv("Consulta 2", avg_query2_with_index, avg_query2_no_index)
    add_query_result_to_csv("Consulta 3", avg_query3_with_index, avg_query3_no_index)
    add_query_result_to_csv("Consulta 4", avg_query4_with_index, avg_query4_no_index)

    # Escreve resultados em CSV
    csv_filename = "resultados_desempenho.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_rows)
    print(f"\nResultados salvos em '{csv_filename}'.")

    # --- Início da Geração de Gráficos SEPARADOS ---

    # Função auxiliar para adicionar rótulos nas barras
    def autolabel(ax, rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    # 1. Gráfico de Barras para Tempos de INSERÇÃO (Usuários)
    if insert_time_usuarios_no_index is not None and insert_time_usuarios_with_index is not None:
        labels_insert_users = ["Sem Índices", "Com Índices"]
        times_insert_users_no_index = [insert_time_usuarios_no_index]
        times_insert_users_with_index = [insert_time_usuarios_with_index]

        x = np.arange(len(labels_insert_users))
        width = 0.35

        fig_users, ax_users = plt.subplots(figsize=(8, 5))
        rects1_users = ax_users.bar(x[0] - width/2, times_insert_users_no_index, width, label='Sem Índices', color='skyblue')
        rects2_users = ax_users.bar(x[1] + width/2, times_insert_users_with_index, width, label='Com Índices', color='lightcoral')

        ax_users.set_ylabel('Tempo (segundos)')
        ax_users.set_title(f'Tempo de Inserção de {NUM_USUARIOS_INSERT} Usuários')
        ax_users.set_xticks(x)
        ax_users.set_xticklabels(labels_insert_users)
        ax_users.legend()
        ax_users.grid(axis='y', linestyle='--', alpha=0.7)

        autolabel(ax_users, rects1_users)
        autolabel(ax_users, rects2_users)

        fig_users.tight_layout()
        plt.savefig('insertion_time_users.png')
        plt.close(fig_users) # Fecha a figura para liberar memória
        print("\nGráfico 'insertion_time_users.png' gerado.")

    # 2. Gráfico de Barras para Tempos de INSERÇÃO (Animais)
    if insert_time_animal_no_index is not None and insert_time_animal_with_index is not None:
        labels_insert_animals = ["Sem Índices", "Com Índices"]
        times_insert_animals_no_index = [insert_time_animal_no_index]
        times_insert_animals_with_index = [insert_time_animal_with_index]

        x = np.arange(len(labels_insert_animals))
        width = 0.35

        fig_animals, ax_animals = plt.subplots(figsize=(8, 5))
        rects1_animals = ax_animals.bar(x[0] - width/2, times_insert_animals_no_index, width, label='Sem Índices', color='skyblue')
        rects2_animals = ax_animals.bar(x[1] + width/2, times_insert_animals_with_index, width, label='Com Índices', color='lightcoral')

        ax_animals.set_ylabel('Tempo (segundos)')
        ax_animals.set_title(f'Tempo de Inserção de {NUM_ANIMAIS_INSERT} Animais')
        ax_animals.set_xticks(x)
        ax_animals.set_xticklabels(labels_insert_animals)
        ax_animals.legend()
        ax_animals.grid(axis='y', linestyle='--', alpha=0.7)

        autolabel(ax_animals, rects1_animals)
        autolabel(ax_animals, rects2_animals)

        fig_animals.tight_layout()
        plt.savefig('insertion_time_animals.png')
        plt.close(fig_animals) # Fecha a figura para liberar memória
        print("Gráfico 'insertion_time_animals.png' gerado.")


    # 3. Gráfico de Barras para Tempos de CONSULTA (Todas as Consultas)
    query_labels = []
    sem_indices_queries = []
    com_indices_queries = []

    # Preenche listas apenas com dados válidos de consulta
    if avg_query1_no_index is not None and avg_query1_with_index is not None:
        query_labels.append("Consulta 1")
        sem_indices_queries.append(avg_query1_no_index)
        com_indices_queries.append(avg_query1_with_index)

    if avg_query2_no_index is not None and avg_query2_with_index is not None:
        query_labels.append("Consulta 2")
        sem_indices_queries.append(avg_query2_no_index)
        com_indices_queries.append(avg_query2_with_index)

    if avg_query3_no_index is not None and avg_query3_with_index is not None:
        query_labels.append("Consulta 3")
        sem_indices_queries.append(avg_query3_no_index)
        com_indices_queries.append(avg_query3_with_index)

    if avg_query4_no_index is not None and avg_query4_with_index is not None:
        query_labels.append("Consulta 4")
        sem_indices_queries.append(avg_query4_no_index)
        com_indices_queries.append(avg_query4_with_index)


    if query_labels: # Só gera o gráfico se houver dados de consulta válidos
        x_queries = np.arange(len(query_labels))
        width_queries = 0.35

        fig_queries, ax_queries = plt.subplots(figsize=(12, 6))
        rects1_queries = ax_queries.bar(x_queries - width_queries/2, sem_indices_queries, width_queries, label='Sem Índices', color='mediumseagreen')
        rects2_queries = ax_queries.bar(x_queries + width_queries/2, com_indices_queries, width_queries, label='Com Índices', color='indianred')

        ax_queries.set_ylabel('Tempo (segundos)')
        ax_queries.set_title('Comparativo de Tempo de Consultas (Com vs Sem Índices)')
        ax_queries.set_xticks(x_queries)
        ax_queries.set_xticklabels(query_labels, rotation=30, ha='right')
        ax_queries.legend()
        ax_queries.grid(axis='y', linestyle='--', alpha=0.7)

        autolabel(ax_queries, rects1_queries)
        autolabel(ax_queries, rects2_queries)

        fig_queries.tight_layout()
        plt.savefig('query_performance.png')
        plt.close(fig_queries) # Fecha a figura para liberar memória
        print("Gráfico 'query_performance.png' gerado.")

    # --- Fim da Geração de Gráficos SEPARADOS ---