from flask import Blueprint, render_template, request, redirect, session, url_for
from models.database import conectar_banco

login_bp = Blueprint('login', __name__)

@login_bp.route('/', methods=['GET', 'POST'])
def login():
    mensagem = ''
    if request.method == 'POST':
        tipo_usuario = request.form['tipo_usuario']
        id_usuario = request.form['id_usuario']
        senha = request.form['senha']

        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor(as_dict=True)

            if tipo_usuario == 'motorista':
                cursor.execute("SELECT * FROM Motoristas WHERE ID_Motorista = %s AND CPF = %s", (id_usuario, senha))
                usuario = cursor.fetchone()
                if usuario:
                    session['id_motorista'] = id_usuario
                    session['nome_motorista'] = usuario['Nome_Abrev'].title()
                    cursor.close()
                    conexao.close()
                    if id_usuario.upper() in ['001', '002']:
                        return redirect(url_for('supervisor.painel_supervisor'))
                    else:
                        return redirect(url_for('motorista.menu'))

            elif tipo_usuario == 'ajudante':
                cursor.execute("SELECT * FROM Ajudantes WHERE ID = %s AND Senha = %s", (id_usuario, senha))
                usuario = cursor.fetchone()
                if usuario:
                    session['id_ajudante'] = id_usuario
                    session['nome_ajudante'] = usuario['Nome'].title()
                    cursor.close()
                    conexao.close()
                    if id_usuario.upper() in ['123']:
                        return redirect(url_for('supervisor.painel_coordenador'))
                    else:
                        return redirect(url_for('ajudante.menub'))

            cursor.close()
            conexao.close()
            mensagem = 'ID ou Senha incorretos.'

    return render_template('login.html', mensagem=mensagem)
