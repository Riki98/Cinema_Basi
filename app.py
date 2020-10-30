# HTML import
from operator import and_

import json
from datetime import datetime, date
from sqlite3.dbapi2 import Binary

from flask import Flask, render_template, request, json, redirect, url_for

# DB e Users import
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from sqlalchemy import select, insert, bindparam, Boolean, Time, Date, update, Table, desc, asc, distinct
from sqlalchemy import Sequence
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

import string

# TYPE import
import datetime
import decimal

from sqlalchemy.dialects.postgresql import psycopg2
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = 'itsreallysecret'
app.config['SECRET_KEY'] = 'secretcinemaucimg'

# ATTENZIONE!!! DA CAMBIARE A SECONDA DEL NOME UTENTE E NOME DB IN POSTGRES
engine = create_engine('postgres+psycopg2://postgres:12358@localhost:5432/CinemaBasi')
#engine = create_engine('postgresql+psycopg2://postgres:1599@localhost:5432/cinema_basi')

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
             #Column('img', Binary)
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
              Column('idsala', Integer),
              Column('numero', Integer)
              )

biglietto = Table('biglietto', metadata,
                  Column('idposto', Integer, ForeignKey(posto.c.idposto)),
                  Column('idproiezione', Integer, ForeignKey(proiezione.c.idproiezione)),
                  Column('idutente', Integer, ForeignKey(utente.c.idutente))
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

# class used to convert into JSON:
class Dato:
    def __init__(self, idfilm, titolo):
        self.idfilm = idfilm
        self.name = titolo
        self.data = []

    def add(self, n):
        print("Dato: visite ", n)
        self.data.append(str(n))

    def tostr(self):
        return [str(num) for num in self.data]

    def __str__(self):
        return str(self.idfilm) + " " + self.name + " " + str([str(num) for num in self.data])


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
        print("LoadUser " + real_email)
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
    oggi = date.today()
    queryFilms = select([film]).where(and_(film.c.datainizio <= oggi, film.c.datafine >= oggi))
    films = conn.execute(queryFilms)
    conn.close()
    if current_user.is_authenticated:
        return render_template('login.html', movies=films) # stessa pagina rimossa dei btn log in e register
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

    queryProiezione = select([proiezione]).where(proiezione.c.idproiezione == idProiezione)
    proiezioni = conn.execute(queryProiezione).fetchone()

    queryFilmToBeBooked = select([film]).where(film.c.idfilm == (proiezioni.idfilm))
    filmToBeBooked = conn.execute(queryFilmToBeBooked).fetchone()

    querySeats = select([sala]).where(sala.c.idsala == (proiezioni.idfilm))
    seats = conn.execute(querySeats).fetchone()

    riga = seats.numfila
    colonna = seats.numcolonne

    # select posto from posto join biglietto where b.idposto=p.idposto and b.idproiezione= "idProiezione"

    queryBiglietti = select([posto]).order_by(asc(biglietto.c.idposto)).select_from(posto.join(biglietto))\
        .where(and_(biglietto.c.idproiezione == idProiezione, biglietto.c.idposto == posto.c.idposto))
    biglietti = conn.execute(queryBiglietti).fetchall()
    posti = []

    for i in range(riga+1):
        posti.append([])
        for j in range(colonna+1):
            posti[i].append(False)

    for b in biglietti:
        posti[int(ord(b.fila)-ord('A'))][int(b.numero)] = True

    conn.close()
    return render_template('prenotazione.html', movie=filmToBeBooked, proiezione=proiezioni, riga=riga, colonna=colonna,
                           string=string, ticket=biglietti, posti=posti)
    # default=alchemyencoder

def revertAcquista(postiAcquistati, idProiezione, lastX, idUtente, idSala):
    delete = biglietto.delete()
    conn = engine.execute()
    for x in range(0, lastX-1):
        numero = postiAcquistati[x]['numero']
        fila = postiAcquistati[x]['fila']

        queryIdPosto = select([posto.c.idposto]). \
            where(and_(and_(posto.c.numero == numero, posto.c.fila == fila), (posto.c.idsala == idSala)))
        idPosto = conn.execute(queryIdPosto).fetchone()

        conn.execute(delete, [
            {
                'idproiezione': idProiezione, 'idposto': idPosto[0],
                'idutente': idUtente
            }
        ])

@app.route('/acquista', methods=['POST'])
@login_required
def acquista():
    eng = create_engine('postgresql+psycopg2://postgres:1599@localhost:5432/cinema_basi', isolation_level='REPEATABLE READ')
    conn = eng.connect()
    formPostiAcquistati = (request.form['posti'])
    # convert dictionary string to dictionary
    postiAcquistati = json.loads(formPostiAcquistati)
    idProiezione = (request.form['idproiezione'])
    queryidSala = select([proiezione.c.idsala]). \
        where(proiezione.c.idproiezione == idProiezione)
    idSala = conn.execute(queryidSala).fetchone()

    idUtente = current_user.get_id()

    for x in range(0, len(postiAcquistati)):
        numero = postiAcquistati[x]['numero']
        fila = postiAcquistati[x]['fila']
        queryIdPosto = select([posto.c.idposto]). \
            where(and_(and_(posto.c.numero == numero, posto.c.fila == fila), (posto.c.idsala == idSala[0])))
        idPosto = conn.execute(queryIdPosto).fetchone()

        # questo biglietto non dovrebbe esistere
        queryBiglietto = select([biglietto]).\
            where(and_(biglietto.c.idproiezione == idProiezione, biglietto.c.idposto == idPosto[0]))
        b = conn.execute(queryBiglietto).fetchone()
        if b is None:
            # insert nuovi biglietti
            insreg = biglietto.insert()

            conn.execute(insreg, [
                {
                    'idproiezione': idProiezione, 'idposto': idPosto[0],
                    'idutente': idUtente
                }
            ])
        else:
            conn.close()
            revertAcquista(postiAcquistati, idProiezione, x, idUtente, idSala[0])

    # prepari dati a vista acquista
    queryOrarioProiezione = select([proiezione.c.orario]). \
        where(proiezione.c.idproiezione == idProiezione)
    orarioProiezione = conn.execute(queryOrarioProiezione).fetchone()
    conn.close()
    return render_template('biglietto.html', numSala=idSala, orario=orarioProiezione, posto=postiAcquistati, len=len(postiAcquistati))

# AREA UTENTE
@app.route('/areaUtente', methods=['GET', 'POST'])
def areaUtente():
    conn = engine.connect()
    #queryBigliettiTot = select([posto.fila, posto.numero, proiezione.orario, proiezione.data, film.titolo])\
    #    .select_from(posto.join(biglietto)).select_from(biglietto.join(proiezione)).select_from(proiezione.join(film))\
    #    .where(biglietto.c.idutente == current_user.id)
    queryBigliettiTot = "select posto.fila, posto.numero, proiezione.orario, proiezione.data, film.titolo " \
                        "from posto inner join biglietto on biglietto.idPosto=posto.idPosto " \
                        "inner join proiezione on proiezione.idProiezione=biglietto.idProiezione " \
                        "inner join film on film.idFilm=proiezione.idFilm " \
                        "where biglietto.idUtente="+str(current_user.id)+";"
    biglietti = conn.execute(queryBigliettiTot).fetchall()
    for b in biglietti:
        print(b)
    conn.close()
    return render_template('areaUtente.html', biglietti=biglietti)

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
        print("admin_page " + current_user.email)
        conn = engine.connect()
        takenFilms = select([film]).order_by(film.c.idfilm.asc())
        queryTakenFilms = conn.execute(takenFilms).fetchall()

        # select([film.c.idfilm, film.c.titolo, date.data, select(func.sum(visite)).select_from(proiezione).alias("somma")])
        # somma dei biglietti divisi per film e data
        query = conn.execute("SELECT\
        film.idfilm, film.titolo, date.data, (SELECT SUM(visite) AS somma\
        FROM proiezione LEFT JOIN(\
            (SELECT COUNT(*) AS visite, biglietto.idproiezione\
        FROM biglietto GROUP BY\
        idproiezione)) AS visitatori ON\
        proiezione.idproiezione = visitatori.idproiezione WHERE\
        proiezione.idfilm = film.idfilm AND proiezione.data = date.data)\
        FROM film,\
        (SELECT DISTINCT proiezione.data FROM proiezione) AS date ORDER BY\
        film.idfilm, date.data\
        ")
        # print(query)
        # query di divisione dei giorni per ogni proiezione
        giorni = conn.execute(select([distinct(proiezione.c.data)]).order_by(proiezione.c.data)).fetchall()

        array = []
        lastId = -1
        for row in query:
            if (row.idfilm > lastId):
                d = Dato(row.idfilm, row.titolo)
                d.add(row.somma)
                array.append(d)
                lastId = row.idfilm
            else:
                (array[len(array) - 1]).add(row.somma)

        stats = json.dumps([dato.__dict__ for dato in array])
        giorni = json.dumps([giorno[0].strftime('%m/%d/%Y') for giorno in giorni])

        conn.close()

        return render_template('admin_logged.html', arrayFilms=queryTakenFilms, stats=stats,
                               adminLogged=current_user.get_email(), giorni=giorni)


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


@app.route('/film/update/<idFilm>', methods=['GET', 'POST'])
@login_required
def updateFilm(idFilm):
    print("updateFilm")
    inputTitle = request.form["inputTitle" + idFilm]
    inputGenre = request.form["inputGenre" + idFilm]
    if request.form["input3d" + idFilm] == 'True':
        input3d = True
        print("DC")
    else:
        input3d = False
    inputPlot = request.form["inputPlot" + idFilm]
    inputStartData = request.form["inputStartDate" + idFilm]
    inputEndData = request.form["inputEndDate" + idFilm]
    inputDuration = request.form["inputDuration" + idFilm]
    inputCountry = request.form["inputCountry" + idFilm]
    inputYearPubb = request.form["inputYear" + idFilm]
    if request.form["inputVM" + idFilm] == 'True':
        inputMinAge = True
        print("FALZO")
    else:
        inputMinAge = False
        print("VERO")
    print(inputMinAge)
    eng = create_engine('postgres+psycopg2://postgres:12358@localhost:5432/CinemaBasi',
                        isolation_level='REPEATABLE READ')
    conn = eng.connect()
    queryUpdate = update(film). \
        where(film.c.idfilm == bindparam("expectedFilm")).values(titolo=bindparam("newInputTitle"),
                                                                 genere=bindparam("newInputGenre"),
                                                                 is3d=bindparam("newInput3d"),
                                                                 trama=bindparam("newInputPlot"),
                                                                 datainizio=bindparam("newInputStartDate"),
                                                                 datafine=bindparam("newInputEndDate"),
                                                                 durata=bindparam("newInputDuration"),
                                                                 paese=bindparam("newInputCountry"),
                                                                 anno=bindparam("newInputYear"),
                                                                 vm=bindparam("newInputVm"))
    conn.execute(queryUpdate, expectedFilm=idFilm, newInputTitle=inputTitle, newInputGenre=inputGenre,
                 newInput3d=input3d, newInputPlot=inputPlot,
                 newInputStartDate=inputStartData, newInputEndDate=inputEndData, newInputDuration=inputDuration,
                 newInputCountry=inputCountry,
                 newInputYear=inputYearPubb, newInputVm=inputMinAge)
    conn.close()
    return redirect("/admin")


def stats():
    conn = engine.connect()
    queryTicketsSold = select([])
    # biglietti per mese
    # select proiezione.idfilm, proiezione.data, sum(visite) from proiezione LEFT JOIN (

    # select idproiezione, count(*) as visite from biglietto group by idproiezione) as visitatori
    # ON proiezione.idproiezione = visitatori.idproiezione group by proiezione.idfilm, proiezione.data
    # genere più visto nel tempo
    # numero posti prenotati su posti disponibili
    # film più guardato


@app.route('/film/insert', methods=['GET', 'POST'])
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
    newImage = request.files["newImage"]
    newMovDir = request.form["newMovDir"]
    newActors = request.form["newActors"]

    print(newTitle + " -> titolo")
    print(newGenre + "-> genere")
    print(is3d + "-> 3D")
    print(newPlot + "-> trama")
    print(newStartData + "-> data inizio")
    print(newLastData + "-> data fine")
    print(newDuration + "-> durata")
    print(newCountry + "-> paese")
    print(newYearPubb + "-> anno")
    print(newMinAge + "-> vm")
    print(newImage + "-> img")

    # FIN QUA SCRIVE CORRETTO
    conn = engine.connect()

    queruyIdFilmDB = select([func.max(film.c.idfilm)])
    idFilmDBres = conn.execute(queruyIdFilmDB).fetchone()
    idFilmDB = idFilmDBres[0] + 1
    # Controllo se il film sia già presente nel database
    isThereQuery = select([film.c.titolo, film.c.anno]). \
        where(and_(film.c.anno == bindparam('annoFilm'), film.c.titolo == bindparam('titoloFilm')))
    isThere = conn.execute(isThereQuery, titoloFilm=newTitle, annoFilm=newYearPubb)

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
    #imageInsert = film.insert()
    #conn.execute(imageInsert, [
    #    {
    #        'img' : image
    #    }
    #])
    print("Immagine salvata")

    conn.close()

    return redirect("/admin")


if __name__ == '__main__':
    app.run(debug=True)
