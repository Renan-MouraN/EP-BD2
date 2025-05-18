-- Criação do banco de dados
CREATE DATABASE petmatch;

-- Conectando ao banco de dados
\c petmatch

-- Tabela de usuários
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(100) NOT NULL,
    telefone VARCHAR(20),
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

-- Inserindo dados iniciais para teste

-- Administrador padrão
INSERT INTO usuarios (nome, email, senha, is_admin) 
VALUES ('Administrador', 'admin@patacerta.com', 'admin123', TRUE);

-- Alguns animais para teste
INSERT INTO animal (nome, idade, porte, tipo, sexo, descricao, status, imagem) VALUES
('Tobby', 2, 'medio', 'cachorro', 'macho', 'Tobby é brincalhão, adora crianças e é muito obediente. Ótimo para famílias!', 'disponivel', 'uploads/tobby.jpg'),
('Luna', 1, 'pequeno', 'gato', 'femea', 'Luna é dócil, calma e adora carinho. Perfeita para apartamentos!', 'disponivel', 'uploads/luna.jpg'),
('Max', 5, 'grande', 'cachorro', 'macho', 'Max é um cão-guia aposentado que precisa de um lar tranquilo e amoroso urgentemente.', 'disponivel', 'uploads/max.jpg'),
('Nina', 3, 'pequeno', 'gato', 'femea', 'Nina é independente, mas muito carinhosa quando quer. Perfeita para quem trabalha fora.', 'disponivel', 'uploads/nina.jpg');

-- Alguns produtos para teste
INSERT INTO produtos (nome, preco, descricao, categoria, estoque, imagem, destaque) VALUES
('Ração Premium para Gatos', 89.90, 'Ração de alta qualidade para gatos adultos. Embalagem de 3kg.', 'Alimentos', 50, 'uploads/racao-gato.jpg', TRUE),
('Coleira Ajustável', 34.50, 'Coleira ajustável para cães de pequeno e médio porte. Material resistente e confortável.', 'Acessórios', 30, 'uploads/coleira.jpg', TRUE),
('Cama para Pets', 120.00, 'Cama confortável para cães e gatos. Tamanho médio, lavável e anti-ácaros.', 'Camas', 15, 'uploads/cama-pet.jpg', TRUE),
('Brinquedo Interativo', 45.90, 'Brinquedo interativo para estimular a mente do seu pet. Ideal para cães de todas as idades.', 'Brinquedos', 25, 'uploads/brinquedo.jpg', TRUE);
