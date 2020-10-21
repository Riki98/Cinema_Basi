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
engine = create_engine('postgresql+psycopg2://postgres:12358@localhost:5432/CinemaBasi', echo=True)
# engine = create_engine('postgresql+psycopg2://postgres:1599@localhost:5432/cinema_basi')

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
              Column('identificativo', Integer),
              Column('password', String)
              )

sala = Table('sala', metadata,
             Column('idsala', Integer, primary_key=True),
             Column('numposti', Integer),
             Column('is3d', Boolean)
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

registafilm = Table('registafilm', metadata,
                    Column('idregista', Integer, foreign_key=True),
                    Column('idfilm', Integer, foreign_key=True)
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


#users = []
#queryUser = select([utente.c.idutente])
#users = conn.execute(queryUser)
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
    if isinstance(obj, datetime.date):  # data
        return obj.isoformat()
    elif isinstance(obj, datetime.time):  # ora
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


# pagina principale per utenti loggati e non
@app.route('/', methods=['GET'])
def home_page():
    films = conn.execute("select * from film")
    #films = conn.execute(select([film.c.titolo]).select_from(film))
    return render_template('index.html', movies=films)


# ajax richiesta giorni per film
@app.route('/selectday', methods=['POST'])
def selectday():
    movie = {}
    movie['title'] = request.json['title']
    queryData = select(distinct(proiezione.c.data)).select_from(film).join(proiezione, film.c.idfilm == proiezione.c.idfilm).where(film.c.titolo == bindparam("titoloFilm"))
    data = conn.execute(queryData, titoloFilm=movie['title'])
    ##data = conn.execute(
        #"select distinct proiezione.data from film inner join proiezione on film.idfilm=proiezione.idfilm where film.titolo='" +
        #movie['title'] + "'")
    return json.dumps([dict(r) for r in data], default=alchemyencoder)


# ajax richiesta orari per film e giorno
@app.route('/selectime', methods=['POST'])
def selectime():
    movie = {}
    movie['title'] = request.json['title']
    movie['date'] = request.json['date']
    queryData = select(distinct(proiezione.c.orario)).select_from(film).\
        join(proiezione, film.c.idfilm == proiezione.c.idfilm).\
        where(proiezione.c.data == bindparam("dataFilm")).and_(film.c.titolo == bindparam("titoloFilm"))
    time = conn.execute(queryData, dataFilm=movie['date'], titoloFilm=movie['title'])
    #time = conn.execute(
        #"select proiezione.orario from film inner join proiezione on film.idfilm=proiezione.idfilm where proiezione.data='" +
        #movie['date'] + "' and film.titolo='" + movie['title'] + "'")
    return json.dumps([dict(r) for r in time], default=alchemyencoder)

@app.route('/film/<idFilm>', methods=['GET'])
@login_required
def film(idFilm):
    #query a db per recuperare entità film con id idFilm
    queryFilm = select(film).where(film.c.idfilm == bindparam("idFilmRecuperato"))
    filmPage = conn.execute(queryFilm, idFilmRecuperato=idFilm)
    #film = conn.execute("select * from film where idfilm =" + idFilm).fetchone()
    queryProiezioni = select(proiezione).where(film.c.idfilm == bindparam("idProiezioneRecuperato"))
    proiezioni = conn.execute(queryProiezioni, idProiezioneRecuperato=idFilm)
    #proiezioni = conn.execute("select * from proiezione where proiezione.idfilm =" + idFilm)

    return render_template('base_film.html', movie=filmPage, proiezioni=proiezioni)



# render alla pagina di prenotazione dei biglietti
@app.route('/prenotazione/<idProiezione>', methods=['GET'])
@login_required
def prenotazione(idProiezione):
    #movie = {}
    #movie['title'] = request.json['title']
    #movie['date'] = request.json['date']
    #movie['time'] = request.json['time']
    #print(movie)

    queryProiezione = select([proiezione]).where(proiezione.c.idproiezione == bindparam("idProiezioniRichieste"))
    proiezioni = conn.execute(queryProiezione, idProiezioniRichieste=idProiezione).fetchone()
    #proiezione = conn.execute("select * from proiezione where idproiezione="+idProiezione).fetchone()

    print(proiezioni.idfilm)

    #film = conn.execute("select * from film where idfilm=" + str(proiezione.idfilm)).fetchone()
    queryFilmToBeBooked = select([film]).where(film.c.idfilm == bindparam("idFilmProiezione"))
    filmToBeBooked = conn.execute(queryFilmToBeBooked, idFilmProiezione=str(proiezione.c.idfilm))

    querySeats = select([sala]).where(sala.c.idsala == bindparam("selezionePosti"))
    seats = conn.execute(querySeats, selezionePosti=str(proiezione.c.idsala))
    #sala = conn.execute("select * from sala where idsala=" + str(proiezione.idsala)).fetchone()

    riga = seats.numfila
    colonna = seats.numcolonne
    #biglietti = conn.execute("select riga,colonna from biglietti where idproiezione="+idProiezione).fetchone()
    #righe = conn.execute(
    #    "select sala.numrighe FROM sala INNER JOIN proiezione INNER JOIN film on film.idfilm=proiezione.idfilm on proiezione.idsala=sala.idsala" +
    #    " WHERE film.titolo = '" + movie['title'] + "' AND proiezione.data = '" + movie[
    #        'date'] + "' AND proiezione.orario ='" + movie['time'] + "'")
    #colonne = conn.execute(
     #   "select sala.numcolonne FROM sala inner join proiezione INNER JOIN film on film.idfilm=proiezione.idfilm on proiezione.idsala=sala.idsala" +
     #   " WHERE film.titolo = '" + movie['title'] + "' AND proiezione.data = '" + movie[
    #        'date'] + "' AND proiezione.orario ='" + movie['time'] + "'")
    return render_template('prenotazione.html', movie=filmToBeBooked, proiezione= proiezione, riga=riga, colonna=colonna)#title=movie['title'], date=movie['date'], time=movie['time'] )
    #         default=alchemyencoder          posti=righe, column=colonne,


@app.route('/acquista/<idProiezione>', methods=['POST'])
@login_required
def do_prenotazione(idProiezione):

    queryDbDirector = select([persona.c.idpersona, persona.c.nomecognome]). \
        where(persona.c.nomecognome == bindparam('nomeRegista'))
    dbDirector = conn.execute(queryDbDirector, nomeRegista=director)  # eseguo la ricerca


    posto = (request.form)

    queryidSala = select([sala.c.idsala]) .\
        where(sala.c.idproiezione==idProiezione)
    idSala = conn.execute(queryidSala)
    queryIdPosto = select([posto.c.idposto]) .\
        where(posto.c.numero==posto[1] and (posto.c.fila==posto[0]) and (posto.c.idsala==idSala))
    idPosto = conn.execute(queryIdPosto)
    idUtente = user.get_id()

    # sto finendo ioo
    conn.execute(insreg, [
        {
            'idproiezione': idProiezione, 'idposto': idPosto,
            'idutente': idUtente
        }
    ])
    #insert nuovi biglietti

    ##prepari dati a vista acquista
    #ritorni vista acquista

    return 0


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    user = None
    if request.method == 'POST':
        form_email = str(request.form['mailLogin'])
        form_passw = str(request.form['passwordLogin'])
        id_admin = form_email.split('@')
        if id_admin[0].isdecimal():
            print("Welcome admin?")
            admins = conn.execute(select([admin.c.identificativo]).where(admin.c.email == form_email)).fetchone()
            adminQuery = select([admin.c.identificativo, admin.c.password]).\
                where(and_(admin.c.identificativo == bindparam('adminId'), admin.c.password == bindparam('adminPassword')))
            adminCredentials = conn.execute(adminQuery, adminId=id_admin[0], adminPassword=form_passw).fetchone()[0]
            if adminCredentials is None:
                return home_page()
            else:
                return render_template('admin_logged.html', idAdminLogged = id_admin[0])

        user = conn.execute(select([utente]).where(utente.c.email == form_email)).fetchone()

    if user is None:
        return home_page()
    real_id = int(user[1])
    real_email = str(user[0]).strip()
    real_pwd = str(user[2]).strip()

    if form_passw == real_pwd:
        user.authenticated = True
        login_user(User(real_id, real_email, real_pwd))  # appoggio a flask_login
        active_users.append(real_id)
        print("Logged in successfully.")
        filmLogin = select([film.c.titolo])
        films = conn.execute(filmLogin)

    return home_page()


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    id = conn.execute(select([func.max(utente.c.idutente)]))
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
    user.authenticated = True
    login_user(User(myid, email, passwordreg))  # appoggio a flask_login
    active_users.append(real_id)
    return home_logged()


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    user = current_user
    user.authenticated = False
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

    idFilmDB = select([func.max(film.c.idfilm)]) + 1
    # Controllo se il film sia già presente nel database
    isThereQuery = select([film.c.titolo, film.c.anno]).\
                      where(and_(film.c.anno == bindparam('annoFilm'), film.c.titolo == bindparam('titoloFilm')))
    isThere = conn.execute(isThereQuery, titoloFilm=newTitle, annoFilm=newYearPubb).fetchone()[0]

    if isThere is None:
        # QUERY DI AGGIUNTA DI UN FILM
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
        queryDbDirector = select([persona.c.idpersona, persona.c.nomecognome]).\
                            where(persona.c.nomecognome == bindparam('nomeRegista'))
        dbDirector = conn.execute(queryDbDirector, nomeRegista=director) #eseguo la ricerca

        insNewDirectorMovie = registafilm.insert()
        if dbDirector is not None: #se è già presente
            conn.execute(insNewDirectorMovie, [
                {
                    'idregista': dbDirector[0], 'idfilm': idFilmDB
                }
            ])
        else: #se invece non c'è

            #inserisco prima la persona
            queryMaxPersonaDB = select([func.max(persona.c.idpersona)])
            idMaxPersonaDB = conn.execute(queryMaxPersonaDB).fetchone()[0] + 1
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
        queryDbActor = select([persona.c.idpersona, persona.c.nomecognome]).\
            where(persona.c.nomecognome == bindparam('nomeAttore'))
        dbActors = conn.execute(queryDbActor, nomeAttore=actor)  # eseguo la ricerca
        insNewActorsMovie = registafilm.insert()
        if dbActors is not None:  # se è già presente
            conn.execute(insNewActorsMovie, [
                {
                    'idattore': dbActors[0], 'idfilm': idFilmDB
                }
            ])
        else:  # se invece non c'è
            # inserisco prima la persona
            idMaxPersonaDB = select([func.max(persona.c.idpersona)])
            idNewPersona = conn.execute(idMaxPersonaDB).fetchone()[0] + 1
            insNewActors = persona.insert()
            conn.execute(insNewActors, [
                {
                    'idpersona': idNewPersona, 'nomecognome': actor
                }
            ])
            # poi aggiungo il collegamento ad attorefilm
            conn.execute(insNewActorsMovie, [
                {
                    'idattore': idNewPersona, 'idfilm': idFilmDB
                }
            ])

    ###### SALVATAGGIO DELLA LOCANDINA
    image = request.files["image"]

    image.save('.\static\img\Locandine', image)

    print("Immagine salvata")

    return render_template("admin_page.html")



@app.route('/admin_page')
@login_required
def load_admin():
    redirect(url_for('admin_page.html'))


if __name__ == '__main__':
    app.run(debug=True)
