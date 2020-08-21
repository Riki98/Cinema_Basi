# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, BooleanField, SubmitField
# from wtforms.validators import DataRequired
from flask import Flask, render_template, request, json, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from sqlalchemy import *
import datetime
import decimal

app = Flask(__name__)

# ATTENZIONE!!! DA CAMBIARE A SECONDA DEL NOME UTENTE E NOME DB IN POSTGRES
#engine = create_engine('postgres://postgres:12358@localhost:5432/Cinema_Basi', echo=True)
engine = create_engine('postgresql+psycopg2://batman@localhost:5432/cinema_basi')

app.config['SECRET_KEY'] = 'secretcinemaucimg'
#login_manager = LoginManager()
#login_manager.init_app(app)

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

proiezioni = Table('proiezioni', metadata,
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

#non mi ricordo a cosa serva questa tabella
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


class User(UserMixin):
    def __init__(self, id, email, pwd):
        self.id = id
        self.email = email
        self.pwd = pwd


@login_manager.user_loader
def load_user(user_id):
    user = conn.execute(select([utente]).where(utente.c.idutente == user_id)).fetchone()
    if user is None:
        return None
    else:
        real_id     = int(user[1])
        real_email  = str(user[0]).strip()
        real_pwd    = str(user[2]).strip()
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


# pagina principale per utenti non loggati
@app.route('/')
def home_page():
    films = conn.execute("select titolo from film")
    # if user
    return render_template('index.html', movies=films, loginbtn=true)


# stessa pagina ma per utente loggato, permette nuove funzioni
@app.route('/logged-bad-rendering')
@login_required
def home_logged():
    films = conn.execute("select titolo from film")
    return render_template('index.html', movies=films, loginbtn=false)


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


# qua non va niente
@app.route('/prenotazione', methods=['POST'])
def prenotazione():
    movie = {}
    movie['title'] = request.json['title']
    movie['date'] = request.json['date']
    movie['time'] = request.json['time']
    return render_template('prenotazione.html', title=movie['title'], date=movie['date'], time=movie['time'])


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_email = str(request.form['mailLogin'])
        form_passw = str(request.form['passwordLogin'])

        user = conn.execute(select([utente]).where(utente.c.email == form_email)).fetchone()
        if user is None:
            return redirect(url_for("home_page"))

        real_id     = int(user[1])
        real_email  = str(user[0]).strip()
        real_pwd    = str(user[2]).strip()

        if form_passw == real_pwd:
            login_user(User(real_id, real_email, real_pwd))
            return redirect(url_for("home_logged"))
        else:
            return redirect(url_for("home_page"))
    else:
        return render_template('index.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    id = conn.execute("select MAX(idutente) from utente")

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
    films = conn.execute("select titolo from film")
    log = true
    return render_template('index.html', movies=films, logged=log)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template("index.html")


if __name__ == '__main__':
    app.run()
