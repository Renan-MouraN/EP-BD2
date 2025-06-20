-- Criação do banco de dados
CREATE DATABASE petmatch;

-- Conectando ao banco de dados
\c petmatch

-- Tabela de usuários
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL, -- UNIQUE em email já cria um índice implícito
    senha VARCHAR(100) NOT NULL,
    telefone VARCHAR(50),
    endereco TEXT,
    cidade VARCHAR(50),
    estado CHAR(2),
    is_admin BOOLEAN DEFAULT FALSE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para a tabela usuarios
CREATE INDEX idx_usuarios_cidade_estado ON usuarios (cidade, estado);
CREATE INDEX idx_usuarios_is_admin ON usuarios (is_admin);


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

-- Índices para a tabela animal
CREATE INDEX idx_animal_status ON animal (status);
CREATE INDEX idx_animal_tipo ON animal (tipo);
CREATE INDEX idx_animal_porte ON animal (porte);
CREATE INDEX idx_animal_data_entrada ON animal (data_entrada);


-- Tabela de adoções
CREATE TABLE adocao (
    id_adocao SERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuarios(id_usuario),
    id_animal INT REFERENCES animal(id_animal),
    data_adocao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'aprovada', 'rejeitada')),
    observacoes TEXT
);

-- Índices para a tabela adocao
CREATE INDEX idx_adocao_status ON adocao (status);
CREATE INDEX idx_adocao_data_adocao ON adocao (data_adocao);
CREATE INDEX idx_adocao_id_usuario ON adocao (id_usuario);
CREATE INDEX idx_adocao_id_animal ON adocao (id_animal);


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

-- Índices para a tabela pedidos
CREATE INDEX idx_pedidos_id_usuario ON pedidos (id_usuario);
CREATE INDEX idx_pedidos_status ON pedidos (status);
CREATE INDEX idx_pedidos_data_pedido ON pedidos (data_pedido);


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

-- Índices para a tabela depoimentos
CREATE INDEX idx_depoimentos_id_usuario ON depoimentos (id_usuario);
CREATE INDEX idx_depoimentos_id_animal ON depoimentos (id_animal);
CREATE INDEX idx_depoimentos_aprovado ON depoimentos (aprovado);
CREATE INDEX idx_depoimentos_data_depoimento ON depoimentos (data_depoimento);


/* ---------- 1. Catálogo de serviços ---------- */
CREATE TABLE servicos (
    id_servico          SERIAL PRIMARY KEY,
    nome                TEXT        NOT NULL,
    descricao           TEXT,
    preco_base          NUMERIC(10,2),
    duracao_minutos     INTEGER,
    ativo               BOOLEAN     DEFAULT TRUE,
    criado_em           TIMESTAMP   DEFAULT NOW(),
    categoria           VARCHAR(50)
);


/* ---------- 2. Prestadores de serviço ---------- */
CREATE TABLE prestadores (
    id_prestador        SERIAL PRIMARY KEY,
    id_usuario          INTEGER     REFERENCES usuarios(id_usuario),
    nome_completo       TEXT        NOT NULL,
    bio                 TEXT,
    telefone            TEXT,
    cidade              TEXT,
    estado              CHAR(2),
    avaliacao_media     NUMERIC(2,1),
    verificado          BOOLEAN     DEFAULT FALSE,
    criado_em           TIMESTAMP   DEFAULT NOW()
);

-- Índices para a tabela prestadores
CREATE INDEX idx_prestadores_cidade_estado ON prestadores (cidade, estado);
CREATE INDEX idx_prestadores_verificado ON prestadores (verificado);
CREATE INDEX idx_prestadores_id_usuario ON prestadores (id_usuario);


/* ---------- 3. Relação Prestador × Serviço (N:N) ---------- */
CREATE TABLE prestador_servicos (
    id_prestador_serv SERIAL PRIMARY KEY,
    id_prestador      INTEGER REFERENCES prestadores(id_prestador)   ON DELETE CASCADE,
    id_servico        INTEGER REFERENCES servicos(id_servico)        ON DELETE CASCADE,
    preco             NUMERIC(10,2),
    raio_atendimento_km INTEGER,
    tempo_estimado_min INTEGER,
    ativo             BOOLEAN     DEFAULT TRUE,
    UNIQUE (id_prestador, id_servico) -- UNIQUE já cria um índice implícito
);

-- Índices para a tabela prestador_servicos
CREATE INDEX idx_prestador_servicos_ativo ON prestador_servicos (ativo);


/* ---------- 4. Pedidos / agendamentos de serviço ---------- */
CREATE TYPE status_pedido AS ENUM ('pendente','confirmado','concluido','cancelado');

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

-- Índices para a tabela pedidos_servico
CREATE INDEX idx_pedidos_servico_id_tutor ON pedidos_servico (id_tutor);
CREATE INDEX idx_pedidos_servico_id_prestador_serv ON pedidos_servico (id_prestador_serv);
CREATE INDEX idx_pedidos_servico_status ON pedidos_servico (status);
CREATE INDEX idx_pedidos_servico_inicio ON pedidos_servico (inicio);