from fastapi import FastAPI, HTTPException, Depends, Query, Form
from fastapi.middleware.cors import CORSMiddleware 
from Classes.classes import *
from Database.connect import connect_db
from sqlalchemy.orm import sessionmaker, Session, joinedload, selectinload
from pydantic import EmailStr
from typing import Optional, List

# SQLAlchemy setup
Engine = connect_db()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

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
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user.is_admin

# --- Root ---
@app.get("/")
async def read_root():
    return {"message": "Bem-vindo à API PataCerta!"}

# --- NOVO ENDPOINT: SERVIÇOS AGENDADOS PELO UTILIZADOR ---
@app.get("/usuarios/{user_id}/servicos-agendados/", response_model=List[PedidoServicoDetalhado])
def read_user_scheduled_services(user_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
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

# ... (restante do código de main.py permanece o mesmo)
# --- CRUD Endpoints for Usuarios ---
@app.get("/usuarios/", response_model=List[UsuarioInDB])
def read_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to view all users")
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return usuarios

@app.get("/usuarios/{usuario_id}", response_model=UsuarioInDB)
def read_usuario(usuario_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db) and current_user_id != usuario_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user's data")
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return usuario

@app.put("/usuarios/{usuario_id}", response_model=UsuarioInDB)
def update_usuario(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db) and current_user_id != usuario_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
    db_usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    for key, value in usuario.model_dump(exclude_unset=True).items():
        setattr(db_usuario, key, value)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@app.delete("/usuarios/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete users")
    
    db_usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    db.delete(db_usuario)
    db.commit()
    return {"message": "Usuario deleted successfully"}

# --- CRUD Endpoints for Animal ---
@app.post("/animals/", response_model=AnimalInDB)
def create_animal(animal: AnimalCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    user_exists = db.query(Usuario).filter(Usuario.id_usuario == current_user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found with the provided userId")

    db_animal = Animal(**animal.model_dump())
    db.add(db_animal)
    db.commit()
    db.refresh(db_animal)
    return db_animal


@app.get("/animals/", response_model=List[AnimalInDB])
def read_animals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    animals = db.query(Animal).offset(skip).limit(limit).all()
    return animals

@app.get("/animals/{animal_id}", response_model=AnimalInDB)
def read_animal(animal_id: int, db: Session = Depends(get_db)):
    animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal

@app.put("/animals/{animal_id}", response_model=AnimalInDB)
def update_animal(animal_id: int, animal: AnimalUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update animals")

    db_animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    for key, value in animal.model_dump(exclude_unset=True).items():
        setattr(db_animal, key, value)
    db.commit()
    db.refresh(db_animal)
    return db_animal

@app.delete("/animals/{animal_id}")
def delete_animal(animal_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete animals")

    db_animal = db.query(Animal).filter(Animal.id_animal == animal_id).first()
    if db_animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    db.delete(db_animal)
    db.commit()
    return {"message": "Animal deleted successfully"}

# --- CRUD Endpoints for Adocao ---
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
    adocoes = db.query(Adocao).offset(skip).limit(limit).all()
    return adocoes

@app.get("/adocoes/{adocao_id}", response_model=AdocaoInDB)
def read_adocao(adocao_id: int, db: Session = Depends(get_db)):
    adocao = db.query(Adocao).filter(Adocao.id_adocao == adocao_id).first()
    if adocao is None:
        raise HTTPException(status_code=404, detail="Adocao not found")
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
        if animal:
            animal.status = 'adotado'
    
    elif adocao.status == 'rejeitada' and db_adocao.status != 'rejeitada':
         animal = db.query(Animal).filter(Animal.id_animal == db_adocao.id_animal).first()
         if animal and animal.status == 'em_tratamento':
             animal.status = 'disponivel'

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
    
    if db_adocao.status == 'pendente' or db_adocao.status == 'em_tratamento':
        animal = db.query(Animal).filter(Animal.id_animal == db_adocao.id_animal).first()
        if animal:
            animal.status = 'disponivel'
    
    db.delete(db_adocao)
    db.commit()
    return {"message": "Adoção deletada com sucesso"}

# --- Endpoints for Products, Orders, etc. remain the same ---

# ... (omitting the rest of the endpoints for brevity, they remain unchanged)
# --- CRUD Endpoints for Produtos ---
@app.post("/produtos/", response_model=ProdutoInDB)
def create_produto(produto: ProdutoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to create products")
    db_produto = Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@app.get("/produtos/", response_model=List[ProdutoInDB])
def read_produtos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    produtos = db.query(Produto).offset(skip).limit(limit).all()
    return produtos

@app.get("/produtos/{produto_id}", response_model=ProdutoInDB)
def read_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id_produto == produto_id).first()
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto not found")
    return produto

@app.put("/produtos/{produto_id}", response_model=ProdutoInDB)
def update_produto(produto_id: int, produto: ProdutoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update products")

    db_produto = db.query(Produto).filter(Produto.id_produto == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto not found")
    for key, value in produto.model_dump(exclude_unset=True).items():
        setattr(db_produto, key, value)
    db.commit()
    db.refresh(db_produto)
    return db_produto

@app.delete("/produtos/{produto_id}")
def delete_produto(produto_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete products")

    db_produto = db.query(Produto).filter(Produto.id_produto == produto_id).first()
    if db_produto is None:
        raise HTTPException(status_code=404, detail="Produto not found")
    db.delete(db_produto)
    db.commit()
    return {"message": "Produto deleted successfully"}

# --- CRUD Endpoints for Pedidos ---
@app.post("/pedidos/", response_model=PedidoInDB)
def create_pedido(pedido: PedidoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db): 
        if pedido.id_usuario != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to create pedido for another user")
        pedido.status = 'pago' 
    
    user_in_body_exists = db.query(Usuario).filter(Usuario.id_usuario == pedido.id_usuario).first()
    if not user_in_body_exists:
        raise HTTPException(status_code=400, detail=f"User with id {pedido.id_usuario} not found.")

    db_pedido = Pedido(**pedido.model_dump())
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido


@app.get("/pedidos/", response_model=List[PedidoInDB])
def read_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pedidos = db.query(Pedido).offset(skip).limit(limit).all()
    return pedidos

@app.get("/pedidos/{pedido_id}", response_model=PedidoInDB)
def read_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(Pedido).filter(Pedido.id_pedido == pedido_id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    return pedido

@app.put("/pedidos/{pedido_id}", response_model=PedidoInDB)
def update_pedido(pedido_id: int, pedido: PedidoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update orders")

    db_pedido = db.query(Pedido).filter(Pedido.id_pedido == pedido_id).first()
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    for key, value in pedido.model_dump(exclude_unset=True).items():
        setattr(db_pedido, key, value)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido

@app.delete("/pedidos/{pedido_id}")
def delete_pedido(pedido_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete orders")

    db_pedido = db.query(Pedido).filter(Pedido.id_pedido == pedido_id).first()
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido not found")
    db.delete(db_pedido)
    db.commit()
    return {"message": "Pedido deleted successfully"}

# --- CRUD Endpoints for Itens Pedido ---
@app.post("/itens_pedido/", response_model=ItemPedidoInDB)
def create_item_pedido(item_pedido: ItemPedidoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    user_exists = db.query(Usuario).filter(Usuario.id_usuario == current_user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found with the provided userId")
    
    db_pedido = db.query(Pedido).filter(Pedido.id_pedido == item_pedido.id_pedido).first()
    if not db_pedido:
        raise HTTPException(status_code=404, detail=f"Pedido with id {item_pedido.id_pedido} not found.")
    
    if not is_user_admin(current_user_id, db) and db_pedido.id_usuario != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to add items to this order")

    db_item_pedido = ItemPedido(**item_pedido.model_dump())
    db.add(db_item_pedido)
    db.commit()
    db.refresh(db_item_pedido)
    return db_item_pedido


@app.get("/itens_pedido/", response_model=List[ItemPedidoInDB])
def read_itens_pedido(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    itens_pedido = db.query(ItemPedido).offset(skip).limit(limit).all()
    return itens_pedido

@app.get("/itens_pedido/{item_id}", response_model=ItemPedidoInDB)
def read_item_pedido(item_id: int, db: Session = Depends(get_db)):
    item_pedido = db.query(ItemPedido).filter(ItemPedido.id_item == item_id).first()
    if item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    return item_pedido

@app.put("/itens_pedido/{item_id}", response_model=ItemPedidoInDB)
def update_item_pedido(item_id: int, item_pedido: ItemPedidoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update order items")
        
    db_item_pedido = db.query(ItemPedido).filter(ItemPedido.id_item == item_id).first()
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    for key, value in item_pedido.model_dump(exclude_unset=True).items():
        setattr(db_item_pedido, key, value)
    db.commit()
    db.refresh(db_item_pedido)
    return db_item_pedido

@app.delete("/itens_pedido/{item_id}")
def delete_item_pedido(item_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete order items")

    db_item_pedido = db.query(ItemPedido).filter(ItemPedido.id_item == item_id).first()
    if db_item_pedido is None:
        raise HTTPException(status_code=404, detail="ItemPedido not found")
    db.delete(db_item_pedido)
    db.commit()
    return {"message": "ItemPedido deleted successfully"}

# --- CRUD Endpoints for Depoimentos ---
@app.post("/depoimentos/", response_model=DepoimentoInDB)
def create_depoimento(depoimento: DepoimentoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db): 
        if depoimento.id_usuario != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to create depoimento for another user")
        depoimento.aprovado = False 
    
    user_in_body_exists = db.query(Usuario).filter(Usuario.id_usuario == depoimento.id_usuario).first()
    if not user_in_body_exists:
        raise HTTPException(status_code=400, detail=f"User with id {depoimento.id_usuario} not found.")

    animal_in_body_exists = db.query(Animal).filter(Animal.id_animal == depoimento.id_animal).first()
    if not animal_in_body_exists:
        raise HTTPException(status_code=400, detail=f"Animal with id {depoimento.id_animal} not found.")

    db_depoimento = Depoimento(**depoimento.model_dump())
    db.add(db_depoimento)
    db.commit()
    db.refresh(db_depoimento)
    return db_depoimento


@app.get("/depoimentos/", response_model=List[DepoimentoInDB])
def read_depoimentos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    depoimentos = db.query(Depoimento).offset(skip).limit(limit).all()
    return depoimentos

@app.get("/depoimentos/{depoimento_id}", response_model=DepoimentoInDB)
def read_depoimento(depoimento_id: int, db: Session = Depends(get_db)):
    depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == depoimento_id).first()
    if depoimento is None:
        raise HTTPException(status_code=404, detail="Depoimento not found")
    return depoimento

@app.put("/depoimentos/{depoimento_id}", response_model=DepoimentoInDB)
def update_depoimento(depoimento_id: int, depoimento: DepoimentoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update testimonials")

    db_depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == depoimento_id).first()
    if db_depoimento is None:
        raise HTTPException(status_code=404, detail="Depoimento not found")
    for key, value in depoimento.model_dump(exclude_unset=True).items():
        setattr(db_depoimento, key, value)
    db.commit()
    db.refresh(db_depoimento)
    return db_depoimento

@app.delete("/depoimentos/{depoimento_id}")
def delete_depoimento(depoimento_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete testimonials")

    db_depoimento = db.query(Depoimento).filter(Depoimento.id_depoimento == depoimento_id).first()
    if db_depoimento is None:
        raise HTTPException(status_code=404, detail="Depoimento not found")
    db.delete(db_depoimento)
    db.commit()
    return {"message": "Depoimento deleted successfully"}

# --- CRUD Endpoints for Servicos (Base para Admin) ---
@app.post("/servicos/", response_model=ServicoInDB)
def create_servico(servico: ServicoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to create services")
    db_servico = Servico(**servico.model_dump())
    db.add(db_servico)
    db.commit()
    db.refresh(db_servico)
    return db_servico

@app.get("/servicos/", response_model=List[ServicoInDB])
def read_servicos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    servicos = db.query(Servico).offset(skip).limit(limit).all()
    return servicos

@app.get("/servicos/{servico_id}", response_model=ServicoInDB)
def read_servico(servico_id: int, db: Session = Depends(get_db)):
    servico = db.query(Servico).filter(Servico.id_servico == servico_id).first()
    if servico is None:
        raise HTTPException(status_code=404, detail="Servico not found")
    return servico

@app.put("/servicos/{servico_id}", response_model=ServicoInDB)
def update_servico(servico_id: int, servico: ServicoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update services")

    db_servico = db.query(Servico).filter(Servico.id_servico == servico_id).first()
    if db_servico is None:
        raise HTTPException(status_code=404, detail="Servico not found")
    for key, value in servico.model_dump(exclude_unset=True).items():
        setattr(db_servico, key, value)
    db.commit()
    db.refresh(db_servico)
    return db_servico

@app.delete("/servicos/{servico_id}")
def delete_servico(servico_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete services")

    db_servico = db.query(Servico).filter(Servico.id_servico == servico_id).first()
    if db_servico is None:
        raise HTTPException(status_code=404, detail="Servico not found")
    db.delete(db_servico)
    db.commit()
    return {"message": "Servico deleted successfully"}

# --- CRUD Endpoints for Prestadores ---
@app.post("/prestadores/", response_model=PrestadorInDB)
def create_prestador(prestador: PrestadorCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to create prestadores")
    
    if prestador.id_usuario:
        user_in_body_exists = db.query(Usuario).filter(Usuario.id_usuario == prestador.id_usuario).first()
        if not user_in_body_exists:
            raise HTTPException(status_code=400, detail=f"User with id {prestador.id_usuario} not found for this prestador.")

    db_prestador = Prestador(**prestador.model_dump())
    db.add(db_prestador)
    db.commit()
    db.refresh(db_prestador)
    return db_prestador

@app.get("/prestadores/", response_model=List[PrestadorInDB])
def read_prestadores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    prestadores = db.query(Prestador).offset(skip).limit(limit).all()
    return prestadores

@app.get("/prestadores/{prestador_id}", response_model=PrestadorInDB)
def read_prestador(prestador_id: int, db: Session = Depends(get_db)):
    prestador = db.query(Prestador).filter(Prestador.id_prestador == prestador_id).first()
    if prestador is None:
        raise HTTPException(status_code=404, detail="Prestador not found")
    return prestador

@app.put("/prestadores/{prestador_id}", response_model=PrestadorInDB)
def update_prestador(prestador_id: int, prestador: PrestadorUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update providers")

    db_prestador = db.query(Prestador).filter(Prestador.id_prestador == prestador_id).first()
    if db_prestador is None:
        raise HTTPException(status_code=404, detail="Prestador not found")
    for key, value in prestador.model_dump(exclude_unset=True).items():
        setattr(db_prestador, key, value)
    db.commit()
    db.refresh(db_prestador)
    return db_prestador

@app.delete("/prestadores/{prestador_id}")
def delete_prestador(prestador_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete providers")

    db_prestador = db.query(Prestador).filter(Prestador.id_prestador == prestador_id).first()
    if db_prestador is None:
        raise HTTPException(status_code=404, detail="Prestador not found")
    db.delete(db_prestador)
    db.commit()
    return {"message": "Prestador deleted successfully"}

# --- CRUD Endpoints for PrestadorServicos ---
@app.post("/prestador_servicos/", response_model=PrestadorServicoInDB)
def create_prestador_servico(prestador_servico: PrestadorServicoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to create prestador services associations")
    
    prestador_exists = db.query(Prestador).filter(Prestador.id_prestador == prestador_servico.id_prestador).first()
    if not prestador_exists:
        raise HTTPException(status_code=400, detail=f"Prestador with id {prestador_servico.id_prestador} not found.")
    
    servico_exists = db.query(Servico).filter(Servico.id_servico == prestador_servico.id_servico).first()
    if not servico_exists:
        raise HTTPException(status_code=400, detail=f"Servico with id {prestador_servico.id_servico} not found.")

    db_prestador_servico = PrestadorServico(**prestador_servico.model_dump())
    db.add(db_prestador_servico)
    db.commit()
    db.refresh(db_prestador_servico)
    return db_prestador_servico

@app.get("/prestador_servicos/", response_model=List[PrestadorServicoInDB])
def read_prestador_servicos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    prestador_servicos = db.query(PrestadorServico).offset(skip).limit(limit).all()
    return prestador_servicos

@app.get("/prestador_servicos/{prestador_serv_id}", response_model=PrestadorServicoInDB)
def read_prestador_servico(prestador_serv_id: int, db: Session = Depends(get_db)):
    prestador_servico = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == prestador_serv_id).first()
    if prestador_servico is None:
        raise HTTPException(status_code=404, detail="PrestadorServico not found")
    return prestador_servico

@app.put("/prestador_servicos/{prestador_serv_id}", response_model=PrestadorServicoInDB)
def update_prestador_servico(prestador_serv_id: int, prestador_servico: PrestadorServicoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update provider service associations")

    db_prestador_servico = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == prestador_serv_id).first()
    if db_prestador_servico is None:
        raise HTTPException(status_code=404, detail="PrestadorServico not found")
    for key, value in prestador_servico.model_dump(exclude_unset=True).items():
        setattr(db_prestador_servico, key, value)
    db.commit()
    db.refresh(db_prestador_servico)
    return db_prestador_servico

@app.delete("/prestador_servicos/{prestador_serv_id}")
def delete_prestador_servico(prestador_serv_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete provider service associations")

    db_prestador_servico = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == prestador_serv_id).first()
    if db_prestador_servico is None:
        raise HTTPException(status_code=404, detail="PrestadorServico not found")
    db.delete(db_prestador_servico)
    db.commit()
    return {"message": "PrestadorServico deleted successfully"}

# --- CRUD Endpoints for PedidosServico ---
@app.post("/pedidos_servico/", response_model=PedidoServicoInDB)
def create_pedido_servico(pedido_servico: PedidoServicoCreate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db): 
        if pedido_servico.id_tutor != current_user_id: 
            raise HTTPException(status_code=403, detail="Not authorized to create service order for another tutor")
        pedido_servico.status = 'pendente' 
    
    animal_exists = db.query(Animal).filter(Animal.id_animal == pedido_servico.id_animal).first()
    if not animal_exists:
        raise HTTPException(status_code=400, detail=f"Animal with id {pedido_servico.id_animal} not found.")
    
    prestador_serv_exists = db.query(PrestadorServico).filter(PrestadorServico.id_prestador_serv == pedido_servico.id_prestador_serv).first()
    if not prestador_serv_exists:
        raise HTTPException(status_code=400, detail=f"PrestadorServico with id {pedido_servico.id_prestador_serv} not found.")
    
    tutor_exists = db.query(Usuario).filter(Usuario.id_usuario == pedido_servico.id_tutor).first()
    if not tutor_exists:
        raise HTTPException(status_code=400, detail=f"Tutor with id {pedido_servico.id_tutor} not found.")

    db_pedido_servico = PedidoServico(**pedido_servico.model_dump())
    db.add(db_pedido_servico)
    db.commit()
    db.refresh(db_pedido_servico)
    return db_pedido_servico

@app.get("/pedidos_servico/", response_model=List[PedidoServicoInDB])
def read_pedidos_servico(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pedidos_servico = db.query(PedidoServico).offset(skip).limit(limit).all()
    return pedidos_servico

@app.get("/pedidos_servico/{pedido_servico_id}", response_model=PedidoServicoInDB)
def read_pedido_servico(pedido_servico_id: int, db: Session = Depends(get_db)):
    pedido_servico = db.query(PedidoServico).filter(PedidoServico.id_pedido_servico == pedido_servico_id).first()
    if pedido_servico is None:
        raise HTTPException(status_code=404, detail="PedidoServico not found")
    return pedido_servico

@app.put("/pedidos_servico/{pedido_servico_id}", response_model=PedidoServicoInDB)
def update_pedido_servico(pedido_servico_id: int, pedido_servico: PedidoServicoUpdate, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to update service orders")

    db_pedido_servico = db.query(PedidoServico).filter(PedidoServico.id_pedido_servico == pedido_servico_id).first()
    if db_pedido_servico is None:
        raise HTTPException(status_code=404, detail="PedidoServico not found")
    for key, value in pedido_servico.model_dump(exclude_unset=True).items():
        setattr(db_pedido_servico, key, value)
    db.commit()
    db.refresh(db_pedido_servico)
    return db_pedido_servico

@app.delete("/pedidos_servico/{pedido_servico_id}")
def delete_pedido_servico(pedido_servico_id: int, db: Session = Depends(get_db), current_user_id: int = Query(..., alias="userId")):
    if not is_user_admin(current_user_id, db):
        raise HTTPException(status_code=403, detail="Not authorized to delete service orders")

    db_pedido_servico = db.query(PedidoServico).filter(PedidoServico.id_pedido_servico == pedido_servico_id).first()
    if db_pedido_servico is None:
        raise HTTPException(status_code=404, detail="PedidoServico not found")
    db.delete(db_pedido_servico)
    db.commit()
    return {"message": "PedidoServico deleted successfully"}

# --- Endpoints de Autenticação ---

@app.post("/register", response_model=UsuarioInDB)
def register_user(usuario: UsuarioCreate, db: Session = Depends(get_db)):
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
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user.senha != password:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    
    return user


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)