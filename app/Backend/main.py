from fastapi import FastAPI, HTTPException, Depends, Query, Form
from fastapi.middleware.cors import CORSMiddleware
# Adicionada importação para servir arquivos estáticos
from fastapi.staticfiles import StaticFiles
from Classes.classes import *
from Database.connect import connect_db
from sqlalchemy.orm import sessionmaker, Session, joinedload, selectinload
from pydantic import EmailStr
from typing import Optional, List
import os

# Configuração do SQLAlchemy
Engine = connect_db()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# Dependência para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

app.mount("/static_images", StaticFiles(directory="static_images"), name="static_images")


# Configuração do CORS para permitir requisições do frontend
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_user_admin(user_id: int, db: Session) -> bool:
    """Função auxiliar para verificar se o usuário é administrador."""
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user.is_admin

# --- Root ---
@app.get("/")
async def read_root():
    """Endpoint principal da API."""
    return {"message": "Bem-vindo à API PataCerta!"}

# --- ENDPOINT: PEDIDOS DE PRODUTOS DO UTILIZADOR ---
@app.get("/usuarios/{user_id}/pedidos/", response_model=List[PedidoDetalhado])
def read_user_orders(user_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    """
    Busca todos os pedidos de produtos para um utilizador específico, incluindo detalhes dos itens.
    É necessária autorização: o utilizador deve ser o dono dos pedidos ou um administrador.
    """
    if user_id != current_user_id and not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a ver os pedidos deste usuário")

    pedidos = (
        db.query(Pedido)
        .filter(Pedido.id_usuario == user_id)
        .options(
            selectinload(Pedido.itens).selectinload(ItemPedido.produto)
        )
        .order_by(Pedido.data_pedido.desc())
        .all()
    )
    
    if not pedidos:
        return []

    return pedidos


# --- ENDPOINT: SERVIÇOS AGENDADOS PELO UTILIZADOR ---
@app.get("/usuarios/{user_id}/servicos-agendados/", response_model=List[PedidoServicoDetalhado])
def read_user_scheduled_services(user_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    """Busca todos os serviços agendados por um usuário."""
    if user_id != current_user_id and not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado")

    pedidos = (
        db.query(PedidoServico)
        .filter(PedidoServico.id_tutor == user_id)
        .options(
            selectinload(PedidoServico.animal),
            selectinload(PedidoServico.prestador_serv).selectinload(PrestadorServico.servico),
            selectinload(PedidoServico.prestador_serv).selectinload(PrestadorServico.prestador)
        )
        .order_by(PedidoServico.inicio.desc())
        .all()
    )
    return pedidos

@app.get("/servicos-disponiveis/", response_model=List[ServicoDisponivelInDB])
def read_servicos_disponiveis(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    """Lista todos os serviços ativos oferecidos por prestadores."""
    resultados = (
        db.query(PrestadorServico)
        .options(
            joinedload(PrestadorServico.servico),
            joinedload(PrestadorServico.prestador)
        )
        .join(Servico, PrestadorServico.id_servico == Servico.id_servico)
        .filter(Servico.ativo == True, PrestadorServico.ativo == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return resultados

# --- Endpoints CRUD para Usuários ---
@app.get("/usuarios/", response_model=List[UsuarioInDB])
def read_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado para ver todos os usuários")
    return db.query(Usuario).offset(skip).limit(limit).all()

@app.get("/usuarios/{usuario_id}", response_model=UsuarioInDB)
def read_usuario(usuario_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db) and current_user_id != usuario_id:
        raise HTTPException(status_code=403, detail="Não autorizado para ver os dados deste usuário")
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario

@app.put("/usuarios/{usuario_id}", response_model=UsuarioInDB)
def update_usuario(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db) and current_user_id != usuario_id:
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar este usuário")
        
    db_usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    for key, value in usuario.model_dump(exclude_unset=True).items():
        setattr(db_usuario, key, value)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@app.delete("/usuarios/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar usuários")
    
    db_usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(db_usuario)
    db.commit()
    return {"message": "Usuário deletado com sucesso"}

# --- Endpoints CRUD para Animais ---
@app.post("/animals/", response_model=AnimalInDB)
def create_animal(animal: AnimalCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a criar animais")

    db_animal = Animal(**animal.model_dump())
    db.add(db_animal)
    db.commit()
    db.refresh(db_animal)
    return db_animal

@app.get("/animals/", response_model=List[AnimalInDB])
def read_animals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Animal).offset(skip).limit(limit).all()

@app.get("/animals/{animal_id}", response_model=AnimalInDB)
def read_animal(animal_id: int, db: Session = Depends(get_db)):
    animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    return animal

@app.put("/animals/{animal_id}", response_model=AnimalInDB)
def update_animal(animal_id: int, animal: AnimalUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar animais")

    db_animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    for key, value in animal.model_dump(exclude_unset=True).items():
        setattr(db_animal, key, value)
    db.commit()
    db.refresh(db_animal)
    return db_animal

@app.delete("/animals/{animal_id}")
def delete_animal(animal_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar animais")

    db_animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Animal não encontrado")
    db.delete(db_animal)
    db.commit()
    return {"message": "Animal deletado com sucesso"}

# --- Endpoints CRUD para Adoção ---
@app.post("/adocoes/", response_model=AdocaoInDB)
def create_adocao(adocao: AdocaoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db): 
        if adocao.id_usuario != current_user_id:
            raise HTTPException(status_code=403, detail="Não autorizado a criar adoção para outro usuário")
        adocao.status = 'pendente'
    
    user_in_db = db.query(Usuario).filter(Usuario.id_usuario == adocao.id_usuario).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail=f"Usuário com id {adocao.id_usuario} não encontrado.")

    try:
        db_animal = db.query(Animal).filter(Animal.id_animal == adocao.id_animal).with_for_update().first()

        if not db_animal:
            raise HTTPException(status_code=404, detail=f"Animal com id {adocao.id_animal} não encontrado.")

        if db_animal.status != 'disponivel':
            raise HTTPException(status_code=400, detail=f"O animal '{db_animal.nome}' não está mais disponível para adoção.")

        db_adocao = Adocao(**adocao.model_dump())
        db.add(db_adocao)
        db_animal.status = 'em_tratamento'
        db.commit()
        db.refresh(db_adocao)
        return db_adocao

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno ao processar a adoção.")

@app.get("/adocoes/", response_model=List[AdocaoInDB])
def read_adocoes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Adocao).offset(skip).limit(limit).all()

@app.get("/adocoes/{adocao_id}", response_model=AdocaoInDB)
def read_adocao(adocao_id: int, db: Session = Depends(get_db)):
    adocao = db.query(Adocao).filter(Adocao.id_adocao == adocao_id).first()
    if adocao is None:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")
    return adocao

@app.put("/adocoes/{adocao_id}", response_model=AdocaoInDB)
def update_adocao(adocao_id: int, adocao: AdocaoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar adoções")

    db_adocao = db.query(Adocao).filter(Adocao.id_adocao == adocao_id).first()
    if db_adocao is None:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")

    if adocao.status == 'aprovada' and db_adocao.status != 'aprovada':
        animal = db.query(Animal).filter(Animal.id_animal == db_adocao.id_animal).first()
        if animal: animal.status = 'adotado'
    
    elif adocao.status == 'rejeitada' and db_adocao.status != 'rejeitada':
         animal = db.query(Animal).filter(Animal.id_animal == db_adocao.id_animal).first()
         if animal and animal.status == 'em_tratamento': animal.status = 'disponivel'

    for key, value in adocao.model_dump(exclude_unset=True).items():
        setattr(db_adocao, key, value)
    
    db.commit()
    db.refresh(db_adocao)
    return db_adocao

@app.delete("/adocoes/{adocao_id}")
def delete_adocao(adocao_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar adoções")

    db_adocao = db.query(Adocao).filter(Adocao.id_adocao == adocao_id).first()
    if db_adocao is None:
        raise HTTPException(status_code=404, detail="Adoção não encontrada")
    
    if db_adocao.status in ['pendente', 'em_tratamento']:
        animal = db.query(Animal).filter(Animal.id_animal == db_adocao.id_animal).first()
        if animal: animal.status = 'disponivel'
    
    db.delete(db_adocao)
    db.commit()
    return {"message": "Adoção deletada com sucesso"}

# --- Endpoints CRUD para Produtos ---
@app.post("/produtos/", response_model=ProdutoInDB)
def create_produto(produto: ProdutoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a criar produtos")
    db_produto = Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@app.get("/produtos/", response_model=List[ProdutoInDB])
def read_produtos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Produto).offset(skip).limit(limit).all()

@app.get("/produtos/{produto_id}", response_model=ProdutoInDB)
def read_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id_produto == produto_id).first()
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@app.put("/produtos/{produto_id}", response_model=ProdutoInDB)
def update_produto(produto_id: int, produto: ProdutoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar produtos")

    db_produto = db.query(Produto).filter(Produto.id_produto == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for key, value in produto.model_dump(exclude_unset=True).items():
        setattr(db_produto, key, value)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@app.delete("/produtos/{produto_id}")
def delete_produto(produto_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar produtos")

    db_produto = db.query(Produto).filter(Produto.id_produto == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(db_produto)
    db.commit()
    return {"message": "Produto deletado com sucesso"}

# --- Endpoints CRUD para Pedidos ---
@app.post("/pedidos/", response_model=PedidoInDB)
def create_pedido(pedido: PedidoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db): 
        if pedido.id_usuario != current_user_id:
            raise HTTPException(status_code=403, detail="Não autorizado a criar pedido para outro usuário")
        pedido.status = 'pago' 
    
    user_in_body_exists = db.query(Usuario).filter(Usuario.id_usuario == pedido.id_usuario).first()
    if not user_in_body_exists:
        raise HTTPException(status_code=400, detail=f"Usuário com id {pedido.id_usuario} não encontrado.")

    db_pedido = Pedido(**pedido.model_dump())
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido

@app.get("/pedidos/", response_model=List[PedidoInDB])
def read_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Pedido).offset(skip).limit(limit).all()

@app.get("/pedidos/{pedido_id}", response_model=PedidoInDB)
def read_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id_pedido == pedido_id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido

@app.put("/pedidos/{pedido_id}", response_model=PedidoInDB)
def update_pedido(pedido_id: int, pedido: PedidoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar pedidos")

    db_pedido = db.query(Pedido).filter(Pedido.id_pedido == pedido_id).first()
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    for key, value in pedido.model_dump(exclude_unset=True).items():
        setattr(db_pedido, key, value)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido

@app.delete("/pedidos/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar pedidos")

    db_pedido = db.query(Pedido).filter(Pedido.id_pedido == pedido_id).first()
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    db.delete(db_pedido)
    db.commit()
    return {"message": "Pedido deletado com sucesso"}

# --- Endpoints CRUD para Itens do Pedido ---
@app.post("/itens_pedido/", response_model=ItemPedidoInDB)
def create_item_pedido(item_pedido: ItemPedidoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    user_exists = db.query(Usuario).filter(Usuario.id_usuario == current_user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    db_pedido = db.query(Pedido).filter(Pedido.id_pedido == item_pedido.id_pedido).first()
    if not db_pedido:
        raise HTTPException(status_code=404, detail=f"Pedido com id {item_pedido.id_pedido} não encontrado.")
    
    if not is_user_admin(current_user_id, db) and db_pedido.id_usuario != current_user_id:
        raise HTTPException(status_code=403, detail="Não autorizado a adicionar itens a este pedido")

    db_item_pedido = ItemPedido(**item_pedido.model_dump())
    db.add(db_item_pedido)
    db.commit()
    db.refresh(db_item_pedido)
    return db_item_pedido

@app.get("/itens_pedido/", response_model=List[ItemPedidoInDB])
def read_itens_pedido(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(ItemPedido).offset(skip).limit(limit).all()

@app.get("/itens_pedido/{item_id}", response_model=ItemPedidoInDB)
def read_item_pedido(item_id: int, db: Session = Depends(get_db)):
    item_pedido = db.query(ItemPedido).filter(ItemPedido.id_item == item_id).first()
    if item_pedido is None:
        raise HTTPException(status_code=404, detail="Item do pedido não encontrado")
    return item_pedido

@app.put("/itens_pedido/{item_id}", response_model=ItemPedidoInDB)
def update_item_pedido(item_id: int, item_pedido: ItemPedidoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar itens de pedido")
        
    db_item_pedido = db.query(ItemPedido).filter(ItemPedido.id_item == item_id).first()
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="Item do pedido não encontrado")
    for key, value in item_pedido.model_dump(exclude_unset=True).items():
        setattr(db_item_pedido, key, value)
    db.commit()
    db.refresh(db_item_pedido)
    return db_item_pedido

@app.delete("/itens_pedido/{item_id}")
def delete_item_pedido(item_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar itens de pedido")

    db_item_pedido = db.query(ItemPedido).filter(ItemPedido.id_item == item_id).first()
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="Item do pedido não encontrado")
    db.delete(db_item_pedido)
    db.commit()
    return {"message": "Item do pedido deletado com sucesso"}

# --- Endpoints CRUD para Depoimentos ---
@app.post("/depoimentos/", response_model=DepoimentoInDB)
def create_depoimento(depoimento: DepoimentoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db): 
        if depoimento.id_usuario != current_user_id:
            raise HTTPException(status_code=403, detail="Não autorizado a criar depoimento para outro usuário")
        depoimento.aprovado = False 
    
    user_in_body_exists = db.query(Usuario).filter(Usuario.id_usuario == depoimento.id_usuario).first()
    if not user_in_body_exists:
        raise HTTPException(status_code=400, detail=f"Usuário com id {depoimento.id_usuario} não encontrado.")

    animal_in_body_exists = db.query(Animal).filter(Animal.id_animal == depoimento.id_animal).first()
    if not animal_in_body_exists:
        raise HTTPException(status_code=400, detail=f"Animal com id {depoimento.id_animal} não encontrado.")

    db_depoimento = Depoimento(**depoimento.model_dump())
    db.add(db_depoimento)
    db.commit()
    db.refresh(db_depoimento)
    return db_depoimento

@app.get("/depoimentos/", response_model=List[DepoimentoInDB])
def read_depoimentos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Depoimento).offset(skip).limit(limit).all()

@app.get("/depoimentos/{depoimento_id}", response_model=DepoimentoInDB)
def read_depoimento(depoimento_id: int, db: Session = Depends(get_db)):
    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == depoimento_id).first()
    if depoimento is None:
        raise HTTPException(status_code=404, detail="Depoimento não encontrado")
    return depoimento

@app.put("/depoimentos/{depoimento_id}", response_model=DepoimentoInDB)
def update_depoimento(depoimento_id: int, depoimento: DepoimentoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar depoimentos")

    db_depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == depoimento_id).first()
    if db_depoimento is None:
        raise HTTPException(status_code=404, detail="Depoimento não encontrado")
    for key, value in depoimento.model_dump(exclude_unset=True).items():
        setattr(db_depoimento, key, value)
    db.commit()
    db.refresh(db_depoimento)
    return db_depoimento

@app.delete("/depoimentos/{depoimento_id}")
def delete_depoimento(depoimento_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar depoimentos")

    db_depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == depoimento_id).first()
    if db_depoimento is None:
        raise HTTPException(status_code=404, detail="Depoimento não encontrado")
    db.delete(db_depoimento)
    db.commit()
    return {"message": "Depoimento deletado com sucesso"}

# --- Endpoints CRUD para Serviços (Base para Admin) ---
@app.post("/servicos/", response_model=ServicoInDB)
def create_servico(servico: ServicoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a criar serviços")
    db_servico = Servico(**servico.model_dump())
    db.add(db_servico)
    db.commit()
    db.refresh(db_servico)
    return db_servico

@app.get("/servicos/", response_model=List[ServicoInDB])
def read_servicos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Servico).offset(skip).limit(limit).all()

@app.get("/servicos/{servico_id}", response_model=ServicoInDB)
def read_servico(servico_id: int, db: Session = Depends(get_db)):
    servico = db.query(Servico).filter(Servico.id_servico == servico_id).first()
    if servico is None:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return servico

@app.put("/servicos/{servico_id}", response_model=ServicoInDB)
def update_servico(servico_id: int, servico: ServicoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar serviços")

    db_servico = db.query(Servico).filter(Servico.id_servico == servico_id).first()
    if db_servico is None:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    for key, value in servico.model_dump(exclude_unset=True).items():
        setattr(db_servico, key, value)
    db.commit()
    db.refresh(db_servico)
    return db_servico

@app.delete("/servicos/{servico_id}")
def delete_servico(servico_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar serviços")

    db_servico = db.query(Servico).filter(Servico.id_servico == servico_id).first()
    if db_servico is None:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    db.delete(db_servico)
    db.commit()
    return {"message": "Serviço deletado com sucesso"}

# --- Endpoints CRUD para Prestadores ---
@app.post("/prestadores/", response_model=PrestadorInDB)
def create_prestador(prestador: PrestadorCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a criar prestadores")
    
    if prestador.id_usuario:
        user_in_body_exists = db.query(Usuario).filter(Usuario.id_usuario == prestador.id_usuario).first()
        if not user_in_body_exists:
            raise HTTPException(status_code=400, detail=f"Usuário com id {prestador.id_usuario} não encontrado para este prestador.")

    db_prestador = Prestador(**prestador.model_dump())
    db.add(db_prestador)
    db.commit()
    db.refresh(db_prestador)
    return db_prestador

@app.get("/prestadores/", response_model=List[PrestadorInDB])
def read_prestadores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Prestador).offset(skip).limit(limit).all()

@app.get("/prestadores/{prestador_id}", response_model=PrestadorInDB)
def read_prestador(prestador_id: int, db: Session = Depends(get_db)):
    prestador = db.query(Prestador).filter(Prestador.id_prestador == prestador_id).first()
    if prestador is None:
        raise HTTPException(status_code=404, detail="Prestador não encontrado")
    return prestador

@app.put("/prestadores/{prestador_id}", response_model=PrestadorInDB)
def update_prestador(prestador_id: int, prestador: PrestadorUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar prestadores")

    db_prestador = db.query(Prestador).filter(Prestador.id_prestador == prestador_id).first()
    if db_prestador is None:
        raise HTTPException(status_code=404, detail="Prestador não encontrado")
    for key, value in prestador.model_dump(exclude_unset=True).items():
        setattr(db_prestador, key, value)
    db.commit()
    db.refresh(db_prestador)
    return db_prestador

@app.delete("/prestadores/{prestador_id}")
def delete_prestador(prestador_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar prestadores")

    db_prestador = db.query(Prestador).filter(Prestador.id_prestador == prestador_id).first()
    if db_prestador is None:
        raise HTTPException(status_code=404, detail="Prestador não encontrado")
    db.delete(db_prestador)
    db.commit()
    return {"message": "Prestador deletado com sucesso"}

# --- Endpoints CRUD para PrestadorServicos ---
@app.post("/prestador_servicos/", response_model=PrestadorServicoInDB)
def create_prestador_servico(prestador_servico: PrestadorServicoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a criar associações de serviços de prestadores")
    
    prestador_exists = db.query(Prestador).filter(Prestador.id_prestador == prestador_servico.id_prestador).first()
    if not prestador_exists:
        raise HTTPException(status_code=400, detail=f"Prestador com id {prestador_servico.id_prestador} não encontrado.")
    
    servico_exists = db.query(Servico).filter(Servico.id_servico == prestador_servico.id_servico).first()
    if not servico_exists:
        raise HTTPException(status_code=400, detail=f"Serviço com id {prestador_servico.id_servico} não encontrado.")

    db_prestador_servico = PrestadorServico(**prestador_servico.model_dump())
    db.add(db_prestador_servico)
    db.commit()
    db.refresh(db_prestador_servico)
    return db_prestador_servico

@app.get("/prestador_servicos/", response_model=List[PrestadorServicoInDB])
def read_prestador_servicos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(PrestadorServico).offset(skip).limit(limit).all()

@app.get("/prestador_servicos/{prestador_serv_id}", response_model=PrestadorServicoInDB)
def read_prestador_servico(prestador_serv_id: int, db: Session = Depends(get_db)):
    prestador_servico = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == prestador_serv_id).first()
    if prestador_servico is None:
        raise HTTPException(status_code=404, detail="Associação Prestador-Serviço não encontrada")
    return prestador_servico

@app.put("/prestador_servicos/{prestador_serv_id}", response_model=PrestadorServicoInDB)
def update_prestador_servico(prestador_serv_id: int, prestador_servico: PrestadorServicoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar associações de serviços de prestadores")

    db_prestador_servico = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == prestador_serv_id).first()
    if db_prestador_servico is None:
        raise HTTPException(status_code=404, detail="Associação Prestador-Serviço não encontrada")
    for key, value in prestador_servico.model_dump(exclude_unset=True).items():
        setattr(db_prestador_servico, key, value)
    db.commit()
    db.refresh(db_prestador_servico)
    return db_prestador_servico

@app.delete("/prestador_servicos/{prestador_serv_id}")
def delete_prestador_servico(prestador_serv_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar associações de serviços de prestadores")

    db_prestador_servico = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == prestador_serv_id).first()
    if db_prestador_servico is None:
        raise HTTPException(status_code=404, detail="Associação Prestador-Serviço não encontrada")
    db.delete(db_prestador_servico)
    db.commit()
    return {"message": "Associação Prestador-Serviço deletada com sucesso"}

# --- Endpoints CRUD para PedidosServico ---
@app.post("/pedidos_servico/", response_model=PedidoServicoInDB)
def create_pedido_servico(pedido_servico: PedidoServicoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db): 
        if pedido_servico.id_tutor != current_user_id: 
            raise HTTPException(status_code=403, detail="Não autorizado a criar pedido de serviço para outro tutor")
        pedido_servico.status = 'pendente' 
    
    animal_exists = db.query(Animal).filter(Animal.id_animal == pedido_servico.id_animal).first()
    if not animal_exists:
        raise HTTPException(status_code=400, detail=f"Animal com id {pedido_servico.id_animal} não encontrado.")
    
    prestador_serv_exists = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == pedido_servico.id_prestador_serv).first()
    if not prestador_serv_exists:
        raise HTTPException(status_code=400, detail=f"Oferta de Serviço com id {pedido_servico.id_prestador_serv} não encontrada.")
    
    tutor_exists = db.query(Usuario).filter(Usuario.id_usuario == pedido_servico.id_tutor).first()
    if not tutor_exists:
        raise HTTPException(status_code=400, detail=f"Tutor com id {pedido_servico.id_tutor} não encontrado.")

    db_pedido_servico = PedidoServico(**pedido_servico.model_dump())
    db.add(db_pedido_servico)
    db.commit()
    db.refresh(db_pedido_servico)
    return db_pedido_servico

@app.get("/pedidos_servico/", response_model=List[PedidoServicoInDB])
def read_pedidos_servico(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(PedidoServico).offset(skip).limit(limit).all()

@app.get("/pedidos_servico/{pedido_servico_id}", response_model=PedidoServicoInDB)
def read_pedido_servico(pedido_servico_id: int, db: Session = Depends(get_db)):
    pedido_servico = db.query(PedidoServico).filter(PedidoServico.id_pedido_servico == pedido_servico_id).first()
    if pedido_servico is None:
        raise HTTPException(status_code=404, detail="Pedido de serviço não encontrado")
    return pedido_servico

@app.put("/pedidos_servico/{pedido_servico_id}", response_model=PedidoServicoInDB)
def update_pedido_servico(pedido_servico_id: int, pedido_servico: PedidoServicoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a atualizar pedidos de serviço")

    db_pedido_servico = db.query(PedidoServico).filter(PedidoServico.id_pedido_servico == pedido_servico_id).first()
    if db_pedido_servico is None:
        raise HTTPException(status_code=404, detail="Pedido de serviço não encontrado")
    for key, value in pedido_servico.model_dump(exclude_unset=True).items():
        setattr(db_pedido_servico, key, value)
    db.commit()
    db.refresh(db_pedido_servico)
    return db_pedido_servico

@app.delete("/pedidos_servico/{pedido_servico_id}")
def delete_pedido_servico(pedido_servico_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Não autorizado a deletar pedidos de serviço")

    db_pedido_servico = db.query(PedidoServico).filter(PedidoServico.id_pedido_servico == pedido_servico_id).first()
    if db_pedido_servico is None:
        raise HTTPException(status_code=404, detail="Pedido de serviço não encontrado")
    db.delete(db_pedido_servico)
    db.commit()
    return {"message": "Pedido de serviço deletado com sucesso"}

# --- Endpoints de Autenticação ---
@app.post("/register", response_model=UsuarioInDB)
def register_user(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Regista um novo usuário no sistema."""
    db_user = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado")
    
    db_usuario = Usuario(**usuario.model_dump())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@app.post("/login", response_model=UsuarioInDB)
def login_for_access(db: Session = Depends(get_db), email: EmailStr = Form(...), password: str = Form(...)):
    """Autentica um usuário e retorna seus dados."""
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # NOTA: Em produção, use hashing de senhas.
    if user.senha != password:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    return user

# --- Execução da Aplicação ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)