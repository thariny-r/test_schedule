from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'o_segredo_do_calice_e_'

def criar_bd():
    conexao = sqlite3.connect('provas.db')
    c = conexao.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS provas
                 (id INTEGER PRIMARY KEY, nome TEXT, data TEXT, nota REAL, status TEXT)''')
    conexao.commit()
    conexao.close()

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if request.method == 'POST':
        nome = request.form['nome']
        data = request.form['data']
        conexao = sqlite3.connect('provas.db')
        c = conexao.cursor()
        c.execute("INSERT INTO provas (nome, data, nota, status) VALUES (?, ?, ?, ?)", 
                  (nome, data, None, 'Agendado'))
        conexao.commit()
        conexao.close()
        flash('Prova agendada com sucesso!', 'success')
        return redirect(url_for('agendar'))
    return render_template('agendar_prova.html')

@app.route('/provas_agendadas')
def provas_agendadas():
    conexao = sqlite3.connect('provas.db')
    c = conexao.cursor()
    c.execute("SELECT * FROM provas WHERE status = 'Agendado'")
    provas = c.fetchall()
    conexao.close()
    return render_template('provas_agendadas.html', provas=provas)

@app.route('/remarcar/<int:id_prova>', methods=['GET', 'POST'])
def remarcar(id_prova):
    if request.method == 'POST':
        nova_data = request.form['nova_data']
        conexao = sqlite3.connect('provas.db')
        c = conexao.cursor()
        c.execute("UPDATE provas SET data = ? WHERE id = ?", (nova_data, id_prova))
        conexao.commit()
        conexao.close()
        flash('Prova reagendada com sucesso!', 'success')
        return redirect(url_for('agendar'))
    return render_template('remarcar_prova.html', id_prova=id_prova)

@app.route('/cancelar/<int:id_prova>')
def cancelar(id_prova):
    conexao = sqlite3.connect('provas.db')
    c = conexao.cursor()
    c.execute("UPDATE provas SET status = 'Cancelado' WHERE id = ?", (id_prova,))
    conexao.commit()
    conexao.close()
    flash('Prova cancelada com sucesso!', 'success')
    return redirect(url_for('provas_agendadas'))

@app.route('/')
def home():
    return redirect(url_for('agendar'))

if __name__ == '__main__':
    criar_bd()
    app.run(debug=True)
