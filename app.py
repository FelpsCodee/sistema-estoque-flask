
#Biblioteca Flask para criar o aplicativo web
from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__) #Aqui seria a instância do aplicativo Flask é como vamos chamar o Flask para começar a codar
app.config['SECRET_KEY'] = 'senhaultramegasecreta@4312'
def init_db():
    try:
        # Conecta a um único banco de dados
        conn = sqlite3.connect('sistema_estoque.db') #conecta o bando de dados ou cria se não existir
        cursor = conn.cursor() # seria a caneta que vamos usar para escrever no banco de dados

        # Criação da tabela usuarios ( aqui nos vamos criar a tebalea de usuarios) ela vai ter os campos id, username e senha)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,           
                username TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            )
        ''')

        # Criação da tabela estoque ( aqui nos vamos criar a tebalea de estoque) ela vai ter os campos id, nome, quantidade, preco, tipo e usuario_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco REAL NOT NULL,
                tipo TEXT NOT NULL,
                usuario_id INTEGER NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        conn.commit() #aqui nos salvamos as alterações no banco de dados
        conn.close() # e aqui fechamos a conexão com ele
        print("Tabelas de usuário e estoque criadas/verificadas com sucesso em 'sistema_estoque.db'!")
    except sqlite3.Error as e: #aqui se der erro ela retorna essa mensagem de erro ao criar ou iniciar o banco
        print(f"Erro ao inicializar o banco de dados: {e}")
    
def formatar_moeda_br(valor): # faqui seria oara formatar o valor do preço para o formato brasileiro
    """
    Formata um valor numérico para o formato de moeda brasileira (Ex: R$ 1.234,56).
    """
    try:
        valor_float = float(valor)
        s_valor = f"{valor_float:,.2f}"
        s_valor = s_valor.replace(",", "TEMP_COMMA").replace(".", ",").replace("TEMP_COMMA", ".")
        return f"R$ {s_valor}"
    except (ValueError, TypeError):
        return f"R$ {valor}"

app.jinja_env.globals.update(formatar_moeda_br=formatar_moeda_br)


@app.route('/') #aqui seria a rota principal ela sempre começará por ela
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
    if 'user_id' not in session: #precisa estar logado para acessar o estoque se não redireciona para a página de login
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
    if 'user_id' not in session: #se o ususario tentar acessar a rota de remover sem estar logado ele vai ser redirecionado para a pagina de login
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
    if 'user_id' not in session: # se o usuario tentar acessar o editar_produto sem estar logado ele vai ser redirecionado para a pagina de login
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

@app.route('/sair') #rota para sair do sistema
def sair():
    session.pop('user_id', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))


@app.route('/meucriador') #rota para a página do criador
def criador():
    return render_template('others.html')

#  este bloco é o "ligar" e "preparar" do aplicativo, garantindo que ele só faça isso quando for o programa principal em execução.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) #significa que o site pode ser acessado de qualquer computador
    app.run(host='0.0.0.0', port=port, debug=False)  #Essa é a linha que FAZ O SITE LIGAR e ficar disponível pra todo mundo acessar
