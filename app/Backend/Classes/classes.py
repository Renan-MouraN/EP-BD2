from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Numeric, TIMESTAMP, Enum, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional

# --- SQLAlchemy Models (Database Table Definitions) ---
Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha = Column(String(100), nullable=False)
    telefone = Column(String(20))
    endereco = Column(Text)
    cidade = Column(String(50))
    estado = Column(String(2))
    is_admin = Column(Boolean, default=False)
    data_cadastro = Column(TIMESTAMP, default=datetime.now)

class Animal(Base):
    __tablename__ = "animal"
    id_animal = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    idade = Column(Integer)
    porte = Column(String(20))
    tipo = Column(String(20))
    sexo = Column(String(10))
    descricao = Column(Text)
    status = Column(String(20), default='disponivel')
    imagem = Column(String(255))
    data_entrada = Column(TIMESTAMP, default=datetime.now)

    __table_args__ = (
        CheckConstraint("porte IN ('pequeno', 'medio', 'grande')", name='chk_animal_porte'),
        CheckConstraint("tipo IN ('cachorro', 'gato', 'outro')", name='chk_animal_tipo'),
        CheckConstraint("sexo IN ('macho', 'femea')", name='chk_animal_sexo'),
        CheckConstraint("status IN ('disponivel', 'adotado', 'em_tratamento')", name='chk_animal_status'),
    )

class Adocao(Base):
    __tablename__ = "adocao"
    id_adocao = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, index=True)
    id_animal = Column(Integer, index=True)
    data_adocao = Column(TIMESTAMP, default=datetime.now)
    status = Column(String(20), default='pendente')
    observacoes = Column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('pendente', 'aprovada', 'rejeitada')", name='chk_adocao_status'),
    )

class Produto(Base):
    # CORREÇÃO 1: O nome da tabela foi alterado para 'produtos' (plural) para corresponder ao schema.sql.
    __tablename__ = "produtos"
    id_produto = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    preco = Column(Numeric(10, 2), nullable=False)
    # CORREÇÃO 2: O nome da coluna foi alterado para 'estoque' para corresponder ao schema.sql.
    estoque = Column(Integer, default=0)
    categoria = Column(String(50))
    imagem = Column(String(255))

class Pedido(Base):
    # CORREÇÃO: O nome da tabela foi alterado para 'pedidos' (plural) para corresponder ao schema.sql.
    __tablename__ = "pedidos"
    id_pedido = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, index=True)
    data_pedido = Column(TIMESTAMP, default=datetime.now)
    status = Column(String(20), default='pendente') # 'pendente', 'pago', 'cancelado', 'enviado', 'entregue'
    valor_total = Column(Numeric(10, 2))

    __table_args__ = (
        CheckConstraint("status IN ('pendente', 'pago', 'cancelado', 'enviado', 'entregue')", name='chk_pedido_status'),
    )

class ItemPedido(Base):
    # CORREÇÃO: O nome da tabela foi alterado para 'itens_pedido' (plural) para corresponder ao schema.sql.
    __tablename__ = "itens_pedido"
    id_item = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, index=True)
    id_produto = Column(Integer, index=True)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

class Depoimento(Base):
    # CORREÇÃO: O nome da tabela foi alterado para 'depoimentos' (plural) para corresponder ao schema.sql.
    __tablename__ = "depoimentos"
    id_depoimento = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, index=True)
    id_animal = Column(Integer, index=True)
    texto = Column(Text, nullable=False)
    data_depoimento = Column(TIMESTAMP, default=datetime.now)
    aprovado = Column(Boolean, default=False)

class Servico(Base):
    # CORREÇÃO: O nome da tabela foi alterado para 'servicos' (plural) para corresponder ao schema.sql.
    __tablename__ = "servicos"
    id_servico = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    preco_base = Column("preco_base", Numeric(10, 2))
    duracao_minutos = Column("duracao_minutos", Integer)


class Prestador(Base):
    # CORREÇÃO: O nome da tabela foi alterado para 'prestadores' (plural) para corresponder ao schema.sql.
    __tablename__ = "prestadores"
    id_prestador = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(100), nullable=False)
    especialidade = Column(String(100))
    telefone = Column(String(20))
    email = Column(String(100))
    id_usuario = Column(Integer, index=True, nullable=True) 

class PrestadorServico(Base):
    # CORREÇÃO: O nome da tabela foi alterado para 'prestador_servicos' (plural) para corresponder ao schema.sql.
    __tablename__ = "prestador_servicos"
    id_prestador_serv = Column(Integer, primary_key=True, index=True)
    id_prestador = Column(Integer, index=True)
    id_servico = Column(Integer, index=True)
    preco = Column("preco", Numeric(10, 2))

class PedidoServico(Base):
    # CORREÇÃO: O nome da tabela foi alterado para 'pedidos_servico' (plural) para corresponder ao schema.sql.
    __tablename__ = "pedidos_servico"
    id_pedido_servico = Column(Integer, primary_key=True, index=True)
    id_animal = Column(Integer, index=True)
    id_prestador_serv = Column(Integer, index=True)
    id_tutor = Column(Integer, index=True)
    inicio = Column("inicio", TIMESTAMP, nullable=False)
    status = Column(String(20), default='pendente')
    observacoes = Column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('pendente', 'confirmado', 'concluido', 'cancelado')", name='chk_pedido_servico_status'),
    )

# --- Pydantic Models (for API Request/Response) ---

class UsuarioBase(BaseModel):
    nome: str
    email: str
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    senha: str
    is_admin: bool = False

class UsuarioUpdate(UsuarioBase):
    nome: Optional[str] = None
    email: Optional[str] = None
    senha: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    is_admin: Optional[bool] = None

class UsuarioInDB(UsuarioBase):
    id_usuario: int
    is_admin: bool
    data_cadastro: datetime

    class Config:
        from_attributes = True

class AnimalBase(BaseModel):
    nome: str
    idade: Optional[int] = None
    porte: Optional[str] = None
    tipo: Optional[str] = None
    sexo: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[str] = 'disponivel'
    imagem: Optional[str] = None

class AnimalCreate(AnimalBase):
    pass

class AnimalUpdate(AnimalBase):
    nome: Optional[str] = None
    idade: Optional[int] = None
    porte: Optional[str] = None
    tipo: Optional[str] = None
    sexo: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[str] = None
    imagem: Optional[str] = None

class AnimalInDB(AnimalBase):
    id_animal: int
    data_entrada: datetime

    class Config:
        from_attributes = True

class AdocaoBase(BaseModel):
    id_usuario: int
    id_animal: int
    observacoes: Optional[str] = None

class AdocaoCreate(AdocaoBase):
    status: Optional[str] = 'pendente'

class AdocaoUpdate(AdocaoBase):
    id_usuario: Optional[int] = None
    id_animal: Optional[int] = None
    data_adocao: Optional[datetime] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None

class AdocaoInDB(AdocaoBase):
    id_adocao: int
    data_adocao: datetime
    status: str

    class Config:
        from_attributes = True

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    # CORREÇÃO: O nome do campo foi alterado para 'estoque' para consistência.
    estoque: Optional[int] = 0
    categoria: Optional[str] = None
    imagem: Optional[str] = None

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(ProdutoBase):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    estoque: Optional[int] = None
    categoria: Optional[str] = None
    imagem: Optional[str] = None

class ProdutoInDB(ProdutoBase):
    id_produto: int

    class Config:
        from_attributes = True

class PedidoBase(BaseModel):
    id_usuario: int
    status: Optional[str] = 'pendente'
    valor_total: Optional[float] = None

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(PedidoBase):
    id_usuario: Optional[int] = None
    data_pedido: Optional[datetime] = None
    status: Optional[str] = None
    valor_total: Optional[float] = None

class PedidoInDB(PedidoBase):
    id_pedido: int
    data_pedido: datetime

    class Config:
        from_attributes = True

class ItemPedidoBase(BaseModel):
    id_pedido: int
    id_produto: int
    quantidade: int
    preco_unitario: float

class ItemPedidoCreate(ItemPedidoBase):
    pass

class ItemPedidoUpdate(ItemPedidoBase):
    id_pedido: Optional[int] = None
    id_produto: Optional[int] = None
    quantidade: Optional[int] = None
    preco_unitario: Optional[float] = None

class ItemPedidoInDB(ItemPedidoBase):
    id_item: int

    class Config:
        from_attributes = True

class DepoimentoBase(BaseModel):
    id_usuario: int
    id_animal: int
    texto: str

class DepoimentoCreate(DepoimentoBase):
    aprovado: Optional[bool] = False

class DepoimentoUpdate(DepoimentoBase):
    id_usuario: Optional[int] = None
    id_animal: Optional[int] = None
    texto: Optional[str] = None
    data_depoimento: Optional[datetime] = None
    aprovado: Optional[bool] = None

class DepoimentoInDB(DepoimentoBase):
    id_depoimento: int
    data_depoimento: datetime
    aprovado: bool

    class Config:
        from_attributes = True

class ServicoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco_base: Optional[float] = None
    duracao_minutos: Optional[int] = None

class ServicoCreate(ServicoBase):
    pass

class ServicoUpdate(ServicoBase):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco_base: Optional[float] = None
    duracao_minutos: Optional[int] = None

class ServicoInDB(ServicoBase):
    id_servico: int

    class Config:
        from_attributes = True

class PrestadorBase(BaseModel):
    nome_completo: str
    especialidade: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    id_usuario: Optional[int] = None

class PrestadorCreate(PrestadorBase):
    pass

class PrestadorUpdate(PrestadorBase):
    nome_completo: Optional[str] = None
    especialidade: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    id_usuario: Optional[int] = None

class PrestadorInDB(PrestadorBase):
    id_prestador: int

    class Config:
        from_attributes = True

class PrestadorServicoBase(BaseModel):
    id_prestador: int
    id_servico: int
    preco: Optional[float] = None

class PrestadorServicoCreate(PrestadorServicoBase):
    pass

class PrestadorServicoUpdate(PrestadorServicoBase):
    id_prestador: Optional[int] = None
    id_servico: Optional[int] = None
    preco: Optional[float] = None

class PrestadorServicoInDB(PrestadorServicoBase):
    id_prestador_serv: int

    class Config:
        from_attributes = True

class PedidoServicoBase(BaseModel):
    id_animal: int
    id_prestador_serv: int
    id_tutor: int
    inicio: datetime
    observacoes: Optional[str] = None

class PedidoServicoCreate(PedidoServicoBase):
    status: Optional[str] = 'pendente'

class PedidoServicoUpdate(PedidoServicoBase):
    id_animal: Optional[int] = None
    id_prestador_serv: Optional[int] = None
    id_tutor: Optional[int] = None
    inicio: Optional[datetime] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None

class PedidoServicoInDB(PedidoServicoBase):
    id_pedido_servico: int
    status: str

    class Config:
        from_attributes = True
