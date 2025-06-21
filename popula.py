import random
from faker import Faker
from faker.providers import BaseProvider
from faker.providers import internet, lorem, address, date_time, phone_number, person, company
import psycopg2
from psycopg2.errors import IntegrityError
from decimal import Decimal
from dotenv import load_dotenv

# Código que trunca as tabelas e as repopula usando Fake

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# --- Definição dos Provedores Customizados ---
def truncate_tables(conn):
    cur = conn.cursor()
    try:
        # A ordem de truncamento é crucial devido às chaves estrangeiras.
        # Trunque as tabelas que dependem de outras primeiro.
        # E use RESTART IDENTITY para resetar os IDs seriais e CASCADE para dependências.
        print("Truncando tabelas existentes...")
        cur.execute("TRUNCATE TABLE pedidos_servico RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE prestador_servicos RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE adocao RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE itens_pedido RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE depoimentos RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE pedidos RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE prestadores RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE servicos RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE produtos RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE animal RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE usuarios RESTART IDENTITY CASCADE;")
        conn.commit()
        print("Tabelas truncadas com sucesso.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Erro ao truncar tabelas: {e}")

# Provedor de nomes de pets (masculino/feminino)
class PetProvider(BaseProvider):
    def pet_name_male(self):
        male_pet_names = [
            "Buddy", "Max", "Charlie", "Rocky", "Leo", "Duke", "Milo", "Jack", "Ollie", "Gus",
            "Bruno", "Lucky", "Toby", "Oscar", "Cooper", "Zeus", "Apollo", "Thor", "Rex", "Bart",
            "Scooby", "Bolt", "Simba", "Marley", "Bento", "Fred", "Bob", "Nico", "Dom", "Kiko",
            "Pixel", "Flash", "Caju", "Cookie", "Floyd", "Zeca", "Dudu", "Tobby", "Chico", "Gaspar",
            "Ace", "Baron", "Beau", "Bear", "Benny", "Boone", "Brooks", "Cody", "Diesel", "Dexter",
            "Finn", "Frankie", "George", "Harley", "Henry", "Hunter", "Jackson", "Jasper", "Kobe", "Koda",
            "Louie", "Maverick", "Moose", "Nash", "Nemo", "Otto", "Prince", "Ranger", "Remy", "River",
            "Rocco", "Roscoe", "Rusty", "Sam", "Scout", "Shadow", "Stanley", "Teddy", "Tucker", "Winston",
            "Bidu", "Totó", "Mingau", "Sansão", "Floquinho", "Bidú", "Cascão", "Cebolinha", "Chico Bento",
            "Pateta", "Pluto", "Dobby", "Yoda", "Baloo", "Chewie", "Pongo"
        ]
        return random.choice(male_pet_names)

    def pet_name_female(self):
        female_pet_names = [
            "Bella", "Lucy", "Luna", "Daisy", "Stella", "Zoe", "Ruby", "Sadie", "Mia", "Penny",
            "Sophie", "Nala", "Mel", "Jade", "Lola", "Maya", "Chloe", "Maggie", "Aurora", "Fiona",
            "Layla", "Frida", "Minnie", "Princesa", "Xuxa", "Pinky", "Sereia", "Sol", "Duda", "Kika",
            "Bela", "Amora", "Pipoca", "Cacau", "Fofinha", "Jujuba", "Dory", "Kiara", "Lua", "Flora",
            "Abby", "Annie", "Ava", "Bailey", "Bambi", "Bonnie", "Coco", "Delilah", "Dixie", "Ella",
            "Ellie", "Evie", "Freya", "Ginger", "Hazel", "Holly", "Honey", "Iris", "Ivy", "Jasmine",
            "Josie", "Lady", "Lexi", "Lily", "Maple", "Molly", "Nova", "Olive", "Phoebe", "Piper",
            "Princess", "Queenie", "Rosie", "Roxy", "Sage", "Sasha", "Sky", "Sugar", "Willow", "Winnie",
            "Perdita", "Leia", "Magali", "Mônica"
        ]
        return random.choice(female_pet_names)

    def pet_data(self):
        gender = random.choice(["macho", "femea"])
        name = self.pet_name_male() if gender == "macho" else self.pet_name_female()
        return {"name": name, "sexo": gender}

# --- Configuração do Faker ---
fake = Faker()
fake.add_provider(PetProvider)

# --- Configurações do Banco de Dados ---

import os
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

# --- Conexão com o Banco de Dados ---
def connect_db():
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
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


# --- Funções de Inserção de Dados ---

def insert_usuarios(conn, num_usuarios):
    cur = conn.cursor()
    usuarios_ids = []
    for _ in range(num_usuarios):
        nome = fake.name()
        email = fake.unique.email() # Usar fake.unique para evitar duplicatas
        senha = fake.password(length=12) # Senha não está hasheada (apenas para dados de teste, não usar em produção)
        telefone = fake.phone_number()
        endereco = fake.address()
        cidade = fake.city()
        estado = fake.state_abbr()
        is_admin = fake.boolean(chance_of_getting_true=2) # 2% de chance de ser admin
        data_cadastro = fake.date_time_between(start_date="-2y", end_date="now")

        cur.execute(
            """
            INSERT INTO usuarios (nome, email, senha, telefone, endereco, cidade, estado, is_admin, data_cadastro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_usuario;
            """,
            (nome, email, senha, telefone, endereco, cidade, estado, is_admin, data_cadastro)
        )
        usuarios_ids.append(cur.fetchone()[0])
    conn.commit()
    print(f"Inseridos {num_usuarios} usuários.")
    return usuarios_ids

def insert_animal(conn, num_animais):
    cur = conn.cursor()
    animal_ids = []
    portes = ['pequeno', 'medio', 'grande']
    tipos = ['cachorro', 'gato', 'outro']
    status_animais = ['disponivel', 'adotado', 'em_tratamento']

    for _ in range(num_animais):
        pet_info = fake.pet_data()
        nome = pet_info['name']
        sexo = pet_info['sexo']
        idade = random.randint(1, 15)
        porte = random.choice(portes)
        tipo = random.choice(tipos)
        descricao = fake.text(max_nb_chars=200)
        status = random.choice(status_animais)
        imagem = fake.image_url()
        data_entrada = fake.date_time_between(start_date="-1y", end_date="now")

        cur.execute(
            """
            INSERT INTO animal (nome, idade, porte, tipo, sexo, descricao, status, imagem, data_entrada)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_animal;
            """,
            (nome, idade, porte, tipo, sexo, descricao, status, imagem, data_entrada)
        )
        animal_ids.append(cur.fetchone()[0])
    conn.commit()
    print(f"Inseridos {num_animais} animais.")
    return animal_ids

def insert_adocao(conn, usuarios_ids, animal_ids, num_adocoes):
    cur = conn.cursor()
    status_adocao = ['pendente', 'aprovada', 'rejeitada']
    for _ in range(num_adocoes):
        id_usuario = random.choice(usuarios_ids)
        id_animal = random.choice(animal_ids)
        data_adocao = fake.date_time_between(start_date="-6m", end_date="now")
        status = random.choice(status_adocao)
        observacoes = fake.text(max_nb_chars=100) if fake.boolean(chance_of_getting_true=50) else None

        cur.execute(
            """
            INSERT INTO adocao (id_usuario, id_animal, data_adocao, status, observacoes)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (id_usuario, id_animal, data_adocao, status, observacoes)
        )
    conn.commit()
    print(f"Inseridas {num_adocoes} adoções.")

def insert_produtos(conn): # 'num_produtos' parameter removed
    cur = conn.cursor()
    produto_ids = []

    # Dicionário com categorias e termos complementares de produtos específicos para cada categoria
    category_product_suffixes = {
        'Alimentação': [
            'Ração Premium', 'Sachê Úmido', 'Bifinho', 'Osso Dental', 'Petisco Natural',
            'Crocante Frango', 'Granulado Peixe', 'Patê Gourmet', 'Alimento Úmido Carne',
            'Snack Saudável Vegetal', 'Farinha de Larva', 'Suplemento Nutricional',
            'Ração Hipoalergênica', 'Comida Congelada', 'Biscoito para Treino'
        ],
        'Brinquedos': [
            'Bola Interativa', 'Brinquedo de Corda', 'Arranhador Gato', 'Mordedor Resistente',
            'Laser Pointer', 'Pelúcia Squeaky', 'Frisbee Leve', 'Vara de Pesca para Gatos',
            'Rato de Brinquedo', 'Quebra-Cabeça Dispenser', 'Túnel Retrátil', 'Mola Elástica',
            'Brinquedo Térmico', 'Boneco de Vinil', 'Dispensador de Petiscos'
        ],
        'Higiene e Beleza': [
            'Shampoo Neutro', 'Condicionador Brilho', 'Escova para Pelos', 'Corta Unhas Ergonômico',
            'Lenço Umedecido Limpeza', 'Perfume Pet Suave', 'Sabonete Líquido Antialérgico',
            'Spray Desembaraçante', 'Luva Tira Pelos', 'Pente Fino Pulgas', 'Escova Dental Pet',
            'Creme Dental Enzimático', 'Odorizador de Ambientes', 'Removedor de Manchas Pet'
        ],
        'Acessórios': [
            'Coleira Ajustável', 'Peitoral Conforto', 'Guia Longa Durável', 'Identificação Tag Personalizada',
            'Bandana Estilosa', 'Gravata Borboleta Chic', 'Laço de Cabelo Fofo', 'Capa de Chuva Protetora',
            'Óculos de Sol Pet', 'Boné Pet Estiloso', 'Bandana de Festa', 'Meia Antiderrapante',
            'Protetor de Patas', 'Sapatinho de Borracha', 'Mochila de Passeio'
        ],
        'Saúde e Farmácia': [
            'Anti-Pulgas Oral', 'Vermífugo Amplo Espectro', 'Suplemento Vitamínico Imunidade',
            'Remédio para Dor', 'Protetor Solar Pet', 'Cicatrizante Tópico', 'Analgésico Gatos',
            'Antibiótico Oral', 'Pomada Cicatrizante Feridas', 'Spray Antisséptico',
            'Colírio para Olhos', 'Solução para Orelhas', 'Probiótico Intestinal',
            'Fita para Glicose', 'Termômetro Digital Pet'
        ],
        'Camas e Conforto': [
            'Caminha Macia Ortopédica', 'Colchonete Antialérgico', 'Casinha Plástica Externa',
            'Cobertor Quente Fleece', 'Nicho de Madeira Resistente', 'Toca Igloo Aconchegante',
            'Almofada Confortável', 'Tapete Gelado Refrescante', 'Rede Suspensa para Gatos',
            'Túnel Interativo', 'Edredom para Pet', 'Cama Suspensa Janela', 'Cobertor Elétrico'
        ],
        'Coleiras e Guias': [
            'Coleira de Couro Clássica', 'Guia Retrátil Automática', 'Peitoral H Ergonômico',
            'Coleira Anti-Puxão', 'Guia Unificada Treinamento', 'Coleira Luminosa LED',
            'Peitoral Antipuxão Conforto', 'Guia Flexível Ajustável', 'Coleira de Treinamento Elétrica',
            'Conjunto Coleira e Guia', 'Guia Dupla para 2 Cães'
        ],
        'Roupas e Moda': [
            'Roupa de Inverno Quente', 'Capa de Chuva Impermeável', 'Vestido Floral Verão',
            'Camiseta Divertida Estampada', 'Fantasia Temática Halloween', 'Sapatinho Protetor Anti-derrapante',
            'Meia Antiderrapante', 'Suéter de Lã Aconchegante', 'Jaqueta Corta Vento Esportiva',
            'Moletom com Capuz', 'Bota de Proteção', 'Gorro Temático'
        ],
        'Treinamento': [
            'Clicker de Adestramento', 'Apito de Treino Profissional', 'Tapete Olfativo Interativo',
            'Petisco de Recompensa Crocante', 'Bolsa para Petiscos Cinto', 'Brinquedo Dispenser Ração',
            'Cone de Agilidade', 'Guia de Treinamento Longa', 'Coleira de Adestramento Remoto',
            'Dispensador de Bolinhas', 'Livro de Treinamento Canino'
        ],
        'Transporte': [
            'Caixa de Transporte Ventilada', 'Bolsa de Passeio Confortável', 'Carrinho Pet Dobrável',
            'Cinto de Segurança Veicular', 'Cadeirinha de Carro Elevatória', 'Mochila de Transporte Transparente',
            'Rodas para Caixa de Transporte', 'Capas Protetoras de Carro', 'Assento Elevado para Cães',
            'Capa de Banco Traseiro', 'Rede de Proteção para Carro'
        ],
        'Comedouros e Bebedouros': [
            'Comedouro Lento Antigula', 'Bebedouro Automático Filtro', 'Fonte de Água Silenciosa',
            'Pote Duplo Inox Antiderrapante', 'Comedouro Elevado Ergonômico', 'Porta Ração Vedado',
            'Dispenser de Água Automático', 'Tigela Antiderrapante Cerâmica', 'Comedouro para Viagem',
            'Pote Dobrável Silicone', 'Bebedouro Portátil'
        ],
        'Limpeza do Ambiente': [
            'Tapete Higiênico Super Absorvente', 'Neutralizador de Odor Concentrado', 'Aspirador de Pelos Portátil',
            'Removedor de Manchas Enzimático', 'Desinfetante Pet Friendly', 'Pá Sanitária com Peneira',
            'Saco para Dejetos Biodegradável', 'Cata Caca com Refil', 'Spray Limpa Xixi',
            'Eliminador de Odores', 'Limpador de Estofados Pet'
        ]
    }

    produtos_data = [] # Data for batch insertion

    for categoria, sufixos_produtos in category_product_suffixes.items():
        for complemento_nome in sufixos_produtos:
            nome = fake.unique.word().capitalize() + " " + complemento_nome
            preco = Decimal(random.uniform(10.00, 500.00)).quantize(Decimal('0.01'))
            descricao = fake.text(max_nb_chars=150)
            estoque = random.randint(0, 700)
            imagem = fake.image_url()
            destaque = fake.boolean(chance_of_getting_true=20)
            
            produtos_data.append((nome, preco, descricao, categoria, estoque, imagem, destaque))

    if produtos_data:
        placeholders = ', '.join(['%s'] * len(produtos_data[0]))
        insert_query = f"""
            INSERT INTO produtos (nome, preco, descricao, categoria, estoque, imagem, destaque)
            VALUES {', '.join([f'({placeholders})' for _ in produtos_data])}
            RETURNING id_produto;
        """
        flattened_values = tuple(item for sublist in produtos_data for item in sublist)
        try:
            cur.execute(insert_query, flattened_values)
            produto_ids = [row[0] for row in cur.fetchall()]
        except psycopg2.IntegrityError as e:
            conn.rollback()
            print(f"Erro de integridade no banco de dados ao inserir produtos em lote: {e}")
            produto_ids = []
            for p_data in produtos_data:
                try:
                    cur.execute(
                        """
                        INSERT INTO produtos (nome, preco, descricao, categoria, estoque, imagem, destaque)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_produto;
                        """,
                        p_data
                    )
                    produto_ids.append(cur.fetchone()[0])
                except psycopg2.IntegrityError as individual_e:
                    conn.rollback() 
                    print(f"Pulando produto com erro: {p_data[0]} - {individual_e}")
                    continue
    else:
        produto_ids = []

    conn.commit()
    print(f"Inseridos {len(produto_ids)} produtos.")
    return produto_ids

def insert_pedidos(conn, usuarios_ids, num_pedidos):
    cur = conn.cursor()
    pedido_ids = []
    status_pedido_compras = ['pendente', 'pago', 'enviado', 'entregue', 'cancelado']
    for _ in range(num_pedidos):
        id_usuario = random.choice(usuarios_ids)
        data_pedido = fake.date_time_between(start_date="-3m", end_date="now")
        valor_total = Decimal(random.uniform(50.00, 1000.00)).quantize(Decimal('0.01'))
        status = random.choice(status_pedido_compras)

        cur.execute(
            """
            INSERT INTO pedidos (id_usuario, data_pedido, valor_total, status)
            VALUES (%s, %s, %s, %s) RETURNING id_pedido;
            """,
            (id_usuario, data_pedido, valor_total, status)
        )
        pedido_ids.append(cur.fetchone()[0])
    conn.commit()
    print(f"Inseridos {num_pedidos} pedidos de compra.")
    return pedido_ids

def insert_itens_pedido(conn, pedido_ids, produto_ids, num_itens_por_pedido=3):
    cur = conn.cursor()
    for pedido_id in pedido_ids:
        produtos_do_pedido = random.sample(produto_ids, min(num_itens_por_pedido, len(produto_ids)))
        for produto_id in produtos_do_pedido:
            quantidade = random.randint(1, 5)
            cur.execute("SELECT preco FROM produtos WHERE id_produto = %s;", (produto_id,))
            preco_unitario = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO itens_pedido (id_pedido, id_produto, quantidade, preco_unitario)
                VALUES (%s, %s, %s, %s);
                """,
                (pedido_id, produto_id, quantidade, preco_unitario)
            )
    conn.commit()
    print(f"Inseridos itens para {len(pedido_ids)} pedidos.")

def insert_depoimentos(conn, usuarios_ids, animal_ids, num_depoimentos):
    cur = conn.cursor()
    for _ in range(num_depoimentos):
        id_usuario = random.choice(usuarios_ids)
        id_animal = random.choice(animal_ids)
        texto = fake.paragraph(nb_sentences=3)
        aprovado = fake.boolean(chance_of_getting_true=80)
        data_depoimento = fake.date_time_between(start_date="-6m", end_date="now")

        cur.execute(
            """
            INSERT INTO depoimentos (id_usuario, id_animal, texto, aprovado, data_depoimento)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (id_usuario, id_animal, texto, aprovado, data_depoimento)
        )
    conn.commit()
    print(f"Inseridos {num_depoimentos} depoimentos.")

def insert_servicos(conn): 
    cur = conn.cursor()
    servico_ids = []

    servicos_definidos = {
        'Estética e Higiene': [
            {"nome": "Banho Completo", "preco_base": 80.00, "duracao_minutos": 90},
            {"nome": "Tosa Higiênica", "preco_base": 70.00, "duracao_minutos": 60},
            {"nome": "Tosa na Tesoura", "preco_base": 120.00, "duracao_minutos": 120},
            {"nome": "Hidratação de Pelos", "preco_base": 60.00, "duracao_minutos": 45},
            {"nome": "Corte de Unhas", "preco_base": 30.00, "duracao_minutos": 20},
            {"nome": "Limpeza de Ouvidos", "preco_base": 25.00, "duracao_minutos": 15},
            {"nome": "Escovação de Dentes", "preco_base": 40.00, "duracao_minutos": 30},
            {"nome": "Remoção de Sub-pelo", "preco_base": 90.00, "duracao_minutos": 75}
        ],
        'Saúde e Bem-Estar': [
            {"nome": "Consulta Veterinária Geral", "preco_base": 150.00, "duracao_minutos": 60},
            {"nome": "Vacinação (V8/V10)", "preco_base": 100.00, "duracao_minutos": 30},
            {"nome": "Vacinação Antirrábica", "preco_base": 80.00, "duracao_minutos": 20},
            {"nome": "Microchipagem", "preco_base": 200.00, "duracao_minutos": 30},
            {"nome": "Exames Laboratoriais (Básico)", "preco_base": 250.00, "duracao_minutos": 45},
            {"nome": "Vermifugação", "preco_base": 50.00, "duracao_minutos": 15},
            {"nome": "Aplicação de Medicamentos", "preco_base": 60.00, "duracao_minutos": 20},
            {"nome": "Revisão Pós-operatória", "preco_base": 120.00, "duracao_minutos": 45}
        ],
        'Cuidado e Passeio': [
            {"nome": "Passeio de Cães (30min)", "preco_base": 40.00, "duracao_minutos": 30},
            {"nome": "Passeio de Cães (60min)", "preco_base": 70.00, "duracao_minutos": 60},
            {"nome": "Pet Sitter Diário", "preco_base": 100.00, "duracao_minutos": 120},
            {"nome": "Creche Diária", "preco_base": 80.00, "duracao_minutos": 480}, # 8 horas
            {"nome": "Hospedagem Noturna", "preco_base": 150.00, "duracao_minutos": 1440}, # 24 horas
            {"nome": "Transporte de Pet (Local)", "preco_base": 90.00, "duracao_minutos": 60},
            {"nome": "Taxi Dog", "preco_base": 80.00, "duracao_minutos": 60}
        ],
        'Adestramento e Comportamento': [
            {"nome": "Adestramento Básico Individual", "preco_base": 250.00, "duracao_minutos": 90},
            {"nome": "Adestramento Avançado (pacote)", "preco_base": 800.00, "duracao_minutos": 360}, # 6 horas total
            {"nome": "Consulta Comportamental", "preco_base": 300.00, "duracao_minutos": 120},
            {"nome": "Socialização de Filhotes", "preco_base": 180.00, "duracao_minutos": 90}
        ],
        'Serviços Especiais': [
            {"nome": "Fisioterapia Animal", "preco_base": 200.00, "duracao_minutos": 60},
            {"nome": "Acupuntura Veterinária", "preco_base": 180.00, "duracao_minutos": 60},
            {"nome": "Ozonioterapia", "preco_base": 150.00, "duracao_minutos": 45},
            {"nome": "Terapia Comportamental", "preco_base": 220.00, "duracao_minutos": 90}
        ]
    }

    servicos_data = []

    for categoria_servico, lista_servicos in servicos_definidos.items():
        for servico_info in lista_servicos:
            nome = servico_info["nome"]
            descricao = fake.sentence(nb_words=10, variable_nb_words=True)
            preco_base = Decimal(servico_info["preco_base"]).quantize(Decimal('0.01'))
            duracao_minutos = servico_info["duracao_minutos"]
            ativo = fake.boolean(chance_of_getting_true=90)
            criado_em = fake.date_time_between(start_date="-1y", end_date="now")
            categoria = categoria_servico.lower()
            servicos_data.append((nome, descricao, preco_base, duracao_minutos, ativo, criado_em, categoria))

    if servicos_data:
        placeholders = ', '.join(['%s'] * len(servicos_data[0]))
        insert_query = f"""
            INSERT INTO servicos (nome, descricao, preco_base, duracao_minutos, ativo, criado_em, categoria)
            VALUES {', '.join([f'({placeholders})' for _ in servicos_data])}
            RETURNING id_servico;
        """
        flattened_values = tuple(item for sublist in servicos_data for item in sublist)
        
        try:
            cur.execute(insert_query, flattened_values)
            servico_ids = [row[0] for row in cur.fetchall()]
        except psycopg2.IntegrityError as e:
            conn.rollback()
            print(f"Erro de integridade no banco de dados ao inserir serviços em lote: {e}")
            servico_ids = []
            for s_data in servicos_data:
                try:
                    cur.execute(
                        """
                        INSERT INTO servicos (nome, descricao, preco_base, duracao_minutos, ativo, criado_em, categoria)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_servico;
                        """,
                        s_data
                    )
                    servico_ids.append(cur.fetchone()[0])
                except psycopg2.IntegrityError as individual_e:
                    conn.rollback()
                    print(f"Pulando serviço com erro: {s_data[0]} - {individual_e}")
                    continue
    else:
        servico_ids = []

    conn.commit()
    print(f"Inseridos {len(servico_ids)} serviços.")
    return servico_ids

def insert_prestadores(conn, usuarios_ids, num_prestadores):
    cur = conn.cursor()
    prestador_ids = []
    for _ in range(num_prestadores):
        id_usuario = random.choice(usuarios_ids)
        nome_completo = fake.name()
        bio = fake.paragraph(nb_sentences=2)
        telefone = fake.phone_number()
        cidade = fake.city()
        estado = fake.state_abbr()
        avaliacao_media = Decimal(random.uniform(3.0, 5.0)).quantize(Decimal('0.1'))
        verificado = fake.boolean(chance_of_getting_true=70)
        criado_em = fake.date_time_between(start_date="-1y", end_date="now")

        cur.execute(
            """
            INSERT INTO prestadores (id_usuario, nome_completo, bio, telefone, cidade, estado, avaliacao_media, verificado, criado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_prestador;
            """,
            (id_usuario, nome_completo, bio, telefone, cidade, estado, avaliacao_media, verificado, criado_em)
        )
        prestador_ids.append(cur.fetchone()[0])
    conn.commit()
    print(f"Inseridos {num_prestadores} prestadores.")
    return prestador_ids

def insert_prestador_servicos(conn, prestador_ids, servico_ids, num_associacoes):
    cur = conn.cursor()
    prestador_servico_ids = []
    added_associations = set()

    while len(prestador_servico_ids) < num_associacoes:
        try:
            id_prestador = random.choice(prestador_ids)
            id_servico = random.choice(servico_ids)

            if (id_prestador, id_servico) in added_associations:
                continue

            preco = Decimal(random.uniform(50.00, 500.00)).quantize(Decimal('0.01'))
            raio_atendimento_km = random.randint(5, 50)
            tempo_estimado_min = random.choice([30, 60, 90, 120, 180])
            ativo = fake.boolean(chance_of_getting_true=95)

            cur.execute(
                """
                INSERT INTO prestador_servicos (id_prestador, id_servico, preco, raio_atendimento_km, tempo_estimado_min, ativo)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_prestador_serv;
                """,
                (id_prestador, id_servico, preco, raio_atendimento_km, tempo_estimado_min, ativo)
            )
            prestador_servico_ids.append(cur.fetchone()[0])
            added_associations.add((id_prestador, id_servico))
        except IntegrityError as e:
            conn.rollback() 
            print(f"Tentativa de inserir duplicata em prestador_servicos, ignorando: {e}")
            continue
    conn.commit()
    print(f"Inseridas {len(prestador_servico_ids)} associações prestador-serviço.")
    return prestador_servico_ids


from datetime import timedelta

def insert_pedidos_servico(conn, animal_ids, prestador_servico_ids, usuarios_ids, num_pedidos_servico):
    cur = conn.cursor()
    status_pedido_servico = ['pendente', 'confirmado', 'concluido', 'cancelado']
    for _ in range(num_pedidos_servico):
        id_animal = random.choice(animal_ids)
        id_prestador_serv = random.choice(prestador_servico_ids)
        id_tutor = random.choice(usuarios_ids)
        inicio = fake.date_time_between(start_date="now", end_date="+3m")
        fim = inicio + random.choice([timedelta(hours=1), timedelta(hours=2), timedelta(hours=3)])
        status = random.choice(status_pedido_servico)
        observacoes = fake.text(max_nb_chars=100) if fake.boolean(chance_of_getting_true=50) else None
        criado_em = fake.date_time_between(start_date="-1m", end_date="now")


        cur.execute(
            """
            INSERT INTO pedidos_servico (id_animal, id_prestador_serv, id_tutor, inicio, fim, status, observacoes, criado_em)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (id_animal, id_prestador_serv, id_tutor, inicio, fim, status, observacoes, criado_em)
        )
    conn.commit()
    print(f"Inseridos {num_pedidos_servico} pedidos de serviço.")

# --- Função Principal de População ---
def populate_all_tables(truncate=False):
    conn = connect_db()
    if truncate:
        print("Limpando tabelas antes da população...")
        truncate_tables(conn)
        
    if conn:
        try:
            print("Iniciando a população do banco de dados...")

            # Número de registros a serem gerados
            num_usuarios = 750
            num_animais = 1000
            num_produtos = 500
            num_servicos = 400
            num_prestadores = 200

            # 1. Popula usuários
            usuarios_ids = insert_usuarios(conn, num_usuarios)

            # 2. Popula animais
            animal_ids = insert_animal(conn, num_animais)

            # 3. Popula adoções (depende de usuários e animais)
            num_adocoes = random.randint(int(num_animais * 0.3), int(num_animais * 0.7))
            insert_adocao(conn, usuarios_ids, animal_ids, num_adocoes)

            # 4. Popula produtos
            produto_ids = insert_produtos(conn)

            # 5. Popula pedidos (de produtos)
            num_pedidos_compras = random.randint(int(num_usuarios * 0.5), int(num_usuarios * 1.5))
            pedido_ids = insert_pedidos(conn, usuarios_ids, num_pedidos_compras)

            # 6. Popula itens de pedido (depende de pedidos e produtos)
            if pedido_ids and produto_ids:
                insert_itens_pedido(conn, pedido_ids, produto_ids, num_itens_por_pedido=random.randint(1, 5))
            else:
                print("Sem pedidos ou produtos para inserir itens de pedido.")

            # 7. Popula depoimentos (depende de usuários e animais)
            num_depoimentos = random.randint(int(num_animais * 0.2), int(num_animais * 0.5))
            insert_depoimentos(conn, usuarios_ids, animal_ids, num_depoimentos)

            # 8. Popula serviços
            servico_ids = insert_servicos(conn)

            # 9. Popula prestadores (depende de usuários)
            prestador_ids = insert_prestadores(conn, usuarios_ids, num_prestadores)

            # 10. Popula prestador_servicos (N:N entre prestadores e serviços)
            num_associacoes = random.randint(num_prestadores * 1, num_prestadores * 4)
            if prestador_ids and servico_ids:
                prestador_servico_ids = insert_prestador_servicos(conn, prestador_ids, servico_ids, num_associacoes)
            else:
                prestador_servico_ids = []
                print("Sem prestadores ou serviços para inserir associações.")

            # 11. Popula pedidos_servico (agendamentos)
            num_pedidos_servico = random.randint(int(num_usuarios * 0.5), int(num_usuarios * 1.0))
            if animal_ids and prestador_servico_ids and usuarios_ids:
                insert_pedidos_servico(conn, animal_ids, prestador_servico_ids, usuarios_ids, num_pedidos_servico)
            else:
                print("Sem animais, prestadores_servico ou usuários para inserir pedidos de serviço.")


            print("\nPopulação do banco de dados concluída com sucesso!")

        except psycopg2.Error as e:
            conn.rollback() # Em caso de erro, desfaz todas as operações
            print(f"Erro durante a população do banco de dados: {e}")
        finally:
            conn.close()
            print("Conexão com o banco de dados fechada.")
    else:
        print("Não foi possível estabelecer conexão com o banco de dados.")

# --- Execução ---
if __name__ == "__main__":
    populate_all_tables(truncate=True)