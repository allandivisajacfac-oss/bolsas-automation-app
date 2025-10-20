from automacao_cotacoes import app, db, User
with app.app_context():
    if User.query.filter_by(username='admin').first():
        print('Usuário admin já existe.')
    else:
        u = User(username='admin')
        u.set_password('SenhaForte123!')
        u.is_admin = True
        db.session.add(u)
        db.session.commit()
        print('Usuário admin criado: admin / SenhaForte123!')
