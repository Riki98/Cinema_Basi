# HTML import
import flask
from flask import Flask, render_template, request, json, redirect, url_for

# DB e Users import
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from sqlalchemy import *

from urllib.parse import urlparse, urljoin
# TYPE import
import datetime
import decimal

app = Flask(__name__)
app.secret_key = 'itsreallysecret'

# ATTENZIONE!!! DA CAMBIARE A SECONDA DEL NOME UTENTE E NOME DB IN POSTGRES
# engine = create_engine('postgres://postgres:12358@localhost:5432/Cinema_Basi', echo=True)
engine = create_engine('postgresql+psycopg2://postgres:12358@localhost:5432/Cinema_Basi')

app.config['SECRET_KEY'] = 'secretcinemaucimg'
# login_manager = LoginManager()
# login_manager.init_app(app)

metadata = MetaData()

film = Table('film', metadata,
             Column('idfilm', Integer, primary_key=True),
             Column('titolo', String),
             Column('is3d', Boolean),
             Column('genere', String),
             Column('trama', String),
             Column('datainizio', Date),
             Column('datafine', Date),
             Column('durata', Integer),
             Column('Paese', String),
             Column('Anno', Integer),
             Column('vm', Integer)
             )

utente = Table('utente', metadata,
               Column('email', String),
               Column('idutente', Integer, primary_key=True),
               Column('password', String),
               Column('nome', String),
               Column('cognome', String),
               Column('datanascita', Date),
               Column('sesso', String),
               Column('numfigli', Integer),
               Column('residenza', String),
               Column('numcell', String)
               )

admin = Table('admin', metadata,
              Column('idadmin', Integer, primary_key=True),
              Column('email', String),
              Column('password', String)
              )

sala = Table('sala', metadata,
             Column('idsala', Integer, primary_key=True),
             Column('numposti', Integer),
             Column('is3d', Boolean)
             )

registafilm = Table('registafilm', metadata,
                    Column('idregista', Integer, foreign_key=True),
                    Column('idfilm', Integer, foreign_key=True)
                    )

proiezione = Table('proiezioni', metadata,
                   Column('orario', Time),
                   Column('idsala', Integer),
                   Column('idfilm', Integer),
                   Column('idproiezione', Integer, primary_key=True),
                   Column('data', Date),
                   )

posto = Table('posto', metadata,
              Column('idposto', Integer, primary_key=True),
              Column('fila', String),
              Column('prenotato', Boolean),
              Column('idsala', Integer),
              Column('numero', Integer)
              )

# non mi ricordo a cosa serva questa tabella
persona = Table('persona', metadata,
                Column('idpersona', Integer, primary_key=True),
                Column('nomecognome', String)
                )

biglietto = Table('biglietto', metadata,
                  Column('idposto', Integer),
                  Column('idproiezione', Integer),
                  Column('idutente', Integer)
                  )

attorefilm = Table('attorefilm', metadata,
                   Column('idattore', Integer),
                   Column('idfilm', Integer)
                   )

metadata.create_all(engine)

# apertura connessione al DB
conn = engine.connect()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# class LoginForm(FlaskForm):
#    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
#  password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=30)])
#  remember = BooleanField('remember me')


# class RegisterForm(FlaskForm):
#   email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=20)])
#  username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
# password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=30)])


users = []
users = conn.execute('select idutente from utente')
active_users = []


class User(UserMixin):
    def __init__(self, id, email, pwd):
        self.id = id
        self.email = email
        self.pwd = pwd

    def is_authenticated(self):
        for identifier in users:
            if self.get_id() == identifier:
                return true
        return false

    def is_active(self):
        for identifier in active_users:
            if self.get_id() == identifier:
                return true
        return false

    def is_anonymous(self):
        if self.is_authenticated() == true:
            return true
        return false

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<User: {self.email}>'

    # users.append(User(id=1, email='antonio@gmail.com', password='password'))


@login_manager.user_loader
def load_user(user_id):
    user = conn.execute(select([utente]).where(utente.c.idutente == user_id)).fetchone()
    if user is None:
        return None
    else:
        real_id = int(user[1])
        real_email = str(user[0]).strip()
        real_pwd = str(user[2]).strip()
        print("LoadUser")
        print(real_email)
        return User(real_id, real_email, real_pwd)


# fun: permette di serializzare i dati per le conversioni json
def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):  # data
        return obj.isoformat()
    elif isinstance(obj, datetime.time):  # ora
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


# pagina principale per utenti loggati e non
@app.route('/')
def home_page():
    films = conn.execute("select titolo from film")

    return render_template('index.html', movies=films)


# stessa pagina ma per utente loggato, permette nuove funzioni
@app.route('/logged-bad-rendering')
@login_required
def home_logged():
    films = conn.execute("select titolo from film")
    return render_template('login.html', movies=films)


# ajax richiesta giorni per film
@app.route('/selectday', methods=['POST'])
def selectday():
    movie = {}
    movie['title'] = request.json['title']
    data = conn.execute(
        "select distinct proiezione.data from film inner join proiezione on film.idfilm=proiezione.idfilm where film.titolo='" +
        movie['title'] + "'")
    return json.dumps([dict(r) for r in data], default=alchemyencoder)


# ajax richiesta orari per film e giorno
@app.route('/selectime', methods=['POST'])
def selectime():
    movie = {}
    movie['title'] = request.json['title']
    movie['date'] = request.json['date']
    time = conn.execute(
        "select proiezione.orario from film inner join proiezione on film.idfilm=proiezione.idfilm where proiezione.data='" +
        movie['date'] + "' and film.titolo='" + movie['title'] + "'")
    return json.dumps([dict(r) for r in time], default=alchemyencoder)


# render alla pagina di prenotazione dei biglietti
@app.route('/prenotazione', methods=['POST'])
@login_required
def prenotazione():
    movie = {}
    movie['title'] = request.json['title']
    movie['date'] = request.json['date']
    movie['time'] = request.json['time']
    films = conn.execute("select titolo from film")
    righe = conn.execute(
        "select sala.numcolonne, sala.numrighe FROM sala INNER JOIN proiezione INNER JOIN film on film.idfilm=proiezione.idfilm on proiezione.idsala=sala.idsala" +
        " WHERE film.titolo = '" + movie['title'] + "' AND proiezione.data = '" + movie[
            'date'] + "' AND proiezione.orario ='" + movie['time'] + "'")
    colonne = conn.execute(
        "select sala.numcolonne FROM sala inner join proiezione INNER JOIN film on film.idfilm=proiezione.idfilm on proiezione.idsala=sala.idsala" +
        " WHERE film.titolo = '" + movie['title'] + "' AND proiezione.data = '" + movie[
            'date'] + "' AND proiezione.orario ='" + movie['time'] + "'")
    return render_template('prenotazione.html', movies=films, posti=righe, column=colonne, title=movie['title'],
                           date=movie['date'], time=movie['time'])
    # default=alchemyencoder


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    user = None
    if request.method == 'POST':
        form_email = str(request.form['mailLogin'])
        form_passw = str(request.form['passwordLogin'])
        if form_email.isdecimal():
            print("madafaka")

        print(form_email)
        print(form_passw)

        user = conn.execute(select([utente]).where(utente.c.email == form_email)).fetchone()

    if user is None:
        return home_page()
    real_id = int(user[1])
    real_email = str(user[0]).strip()
    real_pwd = str(user[2]).strip()

    if form_passw == real_pwd:
        login_user(User(real_id, real_email, real_pwd))  # appoggio a flask_login
        active_users.append(real_id)
        print("Logged in successfully.")
        films = conn.execute("SELECT titolo FROM film")
        return home_logged()
    else:
        return home_page()


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    id = conn.execute("SELECT MAX(idutente) FROM utente")

    myid = id.fetchone()[0]

    mailreg = request.form["emailReg"]
    passwordreg = request.form["passReg"]
    namereg = request.form["nameReg"]
    surnamereg = request.form["surnameReg"]
    addressreg = request.form["addressReg"] + " " + request.form["cityReg"] + " " + request.form["stateReg"] + " " + \
                 request.form["zipReg"]
    birthreg = request.form["birthdateReg"]
    cellphonereg = request.form["cellReg"]
    sexreg = request.form["sexReg"]
    sonsreg = request.form["nSonReg"]
    # insert into the db
    insreg = utente.insert()

    conn.execute(insreg, [
        {
            'email': mailreg, 'idutente': (myid + 1),
            'password': passwordreg, 'nome': namereg,
            'cognome': surnamereg, 'datanascita': birthreg,
            'sesso': sexreg, 'numfigli': sonsreg,
            'residenza': addressreg, 'numcell': cellphonereg
        }

    ])
    films = conn.execute("SELECT titolo FROM film")
    return render_template('index.html', movies=films);


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return home_page()


@app.route('/create_page_film', methods=['POST'])
def insert_film():

    newTitle = request.form["newTitle"]
    newGenre = request.form["newGenre"]
    is3d = request.form["is3d"]
    newPlot = request.form["newPlot"]
    newStartData = request.form["newStartData"]
    newLastData = request.form["newLastData"]
    newDuration = request.form["newDuration"]
    newCountry = request.form["newCountry"]
    newYearPubb = request.form["newYearPubb"]
    newMinAge = request.form["newMinAge"]

    # Controllo se il film sia già presente nel database
    isThereQueryWow = select([film.c.titolo, film.c.anno]).\
                      where(film.c.titolo == newTitle)
    ## DA FINIRE#####################################################################################################################################
    isThereQuery = "SELECT titolo, anno FROM film WHERE titolo = ? AND anno = ?"
    isThereQuery.setString(1, newTitle)
    isThereQuery.setString(2, newYearPubb)
    isThere = conn.execute(isThereQuery).fetchone()[0]

    if not isThere:
        # QUERY DI AGGIUNTA DI UN FILM
        idFilmDB = select([max(film.c.idfilm)]) + 1
        ## idFilmDB = conn.execute("SELECT MAX(idfilm) FROM film").fetchone()[0] + 1
        insNewFilm = film.insert()
        conn.execute(insNewFilm, [
            {
                'idfilm': idFilmDB, 'titolo': newTitle,
                'is3d': is3d, 'genere': newGenre,
                'trama': newPlot, 'datainizio': newStartData,
                'datafine': newLastData, 'durata': newDuration,
                'Paese': newCountry, 'Anno': newYearPubb,
                'vm': newMinAge
            }
        ])
        print("Film inserito")
    else:
        print("Il film esiste già")

    ############ AGGIORNAMENTO DIRECTOR MOVIE ############
    newMovDir = request.form["newMovDir"]
    arrayNewDirectors = newMovDir.split(', ')
    for director in arrayNewDirectors:
        queryDbDirector = "SELECT idpersona, nomecognome FROM persona WHERE nomecognome = '?'" #cerco se c'è il regista
        queryDbDirector.setString(1, director)
        dbDirector = conn.execute(queryDbDirector) #eseguo la ricerca
        insNewDirectorMovie = registafilm.insert()

        if len(dbDirector) != 0: #se è già presente
            conn.execute(insNewDirectorMovie, [
                {
                    'idregista': dbDirector[0], 'idfilm': idFilmDB
                }
            ])
        else: #se invece non c'è
            #inserisco prima la persona
            idMaxPersonaDB = conn.execute("SELECT MAX(idpersona) FROM persona").fetchone()[0] + 1
            insNewDirector = persona.insert()
            conn.execute(insNewDirector, [
                {
                    'idpersona': idMaxPersonaDB, 'nomecognome': director
                }
            ])
            #poi aggiungo il collegamento a registafilm
            conn.execute(insNewDirectorMovie, [
                {
                    'idregista': idMaxPersonaDB, 'idfilm': idFilmDB
                }
            ])

    ############ AGGIORNAMENTO ACTOR MOVIE #############
    newActors = request.form["newActors"]
    arrayNewActors = newMovDir.split(', ')
    for actor in arrayNewActors:
        queryDbActor = "SELECT idpersona, nomecognome FROM persona WHERE nomecognome = '?'"  # cerco se c'è l'attore
        queryDbActor.setString(1, actor)
        dbActors = conn.execute(queryDbActor)  # eseguo la ricerca
        insNewActorsMovie = registafilm.insert()
        if len(dbActors) != 0:  # se è già presente
            conn.execute(insNewActorsMovie, [
                {
                    'idregista': dbActors[0], 'idfilm': idFilmDB
                }
            ])
        else:  # se invece non c'è
            # inserisco prima la persona
            idMaxPersonaDB = conn.execute("SELECT MAX(idpersona) FROM persona").fetchone()[0] + 1
            insNewActors = persona.insert()
            conn.execute(insNewActors, [
                {
                    'idpersona': idMaxPersonaDB, 'nomecognome': actor
                }
            ])
            # poi aggiungo il collegamento ad attorefilm
            conn.execute(insNewActorsMovie, [
                {
                    'idregista': idMaxPersonaDB, 'idfilm': idFilmDB
                }
            ])

    ###### SALVATAGGIO DELLA LOCANDINA
    image = request.files["image"]

    image.save('C:\Users\Riccardo\Documents\PyCharmProjects\Cinema_Basi\templates\templates_film', image)
    print("Immagine salvata")

    return render_template("admin_page.html")


@app.route('/admin_page')
@login_required
def load_admin():
    redirect(url_for('admin_page.html'))


if __name__ == '__main__':
    app.run(debug=True)
