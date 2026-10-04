from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Inicialização da aplicação Flask e do CORS
app = Flask(__name__)
CORS(app)

# Configuração da base de dados SQLite (vai criar o ficheiro nexa.db na pasta do projeto)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexa.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo da Base de Dados para os Produtos
class Produto(db.Model):
    __tablename__ = 'produtos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "preco": self.preco,
            "estoque": self.estoque
        }

# Criar as tabelas automaticamente ao iniciar a aplicação
with app.app_context():
    db.create_all()

# Rota GET: Listar todos os produtos
@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    produtos = Produto.query.all()
    return jsonify([p.to_dict() for p in produtos]), 200

# Rota POST: Adicionar um novo produto
@app.route('/api/produtos', methods=['POST'])
def add_produto():
    dados = request.get_json()
    
    if not dados or 'nome' not in dados or 'preco' not in dados:
        return jsonify({"erro": "Nome e preço são obrigatórios!"}), 400

    novo_produto = Produto(
        nome=dados.get('nome'),
        preco=dados.get('preco'),
        estoque=dados.get('estoque', 0)
    )
    
    db.session.add(novo_produto)
    db.session.commit()
    
    return jsonify({"mensagem": "Produto criado com sucesso!", "produto": novo_produto.to_dict()}), 201

# Executar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)