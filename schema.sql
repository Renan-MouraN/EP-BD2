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

--
-- Definição das Views
--

-- Lista os produtos comprados apenas por usuários que adotaram algum animal
CREATE OR REPLACE VIEW vw_produtos_comprados_por_adotantes AS
WITH UsuariosAdotantesComData AS (
    -- Para cada usuário que adotou, encontra a data da sua primeira adoção
    SELECT
        id_usuario,
        MIN(data_adocao) AS primeira_data_adocao
    FROM
        adocao
    GROUP BY
        id_usuario
)
SELECT
    u.id_usuario,
    u.nome AS nome_usuario,
    ua.primeira_data_adocao, -- Data da primeira adoção do usuário
    p.id_pedido,
    p.data_pedido,
    prod.nome AS nome_produto,
    ip.quantidade,
    ip.preco_unitario,
    (ip.quantidade * ip.preco_unitario) AS valor_total_item
FROM
    usuarios u
JOIN
    UsuariosAdotantesComData ua ON u.id_usuario = ua.id_usuario -- Garante que o usuário é um adotante e traz a data da primeira adoção
JOIN
    pedidos p ON u.id_usuario = p.id_usuario
JOIN
    itens_pedido ip ON p.id_pedido = ip.id_pedido
JOIN
    produtos prod ON ip.id_produto = prod.id_produto
ORDER BY
    u.nome, p.data_pedido, prod.nome;

-- Lista adoções com status 'pendente', incluindo o nome do usuário e do animal.
CREATE OR REPLACE VIEW vw_adocoes_pend AS
SELECT
    ad.id_adocao,
    u.nome AS nome_usuario,
    a.nome AS nome_animal,
    ad.data_adocao,
    ad.observacoes
FROM
    adocao ad
JOIN
    usuarios u ON ad.id_usuario = u.id_usuario
JOIN
    animal a ON ad.id_animal = a.id_animal
WHERE
    ad.status = 'pendente';

-- Exibe produtos que estão marcados como destaque e que possuem estoque disponível.
CREATE OR REPLACE VIEW vw_produtos_em_destaque_c_estoque AS
SELECT
    id_produto,
    nome,
    preco,
    descricao,
    categoria,
    estoque,
    imagem
FROM
    produtos
WHERE
    destaque = TRUE AND estoque > 0;

-- Detalha cada item dentro de cada pedido de e-commerce, incluindo o nome do usuário e do produto.
CREATE OR REPLACE VIEW vw_pedidos_ecommerce AS
SELECT
    p.id_pedido,
    u.nome AS nome_usuario,
    p.data_pedido,
    p.valor_total,
    p.status AS status_pedido,
    ip.quantidade,
    ip.preco_unitario,
    prod.nome AS nome_produto,
    prod.categoria AS categoria_produto
FROM
    pedidos p
JOIN
    usuarios u ON p.id_usuario = u.id_usuario
JOIN
    itens_pedido ip ON p.id_pedido = ip.id_pedido
JOIN
    produtos prod ON ip.id_produto = prod.id_produto;

-- Lista os serviços que estão ativos e que são oferecidos por prestadores
CREATE OR REPLACE VIEW vw_servicos_ativos_prestador AS
SELECT
    s.id_servico,
    s.nome AS nome_servico,
    s.descricao AS descricao_servico,
    s.preco_base,
    s.duracao_minutos,
    s.categoria,
    ps.preco AS preco_oferecido_prestador,
    ps.raio_atendimento_km,
    ps.tempo_estimado_min,
    pr.nome_completo AS nome_prestador,
    pr.avaliacao_media,
    pr.cidade AS cidade_prestador,
    pr.estado AS estado_prestador,
    pr.verificado AS prestador_verificado
FROM
    servicos s
JOIN
    prestador_servicos ps ON s.id_servico = ps.id_servico
JOIN
    prestadores pr ON ps.id_prestador = pr.id_prestador
WHERE
    s.ativo = TRUE AND ps.ativo = TRUE;

-- visão sobre agendamentos de serviço, incluindo nomes do animal, tutor, prestador e serviço.
CREATE OR REPLACE VIEW vw_agendamentos_servicos AS
SELECT
    pos.id_pedido_servico,
    an.nome AS nome_animal,
    u.nome AS nome_tutor,
    pr.nome_completo AS nome_prestador,
    s.nome AS nome_servico,
    pos.inicio,
    pos.fim,
    pos.status AS status_agendamento,
    pos.observacoes,
    pos.criado_em AS data_agendamento
FROM
    pedidos_servico pos
JOIN
    animal an ON pos.id_animal = an.id_animal
JOIN
    usuarios u ON pos.id_tutor = u.id_usuario
JOIN
    prestador_servicos p_s ON pos.id_prestador_serv = p_s.id_prestador_serv
JOIN
    prestadores pr ON p_s.id_prestador = pr.id_prestador
JOIN
    servicos s ON p_s.id_servico = s.id_servico;

-- Mostra a quantidade de adoções, produtos comprados, valor total de compras e serviços solicitados por usuário.
CREATE OR REPLACE VIEW vw_resumo_usrs AS
SELECT
    u.id_usuario,
    u.nome AS nome_usuario,
    COUNT(DISTINCT ad.id_adocao) AS total_adocoes,
    COALESCE(SUM(ip.quantidade), 0) AS total_produtos_comprados,
    COALESCE(SUM(ip.quantidade * ip.preco_unitario), 0.00) AS valor_total_compras,
    COUNT(DISTINCT ps.id_pedido_servico) AS total_servicos_solicitados
FROM
    usuarios u
LEFT JOIN
    adocao ad ON u.id_usuario = ad.id_usuario
LEFT JOIN
    pedidos p ON u.id_usuario = p.id_usuario
LEFT JOIN
    itens_pedido ip ON p.id_pedido = ip.id_pedido
LEFT JOIN
    pedidos_servico ps ON u.id_usuario = ps.id_tutor
GROUP BY
    u.id_usuario, u.nome
ORDER BY
    u.nome;
