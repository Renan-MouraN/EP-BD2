#CÓDIGO COM AS SEGUINTES OTIMIZAÇÕES:
#1.Adicionar índices adequados para as consultas mais frequentes
#2.Implementar cache para reduzir consultas repetitivas ao banco de dados
#3.Criar views materializadas para consultas complexas frequentemente acessadas


from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from werkzeug.utils import secure_filename
from functools import wraps
from flask_caching import Cache  # Nova importação para cache
import time

app = Flask(__name__)
app.secret_key = 'patacerta_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Configuração do cache
app.config['CACHE_TYPE'] = 'SimpleCache'  # Pode ser alterado para Redis ou Memcached em produção
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Tempo em segundos
cache = Cache(app)

# Garantir que a pasta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Extensões permitidas para imagens
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    dsn = "dbname=petmatch user=postgres password=senha host=localhost port=5432"
    conn = psycopg2.connect(dsn)
    conn.set_client_encoding('UTF8')
    return conn

# Função para criar índices e views materializadas
def setup_database_optimizations():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Criar índices para colunas frequentemente pesquisadas
    # Isso vai acelerar as consultas de filtragem na tabela animal
    cur.execute("""
        DO $$
        BEGIN
            -- Criar índice para status (frequentemente filtrado)
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_animal_status') THEN
                CREATE INDEX idx_animal_status ON animal(status);
            END IF;
            
            -- Criar índice para tipo (frequentemente filtrado)
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_animal_tipo') THEN
                CREATE INDEX idx_animal_tipo ON animal(tipo);
            END IF;
            
            -- Criar índice para porte (frequentemente filtrado)
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_animal_porte') THEN
                CREATE INDEX idx_animal_porte ON animal(porte);
            END IF;
            
            -- Criar índice para sexo (frequentemente filtrado)
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_animal_sexo') THEN
                CREATE INDEX idx_animal_sexo ON animal(sexo);
            END IF;
            
            -- Criar índice para idade (frequentemente filtrado)
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_animal_idade') THEN
                CREATE INDEX idx_animal_idade ON animal(idade);
            END IF;
            
            -- Criar índice para produtos (frequentemente listados)
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_produtos_categoria') THEN
                CREATE INDEX idx_produtos_categoria ON produtos(categoria);
            END IF;
        END
        $$;
    """)
    
    # 2. Criar view materializada para animais disponíveis (consulta frequente)
    cur.execute("""
        DO $$
        BEGIN
            -- Verificar se a view materializada já existe
            IF NOT EXISTS (
                SELECT 1 FROM pg_matviews WHERE matviewname = 'view_animais_disponiveis'
            ) THEN
                -- Criar a view materializada
                CREATE MATERIALIZED VIEW view_animais_disponiveis AS
                SELECT id_animal, nome, idade, porte, tipo, sexo, descricao, imagem
                FROM animal
                WHERE status = 'disponivel'
                ORDER BY id_animal;
                
                -- Criar índice na view materializada para melhor desempenho
                CREATE INDEX idx_view_animais_tipo ON view_animais_disponiveis(tipo);
                CREATE INDEX idx_view_animais_porte ON view_animais_disponiveis(porte);
                CREATE INDEX idx_view_animais_sexo ON view_animais_disponiveis(sexo);
            END IF;
        END
        $$;
    """)
    
    # 3. Criar view materializada para produtos em destaque (se existir um campo destaque)
    cur.execute("""
        DO $$
        BEGIN
            -- Verificar se a view materializada já existe
            IF NOT EXISTS (
                SELECT 1 FROM pg_matviews WHERE matviewname = 'view_produtos_catalogo'
            ) THEN
                -- Criar a view materializada
                CREATE MATERIALIZED VIEW view_produtos_catalogo AS
                SELECT id_produto, nome, categoria, preco, descricao, imagem
                FROM produtos
                WHERE estoque > 0
                ORDER BY id_produto;
                
                -- Criar índice na view materializada
                CREATE INDEX idx_view_produtos_categoria ON view_produtos_catalogo(categoria);
            END IF;
        END
        $$;
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# Função para atualizar views materializadas
def refresh_materialized_views():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("REFRESH MATERIALIZED VIEW view_animais_disponiveis")
    cur.execute("REFRESH MATERIALIZED VIEW view_produtos_catalogo")
    conn.commit()
    cur.close()
    conn.close()

# Remover o decorador e função que usava before_first_request
#@app.before_first_request
#def before_first_request():
#    setup_database_optimizations()

# Página inicial - Usando view materializada e cache
@app.route('/')
@cache.cached(timeout=60, query_string=True)  # Cache por 60 segundos com variação por query string
def index():
    porte = request.args.get('porte')
    tipo = request.args.get('tipo')
    idade = request.args.get('idade')
    sexo = request.args.get('sexo')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Usar a view materializada se não houver filtros
    if not any([porte, tipo, idade, sexo]):
        cur.execute("SELECT * FROM view_animais_disponiveis")
        animais = cur.fetchall()
    else:
        # Se houver filtros, usar a consulta original com índices
        query = "SELECT id_animal, nome, idade, porte, tipo, sexo, descricao, imagem FROM animal WHERE status = 'disponivel'"
        params = []
        
        if porte:
            query += " AND porte = %s"
            params.append(porte)
        if tipo:
            query += " AND tipo = %s"
            params.append(tipo)
        if idade:
            if idade == 'filhote':
                query += " AND idade <= 1"
            elif idade == 'adulto':
                query += " AND idade > 1 AND idade <= 7"
            elif idade == 'idoso':
                query += " AND idade > 7"
        if sexo:
            query += " AND sexo = %s"
            params.append(sexo)
        
        cur.execute(query, params)
        animais = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('index.html', animais=animais)

# Página de detalhes do animal - Com cache
@app.route('/pet/<int:animal_id>')
@cache.cached(timeout=300)  # Cache por 5 minutos
def pet_detalhes(animal_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_animal, nome, idade, porte, tipo, sexo, descricao, imagem FROM animal WHERE id_animal = %s", (animal_id,))
    animal = cur.fetchone()
    cur.close()
    conn.close()
    
    if animal is None:
        flash('Animal não encontrado', 'error')
        return redirect(url_for('index'))
    
    return render_template('pet_detalhes.html', animal=animal)

# Rota para adotar um animal - Invalida cache
@app.route('/adotar/<int:animal_id>')
def adotar(animal_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE animal SET status = 'adotado' WHERE id_animal = %s", (animal_id,))
    
    # Neste exemplo estamos usando um ID fixo de usuário (1), em uma aplicação real
    # isso viria da sessão do usuário após login
    cur.execute("INSERT INTO adocao (id_usuario, id_animal, data_adocao) VALUES (1, %s, CURRENT_TIMESTAMP)", (animal_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Atualizar a view materializada após alteração de status
    refresh_materialized_views()
    
    # Invalidar caches relacionados
    cache.delete_memoized(index)
    cache.delete_memoized(todos_pets)
    
    flash('Parabéns! Você adotou um novo amigo.', 'success')
    return redirect(url_for('confirmacao'))

@app.route('/confirmacao')
def confirmacao():
    return render_template('confirmacao.html')

@app.route('/produtos')
@cache.cached(timeout=120)  # Cache por 2 minutos
def produtos():
    conn = get_db_connection()
    cur = conn.cursor()
    # Usar view materializada para produtos
    cur.execute("SELECT id_produto, nome, preco, descricao, imagem FROM view_produtos_catalogo")
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('produtos.html', produtos=produtos)

# Login de administrador (simplificado)
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Em uma aplicação real, você verificaria credenciais no banco de dados e usaria hashing
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciais inválidas', 'error')
    
    return render_template('admin.html')

# Verificar se o administrador está logado
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Acesso restrito. Faça login para continuar.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Dashboard do administrador
@app.route('/admin')
#@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

# CRUD para animais
@app.route('/admin/animais')
#@admin_required
def admin_animais():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_animal, nome, idade, porte, tipo, sexo, status, descricao FROM animal ORDER BY id_animal")
    animais = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('admin_animais.html', animais=animais)

# Adicionar animal
@app.route('/admin/animais/adicionar', methods=['GET', 'POST'])
#@admin_required
def adicionar_animal():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        porte = request.form['porte']
        tipo = request.form['tipo']
        sexo = request.form['sexo']
        descricao = request.form['descricao']
        status = request.form['status']
        
        # Processar upload de imagem
        imagem_path = None
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                imagem_path = 'uploads/' + filename
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO animal (nome, idade, porte, tipo, sexo, descricao, status, imagem) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_animal",
            (nome, idade, porte, tipo, sexo, descricao, status, imagem_path)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        # Atualizar views materializadas após adicionar animal
        refresh_materialized_views()
        
        # Invalidar caches relacionados
        cache.delete_memoized(index)
        cache.delete_memoized(todos_pets)
        
        flash(f'Animal {nome} adicionado com sucesso!', 'success')
        return redirect(url_for('admin_animais'))
    
    return render_template('form_animal.html', animal=None)

# Editar animal
@app.route('/admin/animais/editar/<int:animal_id>', methods=['GET', 'POST'])
#@admin_required
def editar_animal(animal_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        porte = request.form['porte']
        tipo = request.form['tipo']
        sexo = request.form['sexo']
        descricao = request.form['descricao']
        status = request.form['status']
        
        # Obter imagem atual
        cur.execute("SELECT imagem FROM animal WHERE id_animal = %s", (animal_id,))
        current_image = cur.fetchone()[0]
        
        # Processar nova imagem, se fornecida
        imagem_path = current_image
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                imagem_path = 'uploads/' + filename
        
        cur.execute(
            "UPDATE animal SET nome = %s, idade = %s, porte = %s, tipo = %s, sexo = %s, descricao = %s, status = %s, imagem = %s WHERE id_animal = %s",
            (nome, idade, porte, tipo, sexo, descricao, status, imagem_path, animal_id)
        )
        conn.commit()
        
        # Atualizar views materializadas após editar animal
        refresh_materialized_views()
        
        # Invalidar caches específicos
        cache.delete_memoized(index)
        cache.delete_memoized(todos_pets)
        
        flash(f'Animal {nome} atualizado com sucesso!', 'success')
        return redirect(url_for('admin_animais'))
    
    # GET: Carrega informações do animal para o formulário
    cur.execute("SELECT id_animal, nome, idade, porte, tipo, sexo, descricao, status, imagem FROM animal WHERE id_animal = %s", (animal_id,))
    animal = cur.fetchone()
    cur.close()
    conn.close()
    
    if animal is None:
        flash('Animal não encontrado', 'error')
        return redirect(url_for('admin_animais'))
    
    return render_template('form_animal.html', animal=animal)

# Excluir animal
@app.route('/admin/animais/excluir/<int:animal_id>', methods=['POST'])
#@admin_required
def excluir_animal(animal_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verificar se o animal existe
    cur.execute("SELECT nome FROM animal WHERE id_animal = %s", (animal_id,))
    animal = cur.fetchone()
    
    if animal is None:
        flash('Animal não encontrado', 'error')
    else:
        # Em uma aplicação real, você verificaria se este animal está relacionado a outras tabelas
        # e realizaria exclusão em cascata ou bloquearia a exclusão conforme necessário
        try:
            cur.execute("DELETE FROM animal WHERE id_animal = %s", (animal_id,))
            conn.commit()
            
            # Atualizar views materializadas após excluir animal
            refresh_materialized_views()
            
            # Invalidar caches
            cache.delete_memoized(index)
            cache.delete_memoized(todos_pets)
            
            flash(f'Animal {animal[0]} excluído com sucesso!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Erro ao excluir animal: {str(e)}', 'error')
    
    cur.close()
    conn.close()
    return redirect(url_for('admin_animais'))

# -------------------- CRUD de PRODUTOS --------------------
# LISTAR
@app.route('/admin/produtos')
# @admin_required
def lista_produtos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT id_produto, nome, categoria,
                          preco, estoque, descricao, imagem
                   FROM produtos
                   ORDER BY id_produto""")
    produtos = cur.fetchall()
    cur.close(); conn.close()
    return render_template('lista_produtos.html', produtos=produtos)

# ADICIONAR
@app.route('/admin/produtos/adicionar', methods=['GET', 'POST'])
# @admin_required
def adicionar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        categoria = request.form['categoria']
        descricao = request.form['descricao']
        preco = request.form['preco']
        estoque = request.form['estoque']
        #destaque = request.form['destaque']

        # Processar upload de imagem
        imagem_path = None
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                imagem_path = 'uploads/' + filename

        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("""INSERT INTO produtos
                       (nome, categoria, descricao, preco, estoque, imagem)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (nome, categoria, descricao, preco, estoque, imagem_path))
        conn.commit(); cur.close(); conn.close()
        
        # Atualizar views materializadas após adicionar produto
        refresh_materialized_views()
        
        # Invalidar cache dos produtos
        cache.delete_memoized(produtos)
        
        flash(f'Produto {nome} adicionado com sucesso!', 'success')
        return redirect(url_for('lista_produtos'))

    return render_template('form_produto.html', titulo="Adicionar Produto", produto=None, action="adicionar_produto")

# EDITAR
@app.route('/admin/produtos/editar/<int:prod_id>', methods=['GET', 'POST'])
# @admin_required
def editar_produto(prod_id):
    conn = get_db_connection(); cur = conn.cursor()
    if request.method == 'POST':
        nome = request.form['nome']
        categoria = request.form['categoria']
        descricao = request.form['descricao']
        preco = request.form['preco']
        estoque = request.form['estoque']
        #destaque = request.form['destaque']

        # Obter imagem atual
        cur.execute("SELECT imagem FROM produtos WHERE id_produto=%s", (prod_id,))
        current_image = cur.fetchone()[0]

        # Processar nova imagem, se fornecida
        imagem_path = current_image
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    imagem_path = 'uploads/' + filename

        cur.execute("""UPDATE produtos
                       SET nome=%s, categoria=%s, descricao=%s, preco=%s, 
                           estoque=%s, imagem=%s
                       WHERE id_produto=%s""",
                    (nome, categoria, descricao, preco, estoque, 
                     imagem_path, prod_id))
        conn.commit()
        
        # Atualizar views materializadas após editar produto
        refresh_materialized_views()
        
        # Invalidar cache dos produtos
        cache.delete_memoized(produtos)
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('lista_produtos'))

    # GET: Carrega informações do produto para o formulário
    cur.execute("""SELECT id_produto, nome, preco, descricao, categoria, estoque,
                          imagem
                   FROM produtos WHERE id_produto=%s""", (prod_id,))
    produto = cur.fetchone(); cur.close(); conn.close()
    if not produto:
        flash('Produto não encontrado', 'error')
        return redirect(url_for('lista_produtos'))
    
    return render_template('form_produto.html', titulo="Editar Produto", produto=produto, action="editar_produto", prod_id=prod_id)

# EXCLUIR
@app.route('/admin/produtos/excluir/<int:prod_id>', methods=['POST'])
# @admin_required
def excluir_produto(prod_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT nome FROM produtos WHERE id_produto=%s", (prod_id,))
    produto = cur.fetchone()
    if not produto:
        flash('Produto não encontrado', 'error')
    else:
        try:
            cur.execute("DELETE FROM produtos WHERE id_produto=%s", (prod_id,))
            conn.commit()
            
            # Atualizar views materializadas após excluir produto
            refresh_materialized_views()
            
            # Invalidar cache dos produtos
            cache.delete_memoized(produtos)
            
            flash(f'Produto {produto[0]} excluído com sucesso!', 'success')
        except Exception as e:
            conn.rollback(); flash(f'Erro ao excluir produto: {str(e)}', 'error')
    cur.close(); conn.close()
    return redirect(url_for('lista_produtos'))


# Página de busca
@app.route('/busca')
def busca():
    # Esta rota é chamada pelo formulário de filtro na página inicial
    # Redirecionamos para index com os parâmetros de busca
    return redirect(url_for('index', 
                          tipo=request.args.get('tipo'),
                          porte=request.args.get('porte'),
                          idade=request.args.get('idade'),
                          sexo=request.args.get('sexo')))

@app.route('/todos-pets')
@cache.cached(timeout=120)  # Cache por 2 minutos
def todos_pets():
    conn = get_db_connection()
    cur = conn.cursor()
    # Usar view materializada para melhor desempenho
    cur.execute("SELECT * FROM view_animais_disponiveis")
    animais = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('todos_pets.html', animais=animais)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado com sucesso!', 'success')
    return redirect(url_for('index'))

# Função para atualizar periodicamente as views materializadas
# Em um sistema real, isso seria melhor implementado com uma tarefa agendada
def schedule_refresh():
    while True:
        time.sleep(3600)  # Atualiza a cada hora
        try:
            refresh_materialized_views()
            print("Views materializadas atualizadas com sucesso")
        except Exception as e:
            print(f"Erro ao atualizar views materializadas: {str(e)}")

# Em uma aplicação real, você usaria uma tarefa em segundo plano como Celery
# para executar essa função schedule_refresh()
# Para este exemplo, não vamos iniciar essa thread para evitar complicações

if __name__ == '__main__':
    setup_database_optimizations()  # Chama explicitamente antes de rodar o app
    app.run(debug=True)