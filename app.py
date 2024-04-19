from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///provas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'o_segredo_do_calice_e_'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Tabela de associação para a relação muitos-para-muitos
aluno_cursos = db.Table('aluno_cursos',
    db.Column('aluno_id', db.Integer, db.ForeignKey('aluno.id', ondelete='CASCADE'), primary_key=True),
    db.Column('curso_id', db.Integer, db.ForeignKey('curso.id', ondelete='CASCADE'), primary_key=True),
    db.ForeignKeyConstraint(['aluno_id'], ['aluno.id'], name='fk_aluno_cursos_aluno_id'),
    db.ForeignKeyConstraint(['curso_id'], ['curso.id'], name='fk_aluno_cursos_curso_id')
)

class Curso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    provas = db.relationship('Prova', backref='curso', lazy=True)
    alunos = db.relationship('Aluno', secondary=aluno_cursos, back_populates='cursos')

class Aluno(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))  # Armazenará o hash da senha
    
    cursos = db.relationship('Curso', secondary='aluno_cursos', back_populates='alunos')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Prova(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id'))
    aluno_id = db.Column(db.Integer, db.ForeignKey('aluno.id'))
    data_agendada = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Não Agendada')

    aluno = db.relationship('Aluno', backref='provas_agendadas')

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Aluno': Aluno, 'Curso': Curso, 'aluno_cursos': aluno_cursos}

@login_manager.user_loader
def load_user(user_id):
    return Aluno.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        aluno = Aluno.query.filter_by(username=username).first()
        if aluno and aluno.check_password(password):
            login_user(aluno)
            return redirect(url_for('agendar'))  # Redirecione para a página inicial ou dashboard
        else:
            flash('Nome de usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    if request.method == 'POST':
        prova_id = request.form['nome']
        data_agendada = request.form['data']
        prova = Prova.query.get(prova_id)
        
        if prova and prova.curso in current_user.cursos:
            prova.data_agendada = datetime.strptime(data_agendada, '%Y-%m-%d')  # Convertendo string para data
            prova.status = 'Agendada'
            prova.aluno_id = current_user.id  # Vinculando prova ao usuário atual
            db.session.commit()
            flash('Prova agendada com sucesso!', 'success')
            return redirect(url_for('agendar'))
        else:
            flash('Prova não disponível ou você não está matriculado no curso desta prova.', 'error')
            return redirect(url_for('agendar'))

    provas = Prova.query.join(Curso).filter(Curso.id.in_([curso.id for curso in current_user.cursos])).all()
    return render_template('agendar_prova.html', provas=provas) 

@app.route('/provas_agendadas')
@login_required
def provas_agendadas():
    provas = Prova.query.filter_by(aluno_id=current_user.id, status='Agendada').all()
    if not provas:
        flash('Nenhuma prova agendada encontrada.', 'info')
    return render_template('provas_agendadas.html', provas=provas)

@app.route('/remarcar/<int:id_prova>', methods=['GET', 'POST'])
@login_required  # Garante que apenas usuários autenticados possam acessar
def remarcar(id_prova):
    prova = Prova.query.get_or_404(id_prova)  # Busca a prova ou retorna erro 404 se não encontrada

    if request.method == 'POST':
        nova_data = request.form['nova_data']
        if prova.aluno_id != current_user.id:  # Verifica se a prova pertence ao usuário logado
            flash('Você não tem permissão para modificar esta prova.', 'danger')
            return redirect(url_for('agendar'))

        # Convertendo a string da nova data em um objeto datetime
        try:
            nova_data_formatada = datetime.strptime(nova_data, '%Y-%m-%d')
            prova.data_agendada = nova_data_formatada  # Atualizando a data agendada
            db.session.commit()  # Aplica as mudanças no banco de dados
            flash('Prova reagendada com sucesso!', 'success')
        except ValueError:
            flash('Formato de data inválido. Por favor, use o formato AAAA-MM-DD.', 'error')

        return redirect(url_for('provas_agendadas'))

    return render_template('remarcar_prova.html', prova=prova)

@app.route('/cancelar/<int:id_prova>')
@login_required
def cancelar(id_prova):
    prova = Prova.query.get_or_404(id_prova)
    if prova.aluno_id == current_user.id:  # Garante que apenas o proprietário possa cancelar a prova
        prova.status = 'Cancelado'
        db.session.commit()
        flash('Prova cancelada com sucesso!', 'success')
    else:
        flash('Não autorizado a cancelar esta prova.', 'error')
    return redirect(url_for('provas_agendadas'))

@app.route('/')
def home():
    return redirect(url_for('agendar'))


if __name__ == '__main__':
    app.run(debug=True)




















# from flask import Flask, render_template, request, redirect, url_for, flash
# import sqlite3

# app = Flask(__name__)
# app.secret_key = 'o_segredo_do_calice_e_'

# def criar_bd():
#     conexao = sqlite3.connect('provas.db')
#     c = conexao.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS provas
#                  (id INTEGER PRIMARY KEY, nome TEXT, data TEXT, nota REAL, status TEXT)''')
#     conexao.commit()
#     conexao.close()

# @app.route('/agendar', methods=['GET', 'POST'])
# def agendar():
#     if request.method == 'POST':
#         nome = request.form['nome']
#         data = request.form['data']
#         conexao = sqlite3.connect('provas.db')
#         c = conexao.cursor()
#         c.execute("INSERT INTO provas (nome, data, nota, status) VALUES (?, ?, ?, ?)", 
#                   (nome, data, None, 'Agendado'))
#         conexao.commit()
#         conexao.close()
#         flash('Prova agendada com sucesso!', 'success')
#         return redirect(url_for('agendar'))
#     return render_template('agendar_prova.html')

# @app.route('/provas_agendadas')
# def provas_agendadas():
#     conexao = sqlite3.connect('provas.db')
#     c = conexao.cursor()
#     c.execute("SELECT * FROM provas WHERE status = 'Agendado'")
#     provas = c.fetchall()
#     conexao.close()
#     return render_template('provas_agendadas.html', provas=provas)

# @app.route('/remarcar/<int:id_prova>', methods=['GET', 'POST'])
# def remarcar(id_prova):
#     if request.method == 'POST':
#         nova_data = request.form['nova_data']
#         conexao = sqlite3.connect('provas.db')
#         c = conexao.cursor()
#         c.execute("UPDATE provas SET data = ? WHERE id = ?", (nova_data, id_prova))
#         conexao.commit()
#         conexao.close()
#         flash('Prova reagendada com sucesso!', 'success')
#         return redirect(url_for('agendar'))
#     return render_template('remarcar_prova.html', id_prova=id_prova)

# @app.route('/cancelar/<int:id_prova>')
# def cancelar(id_prova):
#     conexao = sqlite3.connect('provas.db')
#     c = conexao.cursor()
#     c.execute("UPDATE provas SET status = 'Cancelado' WHERE id = ?", (id_prova,))
#     conexao.commit()
#     conexao.close()
#     flash('Prova cancelada com sucesso!', 'success')
#     return redirect(url_for('provas_agendadas'))

# @app.route('/')
# def home():
#     return redirect(url_for('agendar'))

# if __name__ == '__main__':
#     criar_bd()
#     app.run(debug=True)
