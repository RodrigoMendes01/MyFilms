from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
import os
import mysql.connector
from urllib.parse import quote
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

databaseUser = os.getenv("DATABASE_USER")
databasePassword = os.getenv("DATABASE_PASSWORD")

# Configurações básicas
app = Flask(__name__)
app.secret_key = 'moviesDB'
bcrypt = Bcrypt()

# Configuração do banco de dados e upload
app.config['SQLALCHEMY_DATABASE_URI'] = "{SGDB}://{user}:{password}@{server}/{database}".format(
    SGDB='mysql+mysqlconnector',
    user=databaseUser,
    password=quote(databasePassword),
    server='localhost',
    database='movies',
)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

db = SQLAlchemy(app)

# Função para validar extensão de arquivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Modelos de banco de dados
class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    movies = db.relationship("Movies", backref="user", lazy=True)

class Movies(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    commentary = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    recommend = db.Column(db.Boolean, nullable=False)
    times_watched = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return '<Movie %s>' % self.name

# Funções auxiliares
def save_image(image):
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        return filename
    return None

# Rotas de usuários
@app.route("/register")
def register():
    return render_template("register.html")

@app.route('/create_user', methods=['POST'])
def create_user():
    try:
        user_name = request.form["name"]
        user_email = request.form["email"]
        user_password = request.form["password"]

        if not user_name or not user_email or not user_password:
            flash("Preencha os campos com os dados necessários", "danger")
            return redirect("/register")

        if Users.query.filter_by(email=user_email).first():
            flash("E-mail já cadastrado", "danger")
            return redirect("/register")

        hashed_password = bcrypt.generate_password_hash(user_password).decode('utf-8')
        new_user = Users(email=user_email, name=user_name, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Usuário criado com sucesso!", 'success')
        return redirect("/login")
    except Exception as e:
        print(e)
        flash("Erro ao cadastrar usuário", "danger")
        return redirect("/register")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route('/authenticate', methods=["POST"])
def authenticate():
    try:
        email = request.form["email"]
        password = request.form["password"]

        if email and password:
            user = Users.query.filter_by(email=email).first()

            if not user or not bcrypt.check_password_hash(user.password, password):
                flash("E-mail ou senha inválidos", "danger")
                return redirect("/login")

            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name

            flash("Bem-vindo(a), " + user.name + "!", "success")
            return redirect('/')
        else:
            flash("E-mail e senha são obrigatórios", "danger")
            return redirect("/login")
    except Exception as e:
        print(e)
        flash("Erro ao realizar login", "danger")
        return redirect("/login")

@app.route("/exit")
def exit():
    session.clear()
    return redirect('/login')

# Rotas de filmes
@app.route("/")
def show_movies():
    if 'user_email' not in session or 'user_id' not in session:
        return redirect("/login")

    movies_list = Movies.query.order_by(Movies.name).all()
    return render_template('home.html', movies=movies_list)

@app.route("/insert", methods=['POST'])
def create_movie():
    name = request.form['name']
    commentary = request.form['commentary']
    image = request.files['image']
    rating = request.form['rating']
    recommend = request.form['recommend'] == "1"
    times_watched = request.form['times_watched']

    filename = save_image(image)
    if not filename:
        flash("Imagem inválida", "danger")
        return redirect("/")

    new_movie = Movies(name=name, commentary=commentary, image=filename, rating=rating, 
                       recommend=recommend, times_watched=times_watched, user_id=session['user_id'])
    db.session.add(new_movie)
    db.session.commit()

    flash("Filme adicionado com sucesso!", 'success')
    return redirect("/")

@app.route('/search')
def search_movies():
    movie_name = request.args.get('search')
    if not movie_name:
        flash("Informe um nome válido!", 'danger')
        return redirect('/')

    movies = Movies.query.filter(Movies.name.like(f"%{movie_name}%")).all()
    if not movies:
        flash("Nenhum filme encontrado!", 'warning')
        return redirect('/')

    flash(f"{len(movies)} Filmes encontrados", 'success')
    return render_template('home.html', movies=movies)

@app.route('/details/<int:id>')
def movie_details(id):
    movie = Movies.query.filter_by(id=id).first()
    if not movie:
        flash("Filme não encontrado", 'danger')
        return redirect('/')
    return render_template('details.html', movieListed=movie)

@app.route("/edit", methods=['POST'])
def edit_movie():
    movie_id = request.form["id"]
    movie = Movies.query.filter_by(id=movie_id).first()

    if not movie:
        flash("Filme não encontrado", 'danger')
        return redirect('/')

    movie.name = request.form['name']
    movie.commentary = request.form['commentary']
    movie.rating = request.form['rating']
    movie.recommend = request.form['recommend'] == "1"
    movie.times_watched = request.form['times_watched']

    new_image = request.files['image']
    if new_image and allowed_file(new_image.filename):
        new_filename = save_image(new_image)
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], movie.image))
        movie.image = new_filename

    db.session.commit()
    return redirect(f"/details/{movie_id}")

@app.route("/delete/<int:id>")
def delete_movie(id):
    movie = Movies.query.filter_by(id=id).first()
    if movie:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], movie.image))
        db.session.delete(movie)
        db.session.commit()
        flash("Filme removido com sucesso", "danger")
    else:
        flash("Filme não encontrado", "danger")
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
