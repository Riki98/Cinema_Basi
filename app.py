# authors Giana Corò Farhan
import flask
from flask import Flask, render_template, request, jsonify, json, url_for
# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, BooleanField, SubmitField
# from wtforms.validators import DataRequired
import decimal, datetime

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from sqlalchemy import *
from sqlalchemy.sql.functions import user

app = Flask(__name__)

#engine = create_engine('postgres://postgres:12358@localhost:5432/Cinema_Basi', echo=True)
engine = create_engine('postgresql+psycopg2://batman@localhost:5432/cinema_basi')

app.config['SECRET_KEY'] = 'secretcinemaucimg'
login_manager = LoginManager()
login_manager.init_app(app)

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
               Column('email', Integer),
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


# classe utente per flask_login
class User(UserMixin):
    def __init__(self, id, email, pwd):
        self.id = id
        self.email = email
        self.pwd = pwd

    def is_active(self):
        # Here you should write whatever the code is
        # that checks the database if your user is active
        return self.active

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

#class Date:
#    def __init__(self):
#        self.day = 0
#        self.month = 0
#        self.year = 0
#
#    def set_day(self, day):
#        self.day = day
#
#    def set_month(self, month):
#        self.month = month
#
#    def set_year(self, year):
#        self.year = year

# fun: permette di serializzare i dati per le conversioni json
def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):  # data
        return obj.isoformat()
    elif isinstance(obj, datetime.time):  # ora
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


# """dovrebbe""" restituire le info di un utente interrogando per mail
@login_manager.user_loader
def load_user(user_email):
    authconn = engine.connect()
    rs = conn.execute('select * from utente where email="' + user_email + '"')
    user = rs.fetchone()
    authconn.close()
    return User(user.id, user.email, user.pwd)


# app.config['1599']='secret'
# login_manager = LoginManager()
# login_manager.init_app(app)

# pagina principale per utenti non loggati
@app.route('/')
def home_page():
    films = conn.execute("select titolo from film")
    # if user
    return render_template('index.html', movies=films, loginbtn=true)


# stessa pagina ma per utente loggato, permette nuove funzioni
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
    # login prof

    if request.method == 'POST':
        rs = conn.execute(utente.select(text('email')).where(utente.c.email == request.form['mailLogin']))
        real_pwd = rs.fetchone()['password']
        if request.form['passwordLogin'] == real_pwd:
            login_user(load_user(request.form['mailLogin']))
            return render_template('user.html')
        else:
            return render_template('index.html')
    else:
        return render_template('index.html')


# login nostro

# maillogin = request.form["mailLogin"]
# requser = select([utente.c.email]).where(utente.c.email == maillogin)
# print(requser)
# passwordLogin = request.form["passwordLogin"]
# reqpass = select([utente.c.password]).where(utente.c.password == maillogin)
# print(reqpass)

# login_user(user)
# flask.flash('Logged in successfully')
# films = conn.execute("select titolo from film")

# if maillogin == conn.execute(requser) and passwordLogin == conn.execute(reqpass):
#  log = true
# return render_template('index.html', movies=films, logged=log)
#  else:
#   return render_template('index.html')


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
    return render_template('index.html', movies=films, logged=log);


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template("index.html")


# < td class ="sala-icon" fila="C" numero="1" color-posto="green" > < img id id src="{{ url_for('static', filename='img/armchair-green.png') }}" / >
# < img src="{{ url_for('static', filename='img/armchair.png') }}" /> </td>

if __name__ == '__main__':
    app.run()
