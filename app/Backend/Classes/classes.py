from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Numeric, TIMESTAMP, Enum, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, List

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
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), index=True)
    id_animal = Column(Integer, ForeignKey('animal.id_animal'), index=True)
    data_adocao = Column(TIMESTAMP, default=datetime.now)
    status = Column(String(20), default='pendente')
    observacoes = Column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('pendente', 'aprovada', 'rejeitada')", name='chk_adocao_status'),
    )

class Produto(Base):
    __tablename__ = "produtos"
    id_produto = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    preco = Column(Numeric(10, 2), nullable=False)
    estoque = Column(Integer, default=0)
    categoria = Column(String(50))
    imagem = Column(String(255))
    destaque = Column(Boolean, default=False)

class Pedido(Base):
    __tablename__ = "pedidos"
    id_pedido = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), index=True)
    data_pedido = Column(TIMESTAMP, default=datetime.now)
    status = Column(String(20), default='pendente') 
    valor_total = Column(Numeric(10, 2))
    __table_args__ = (
        CheckConstraint("status IN ('pendente', 'pago', 'cancelado', 'enviado', 'entregue')", name='chk_pedido_status'),
    )
    itens = relationship("ItemPedido", back_populates="pedido")

class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id_item = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey('pedidos.id_pedido'), index=True)
    id_produto = Column(Integer, ForeignKey('produtos.id_produto'), index=True)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto")

class Depoimento(Base):
    __tablename__ = "depoimentos"
    id_depoimento = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), index=True)
    id_animal = Column(Integer, ForeignKey('animal.id_animal'), index=True)
    texto = Column(Text, nullable=False)
    data_depoimento = Column(TIMESTAMP, default=datetime.now)
    aprovado = Column(Boolean, default=False)

class Servico(Base):
    __tablename__ = "servicos"
    id_servico = Column(Integer, primary_key=True, index=True)
    nome = Column(Text, nullable=False)
    descricao = Column(Text)
    preco_base = Column(Numeric(10, 2))
    duracao_minutos = Column(Integer)
    ativo = Column(Boolean, default=True)
    categoria = Column(String(50))
    criado_em = Column(TIMESTAMP, default=datetime.now)

class Prestador(Base):
    __tablename__ = "prestadores"
    id_prestador = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), index=True, nullable=True) 
    nome_completo = Column(Text, nullable=False)
    bio = Column(Text)
    telefone = Column(Text)
    cidade = Column(Text)
    estado = Column(String(2))
    avaliacao_media = Column(Numeric(2,1))
    verificado = Column(Boolean, default=False)
    criado_em = Column(TIMESTAMP, default=datetime.now)

class PrestadorServico(Base):
    __tablename__ = "prestador_servicos"
    id_prestador_serv = Column(Integer, primary_key=True, index=True)
    id_prestador = Column(Integer, ForeignKey("prestadores.id_prestador", ondelete="CASCADE"), index=True)
    id_servico = Column(Integer, ForeignKey("servicos.id_servico", ondelete="CASCADE"), index=True)
    preco = Column(Numeric(10, 2))
    raio_atendimento_km = Column(Integer)
    tempo_estimado_min = Column(Integer)
    ativo = Column(Boolean, default=True)
    prestador = relationship("Prestador")
    servico = relationship("Servico")

class PedidoServico(Base):
    __tablename__ = "pedidos_servico"
    id_pedido_servico = Column(Integer, primary_key=True, index=True)
    id_animal = Column(Integer, ForeignKey('animal.id_animal', ondelete="CASCADE"), index=True)
    id_prestador_serv = Column(Integer, ForeignKey('prestador_servicos.id_prestador_serv'), index=True)
    id_tutor = Column(Integer, ForeignKey('usuarios.id_usuario'), index=True)
    inicio = Column(TIMESTAMP, nullable=False)
    fim = Column(TIMESTAMP)
    status = Column(String(20), default='pendente')
    observacoes = Column(Text)
    criado_em = Column(TIMESTAMP, default=datetime.now)
    __table_args__ = (
        CheckConstraint("status IN ('pendente', 'confirmado', 'concluido', 'cancelado')", name='chk_pedido_servico_status'),
    )
    animal = relationship("Animal")
    prestador_serv = relationship("PrestadorServico")


# --- Pydantic Models ---

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
    is_admin: Optional[bool] = None

class UsuarioInDB(UsuarioBase):
    id_usuario: int
    is_admin: bool
    data_cadastro: datetime
    class Config: from_attributes = True

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
    
class AnimalInDB(AnimalBase):
    id_animal: int
    data_entrada: datetime
    class Config: from_attributes = True

class AdocaoBase(BaseModel):
    id_usuario: int
    id_animal: int
    observacoes: Optional[str] = None

class AdocaoCreate(AdocaoBase):
    status: Optional[str] = 'pendente'

class AdocaoUpdate(AdocaoBase):
    id_usuario: Optional[int] = None
    id_animal: Optional[int] = None
    status: Optional[str] = None

class AdocaoInDB(AdocaoBase):
    id_adocao: int
    data_adocao: datetime
    status: str
    class Config: from_attributes = True

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    estoque: Optional[int] = 0
    categoria: Optional[str] = None
    imagem: Optional[str] = None
    destaque: Optional[bool] = False

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoUpdate(ProdutoBase):
    nome: Optional[str] = None
    preco: Optional[float] = None
    estoque: Optional[int] = None
    destaque: Optional[bool] = None

class ProdutoInDB(ProdutoBase):
    id_produto: int
    class Config: from_attributes = True

class ServicoInDB(BaseModel):
    id_servico: int
    nome: str
    class Config: from_attributes = True

class PrestadorInDB(BaseModel):
    id_prestador: int
    nome_completo: str
    class Config: from_attributes = True
    
class ServicoDisponivelInDB(BaseModel):
    id_prestador_serv: int
    preco: Optional[float] = None
    servico: ServicoInDB
    prestador: PrestadorInDB
    class Config: from_attributes = True

class AnimalResumo(BaseModel):
    nome: str
    class Config: from_attributes = True

class PrestadorServicoDetalhes(BaseModel):
    servico: ServicoInDB
    prestador: PrestadorInDB
    class Config: from_attributes = True

class PedidoServicoDetalhado(BaseModel):
    id_pedido_servico: int
    inicio: datetime
    status: str
    observacoes: Optional[str] = None
    animal: AnimalResumo
    prestador_serv: PrestadorServicoDetalhes
    class Config: from_attributes = True
    
# --- Modelos para Pedidos de Produtos ---
class ProdutoResumo(BaseModel):
    nome: str
    preco: float
    class Config: from_attributes = True

class ItemPedidoDetalhes(BaseModel):
    quantidade: int
    preco_unitario: float
    produto: ProdutoResumo
    class Config: from_attributes = True

class PedidoDetalhado(BaseModel):
    id_pedido: int
    data_pedido: datetime
    status: str
    valor_total: float
    itens: List[ItemPedidoDetalhes]
    class Config: from_attributes = True

class PedidoBase(BaseModel):
    id_usuario: int
    status: Optional[str] = 'pendente'
    valor_total: Optional[float] = None

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(PedidoBase):
    id_usuario: Optional[int] = None
    status: Optional[str] = None
    valor_total: Optional[float] = None
    
class PedidoInDB(PedidoBase):
    id_pedido: int
    data_pedido: datetime
    class Config: from_attributes = True

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
    class Config: from_attributes = True

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
    aprovado: Optional[bool] = None

class DepoimentoInDB(DepoimentoBase):
    id_depoimento: int
    data_depoimento: datetime
    aprovado: bool
    class Config: from_attributes = True

class ServicoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco_base: Optional[float] = None
    duracao_minutos: Optional[int] = None
    ativo: Optional[bool] = True
    categoria: Optional[str] = None

class ServicoCreate(ServicoBase):
    pass

class ServicoUpdate(ServicoBase):
    nome: Optional[str] = None
    
class PrestadorBase(BaseModel):
    nome_completo: str
    id_usuario: Optional[int] = None
    bio: Optional[str] = None
    telefone: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    avaliacao_media: Optional[float] = None
    verificado: Optional[bool] = False

class PrestadorCreate(PrestadorBase):
    pass

class PrestadorUpdate(PrestadorBase):
    nome_completo: Optional[str] = None
    
class PrestadorServicoBase(BaseModel):
    id_prestador: int
    id_servico: int
    preco: Optional[float] = None
    raio_atendimento_km: Optional[int] = None
    tempo_estimado_min: Optional[int] = None
    ativo: Optional[bool] = True

class PrestadorServicoCreate(PrestadorServicoBase):
    pass

class PrestadorServicoUpdate(PrestadorServicoBase):
    id_prestador: Optional[int] = None
    id_servico: Optional[int] = None
    preco: Optional[float] = None
    raio_atendimento_km: Optional[int] = None
    tempo_estimado_min: Optional[int] = None
    ativo: Optional[bool] = None

class PrestadorServicoInDB(PrestadorServicoBase):
    id_prestador_serv: int
    class Config: from_attributes = True

class PedidoServicoBase(BaseModel):
    id_animal: int
    id_prestador_serv: int
    id_tutor: int
    inicio: datetime
    fim: Optional[datetime] = None
    observacoes: Optional[str] = None

class PedidoServicoCreate(PedidoServicoBase):
    status: Optional[str] = 'pendente'

class PedidoServicoUpdate(PedidoServicoBase):
    id_animal: Optional[int] = None
    id_prestador_serv: Optional[int] = None
    id_tutor: Optional[int] = None
    inicio: Optional[datetime] = None
    status: Optional[str] = None

class PedidoServicoInDB(PedidoServicoBase):
    id_pedido_servico: int
    status: str
    criado_em: datetime
    class Config: from_attributes = True
