# Bolsas - Automação de Cotações

Instruções rápidas:

1. Criar virtualenv e ativar:
   python -m venv venv
   .\venv\Scripts\Activate.ps1

2. Instalar dependências:
   pip install -r requirements.txt

3. Copiar .env (editar se necessário):
   copy .env.example .env

4. Criar DB e seed + admin:
   python automacao_cotacoes.py  # app criará DB e seed se não existir
   python create_admin.py

5. Abrir http://127.0.0.1:5000 (login admin / SenhaForte123!)

Deploy: usar render.yaml ou docker-compose for production.
