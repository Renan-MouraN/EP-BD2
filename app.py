from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

def get_db_connection():
    dsn = "dbname=petmatch user=postgres password=senha host=localhost port=5432"
    conn = psycopg2.connect(dsn)
    conn.set_client_encoding('UTF8')
    return conn

@app.route('/')
def index():
    porte = request.args.get('porte')
    conn = get_db_connection()
    cur = conn.cursor()
    if porte:
        cur.execute("SELECT id_animal, nome, idade, porte, descricao FROM animal WHERE status = 'disponivel' AND porte = %s", (porte,))
    else:
        cur.execute("SELECT id_animal, nome, idade, porte, descricao FROM animal WHERE status = 'disponivel'")
    animais = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', animais=animais)

@app.route('/adotar/<int:animal_id>')
def adotar(animal_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE animal SET status = 'adotado' WHERE id_animal = %s", (animal_id,))
    cur.execute("INSERT INTO adocao (id_usuario, id_animal) VALUES (1, %s)", (animal_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('confirmacao'))

@app.route('/confirmacao')
def confirmacao():
    return render_template('confirmacao.html')

@app.route('/produtos')
def produtos():
    return render_template('produtos.html')


if __name__ == '__main__':
    app.run(debug=True)
