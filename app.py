# HTML import
from operator import and_

import json
import flask
from flask import Flask, render_template, request, json, redirect, url_for

# DB e Users import
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from sqlalchemy import select, insert, bindparam, Boolean, Time, Date, update, Table
from sqlalchemy import Sequence
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

from urllib.parse import urlparse, urljoin
# TYPE import
import datetime
import decimal

# Security import (https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database)
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'itsreallysecret'
app.config['SECRET_KEY'] = 'secretcinemaucimg'

# ATTENZIONE!!! DA CAMBIARE A SECONDA DEL NOME UTENTE E NOME DB IN POSTGRES
engine = create_engine('postgres://postgres:12358@localhost:5432/CinemaBasi', echo=True)
# engine = create_engine('postgresql+psycopg2://postgres:1599@localhost:5432/cinema_basi')

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
             Column('paese', String),
             Column('anno', Integer),
             Column('vm', Integer),
             Column('shown', Boolean)
             )

utente = Table('utente', metadata,
               Column('email', String),
               Column('idutente', Integer, Sequence('user_id_sequence'), primary_key=True),
               Column('password', String),
               Column('nome', String),
               Column('cognome', String),
               Column('datanascita', Date),
               Column('sesso', String),
               Column('numfigli', Integer),
               Column('residenza', String),
               Column('numcell', String),
               Column('role', Integer)
               )

persona = Table('persona', metadata,
                Column('idpersona', Integer, primary_key=True),
                Column('nomecognome', String)
                )

sala = Table('sala', metadata,
             Column('idsala', Integer, primary_key=True),
             Column('numfila', Integer),
             Column('numcolonne', Integer),
             Column('is3d', Boolean)
             )

proiezione = Table('proiezione', metadata,
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

biglietto = Table('biglietto', metadata,
                  Column('idposto', Integer),
                  Column('idproiezione', Integer),
                  Column('idutente', Integer)
                  )

attorefilm = Table('attorefilm', metadata,
                   Column('idpersona', Integer, ForeignKey(persona.c.idpersona)),
                   Column('idfilm', Integer, ForeignKey(film.c.idfilm))
                   )

registafilm = Table('registafilm', metadata,
                    Column('idpersona', Integer, ForeignKey(persona.c.idpersona)),
                    Column('idfilm', Integer, ForeignKey(film.c.idfilm))
                    )

metadata.create_all(engine)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

active_users = []


class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        if self.is_authenticated() == True:
            return False
        return True

    def get_id(self):
        return self.id

    def get_role(self):
        return self.role

    def get_email(self):
        return self.email

    def __repr__(self):
        return f'<User: {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    conn = engine.connect()
    user = conn.execute(select([utente]).where(utente.c.idutente == user_id)).fetchone()
    conn.close()
    if user is None:
        return None
    else:
        real_id = int(user[1])
        real_email = str(user[0]).strip()
        real_role = user['role']
        print("LoadUser")
        print(real_email)
        return User(real_id, real_email, real_role)


# fun: permette di serializzare i dati per le conversioni json
def alchemyencoder(obj):
    if isinstance(obj, datetime.date):  # data
        return obj.isoformat()
    elif isinstance(obj, datetime.time):  # ora
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


# render alla pagina principale
@app.route('/', methods=['GET'])
def home_page():
    # apertura connessione al DB
    conn = engine.connect()
    queryFilms = select([film])
    films = conn.execute(queryFilms)
    conn.close()
    if current_user.is_authenticated:
        return render_template('login.html', movies=films)  # stessa pagina rimossa dei btn log in e register
    else:
        return render_template('index.html', movies=films)


@app.route('/film/<idFilm>', methods=['GET'])
@login_required
def base_film(idFilm):
    conn = engine.connect()
    # query a db per recuperare entità film con id idFilm
    queryFilm = select([film.c.titolo, film.c.trama, film.c.genere, film.c.is3d]).where(
        film.c.idfilm == bindparam("idFilmRecuperato"))
    filmPage = conn.execute(queryFilm, {'idFilmRecuperato': idFilm}).fetchone()

    queryProiezioni = select([proiezione.c.idproiezione, proiezione.c.data, proiezione.c.orario]).where(
        proiezione.c.idfilm == bindparam("idProiezioneRecuperato"))
    proiezioni = conn.execute(queryProiezioni, {'idProiezioneRecuperato': idFilm})

    conn.close()
    return render_template('base_film.html', movie=filmPage, spettacoli=proiezioni)


# render alla pagina di prenotazione dei biglietti
@app.route('/prenotazione/<idProiezione>', methods=['GET'])
@login_required
def prenotazione(idProiezione):
    conn = engine.connect()

    queryProiezione = select([proiezione]).where(proiezione.c.idproiezione == bindparam('idProiezioniRichieste'))
    proiezioni = conn.execute(queryProiezione, {'idProiezioniRichieste': idProiezione}).fetchone()

    queryFilmToBeBooked = select([film]).where(film.c.idfilm == bindparam('idFilmProiezione'))
    filmToBeBooked = conn.execute(queryFilmToBeBooked, {'idFilmProiezione': (proiezioni.idfilm)}).fetchone()

    querySeats = select([sala]).where(sala.c.idsala == bindparam('selezionePosti'))
    seats = conn.execute(querySeats, {'selezionePosti': (proiezioni.idsala)}).fetchone()

    riga = seats.numfila
    colonna = seats.numcolonne
    conn.close()
    return render_template('prenotazione.html', movie=filmToBeBooked, proiezione=proiezione, riga=riga, colonna=colonna)
    # default=alchemyencoder


@app.route('/acquista/<idProiezione>', methods=['POST'])
@login_required
def do_prenotazione(idProiezione):
    conn = engine.connect()
    pos = (request.form)
    print(pos)
    queryidSala = select([sala.c.idsala]). \
        where(sala.c.idproiezione == idProiezione)
    idSala = conn.execute(queryidSala)
    queryIdPosto = select([posto.c.idposto]). \
        where(posto.c.numero == pos[1] and (posto.c.fila == pos[0]) and (posto.c.idsala == idSala))
    idPosto = conn.execute(queryIdPosto)
    idUtente = current_user.get_id()

    # insert nuovi biglietti
    insreg = biglietto.insert
    conn.execute(insreg, [
        {
            'idproiezione': idProiezione, 'idposto': idPosto,
            'idutente': idUtente
        }
    ])
    ##prepari dati a vista acquista
    # ritorni vista acquista
    conn.close()
    return render_template('biglietto.html', ticket=ticket)


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = engine.connect()
    if request.method == 'POST':
        form_email = str(request.form['mailLogin'])
        form_passw = str(request.form['passwordLogin'])
        queryControlUser = select([utente]).where(
            and_(utente.c.email == bindparam('expectedEmail'), utente.c.password == bindparam('expectedPAss')))
        utente_log = conn.execute(queryControlUser, expectedEmail=form_email, expectedPAss=form_passw).fetchone()
        print(utente_log)
        conn.close()
        if utente_log is None:
            return redirect("/")  # home_page()
        else:
            print(utente_log)
            login_user(User(utente_log['idutente'], utente_log['email'], utente_log['role']))  # appoggio a flask_login
            active_users.append(utente_log)
            print("Logged in successfully.")
            if int(current_user.get_role()) == 0:
                return redirect("/")
            else:
                return redirect("/admin")
    return render_template('login.html')


@app.route('/admin')
@login_required
def admin_page():
    if current_user.role == 0:
        return redirect("/")
    else:
        print(current_user)
        conn = engine.connect()
        takenFilms = select([film]).order_by(film.c.idfilm.asc())
        queryTakenFilms = conn.execute(takenFilms).fetchall()

        query = conn.execute("select film.idfilm, film.titolo, dati.somma,dati.data from film INNER JOIN (select proiezione.idfilm, proiezione.data, sum(visite)as somma from proiezione LEFT JOIN (\
        select idproiezione, count(*) as visite from biglietto group by idproiezione) as visitatori\
        ON proiezione.idproiezione = visitatori.idproiezione group by proiezione.idfilm, proiezione.data) AS dati on film.idfilm = dati.idfilm").fetchall()
        print(query)

        # convert into JSON:
        y = json.dumps({'result': query})

        # the result is a JSON string:
        print(y)

        conn.close()

    return render_template('admin_logged.html', arrayFilms=queryTakenFilms, stats=query, adminLogged=current_user.get_email())


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = engine.connect()
    id = conn.execute(select([func.max(utente.c.idutente)]))
    myid = id.fetchone()[0] + 1

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
            'email': mailreg, 'idutente': myid,
            'password': passwordreg, 'nome': namereg,
            'cognome': surnamereg, 'datanascita': birthreg,
            'sesso': sexreg, 'numfigli': sonsreg,
            'residenza': addressreg, 'numcell': cellphonereg
        }

    ])
    conn.close()
    User.authenticated = True
    login_user(User(myid, mailreg, 0))  # appoggio a flask_login
    active_users.append(myid)
    return home_page()


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/film/unpublish/<idFilm>', methods=['GET'])
@login_required
def cancellazione(idFilm):
    conn = engine.connect()
    queryDelete = film.update().where(film.c.idfilm == bindparam("filmTaken")).values({"shown": 0})
    conn.execute(queryDelete, {'filmTaken': idFilm})
    conn.close()
    return redirect("/admin")


@app.route('/film/publish/<idFilm>', methods=['GET'])
@login_required
def ripubblicazione(idFilm):
    conn = engine.connect()
    queryDelete = film.update().where(film.c.idfilm == bindparam("filmTaken")).values({"shown": 1})
    conn.execute(queryDelete, {'filmTaken': idFilm})
    conn.close()
    return redirect("/admin")


@app.route('/film/update/<idFilm>', methods=['GET'])
@login_required
def updateFilm(idFilm):
    conn = engine.connect()
    queryDelete = film.update().where(film.c.idfilm == bindparam("filmTaken")).values({"shown": 1})
    conn.execute(queryDelete, {'filmTaken': idFilm})
    print("Ciaoooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo")
    conn.close()
    return redirect("/admin")


def stas():
    conn = engine.connect()
    queryTicketsSold = select([])
    # biglietti per mese
    # select proiezione.idfilm, proiezione.data, sum(visite) from proiezione LEFT JOIN (


# select idproiezione, count(*) as visite from biglietto group by idproiezione) as visitatori
# ON proiezione.idproiezione = visitatori.idproiezione group by proiezione.idfilm, proiezione.data
# genere più visto nel tempo
# numero posti prenotati su posti disponibili
# film più guardato


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

    conn = engine.connect()

    idFilmDB = select([func.max(film.c.idfilm)]) + 1
    # Controllo se il film sia già presente nel database
    isThereQuery = select([film.c.titolo, film.c.anno]). \
        where(and_(film.c.anno == bindparam('annoFilm'), film.c.titolo == bindparam('titoloFilm')))
    isThere = conn.execute(isThereQuery, {'titoloFilm': newTitle, 'annoFilm': newYearPubb}).fetchone()[0]

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
        queryDbDirector = select([persona.c.idpersona, persona.c.nomecognome]). \
            where(persona.c.nomecognome == bindparam('nomeRegista'))
        dbDirector = conn.execute(queryDbDirector, {'nomeRegista': director})  # eseguo la ricerca

        insNewDirectorMovie = registafilm.insert()
        if dbDirector is not None:  # se è già presente
            conn.execute(insNewDirectorMovie, [
                {
                    'idregista': dbDirector[0], 'idfilm': idFilmDB
                }
            ])
        else:  # se invece non c'è

            # inserisco prima la persona
            queryMaxPersonaDB = select([func.max(persona.c.idpersona)])
            idMaxPersonaDB = conn.execute(queryMaxPersonaDB).fetchone()[0] + 1
            insNewDirector = persona.insert()
            conn.execute(insNewDirector, [
                {
                    'idpersona': idMaxPersonaDB, 'nomecognome': director
                }
            ])
            # poi aggiungo il collegamento a registafilm
            conn.execute(insNewDirectorMovie, [
                {
                    'idregista': idMaxPersonaDB, 'idfilm': idFilmDB
                }
            ])

    ############ AGGIORNAMENTO ACTOR MOVIE #############
    newActors = request.form["newActors"]
    arrayNewActors = newActors.split(', ')
    for actor in arrayNewActors:
        queryDbActor = select([persona.c.idpersona, persona.c.nomecognome]). \
            where(persona.c.nomecognome == bindparam('nomeAttore'))
        dbActors = conn.execute(queryDbActor, {'nomeAttore': actor})  # eseguo la ricerca
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

    conn.close()

    return render_template("admin_logged.html")


if __name__ == '__main__':
    app.run(debug=True)
