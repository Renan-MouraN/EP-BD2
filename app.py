from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from werkzeug.utils import secure_filename
from functools import wraps


app = Flask(__name__)
app.secret_key = 'patacerta_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

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

# Página inicial
@app.route('/')
def index():
    porte = request.args.get('porte')
    tipo = request.args.get('tipo')
    idade = request.args.get('idade')
    sexo = request.args.get('sexo')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
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

# Página de detalhes do animal
@app.route('/pet/<int:animal_id>')
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

# Rota para adotar um animal
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
    
    flash('Parabéns! Você adotou um novo amigo.', 'success')
    return redirect(url_for('confirmacao'))

@app.route('/confirmacao')
def confirmacao():
    return render_template('confirmacao.html')

@app.route('/produtos')
def produtos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_produto, nome, preco, descricao, imagem FROM produtos")
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
        conn.commit(); flash('Produto atualizado com sucesso!', 'success')
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
            conn.commit(); flash(f'Produto {produto[0]} excluído com sucesso!', 'success')
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
def todos_pets():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_animal, nome, idade, porte, tipo, sexo, descricao, imagem FROM animal WHERE status = 'disponivel' ORDER BY id_animal")
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

if __name__ == '__main__':
    app.run(debug=True)