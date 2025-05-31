from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import locale

app = Flask(__name__)
app.config['SECRET_KEY'] = 'senhaultramegasecreta@4312'

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')


def formatar_moeda_br(valor):
    return locale.currency(valor, grouping=True, symbol=True)


app.jinja_env.globals.update(formatar_moeda_br=formatar_moeda_br)


@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, username, senha FROM usuarios WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user:
                if check_password_hash(user[2], senha):
                    session['user_id'] = user[0]
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('estoque'))
                else:
                    flash('Usuário ou senha inválidos!', 'danger')
                    return render_template('login.html')
            else:
                flash('Usuário ou senha inválidos!', 'danger')
                return render_template('login.html')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        hashed_senha = generate_password_hash(senha)

        with sqlite3.connect('usuarios.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Nome de usuário já existe. Por favor, escolha outro.', 'warning')
                return render_template('cadastro.html')

            cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (username, hashed_senha))
            conn.commit()

        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('cadastro.html')


@app.route('/estoque', methods=['GET', 'POST'])
def estoque():
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    with sqlite3.connect('estoque.db') as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            nome = request.form['nome']
            quantidade = request.form['quantidade']
            preco = request.form['preco']
            tipo = request.form['tipo']

            cursor.execute("INSERT INTO estoque (nome, quantidade, preco, tipo, usuario_id) VALUES (?, ?, ?, ?, ?)",
                           (nome, int(quantidade), float(preco), tipo, user_id))
            conn.commit()

            flash('Item adicionado com sucesso!', 'success')
            return redirect(url_for('estoque'))

        cursor.execute("SELECT id, nome, quantidade, preco, tipo FROM estoque WHERE usuario_id = ?", (user_id,))
        itens = cursor.fetchall()

    return render_template("estoque.html", itens=itens)

@app.route('/remove', methods=['POST'])
def remove():
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        item_id = request.form['item_id']
        user_id = session['user_id']

        with sqlite3.connect('estoque.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM estoque WHERE id = ? AND usuario_id = ?", (item_id, user_id))
            conn.commit()
            if cursor.rowcount == 0:
                flash('Item não encontrado ou você não tem permissão para removê-lo.', 'danger')
            else:
                flash('Item removido com sucesso!', 'success')

        return redirect(url_for('estoque'))

@app.route('/editar_produto/<int:item_id>', methods=['GET', 'POST'])
def editar_produto(item_id):
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    with sqlite3.connect('estoque.db') as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            nome = request.form['nome']
            quantidade = request.form['quantidade']
            preco = request.form['preco']
            tipo = request.form['tipo']

            cursor.execute("UPDATE estoque SET nome = ?, quantidade = ?, preco = ?, tipo = ? WHERE id = ? AND usuario_id = ?",
                           (nome, int(quantidade), float(preco), tipo, item_id, user_id))
            conn.commit()

            if cursor.rowcount == 0:
                flash('Produto não encontrado ou você não tem permissão para editá-lo.', 'danger')
            else:
                flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('estoque'))
        else:
            cursor.execute("SELECT id, nome, quantidade, preco, tipo FROM estoque WHERE id = ? AND usuario_id = ?", (item_id, user_id))
            item = cursor.fetchone()

            if item is None:
                flash('Produto não encontrado ou você não tem permissão para editá-lo.', 'danger')
                return redirect(url_for('estoque'))

    return render_template('editar_produto.html', item=item)

@app.route('/sair')
def sair():
    session.pop('user_id', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
    
