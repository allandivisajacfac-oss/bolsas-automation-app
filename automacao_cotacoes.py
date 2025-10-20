from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
import threading, time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cotacoes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Cotacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    simbolo = db.Column(db.String(10), nullable=False)
    valor = db.Column(db.Float, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dados')
def dados():
    cotacoes = Cotacao.query.all()
    return jsonify([{ 'simbolo': c.simbolo, 'valor': c.valor } for c in cotacoes])

def atualizar_cotacoes():
    while True:
        simbolos = ['AAPL', 'MSFT', 'GOOGL', 'PETR4.SA', 'VALE3.SA', 'BTC-USD', 'ETH-USD', 'USDBRL=X', 'EURBRL=X']
        for s in simbolos:
            try:
                preco = yf.Ticker(s).history(period='1d')['Close'].iloc[-1]
                c = Cotacao.query.filter_by(simbolo=s).first()
                if c:
                    c.valor = preco
                else:
                    c = Cotacao(simbolo=s, valor=preco)
                    db.session.add(c)
                db.session.commit()
            except Exception as e:
                print(f"Erro ao atualizar {s}: {e}")
        time.sleep(600)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    t = threading.Thread(target=atualizar_cotacoes, daemon=True)
    t.start()
    app.run(debug=True)
