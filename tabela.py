import sqlite3


conn_usuarios = sqlite3.connect('usuarios.db')
cursor_usuarios = conn_usuarios.cursor()


cursor_usuarios.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL
)
''')

conn_usuarios.commit()
conn_usuarios.close() 


conn_estoque = sqlite3.connect('estoque.db')
cursor_estoque = conn_estoque.cursor()


cursor_estoque.execute('''
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

conn_estoque.commit()
conn_estoque.close() 

print("Tabelas de usuario e estoque criadas com sucesso!")
