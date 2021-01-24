# HTML import
import os
from operator import and_

import json
from datetime import datetime, date
from sqlite3.dbapi2 import Binary

import flask
from flask import Flask, render_template, request, json, redirect, url_for, flash, send_from_directory

from werkzeug.utils import secure_filename

# DB e Users import
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from sqlalchemy import select, insert, bindparam, Boolean, Time, Date, update, Table, desc, asc, distinct
from sqlalchemy import Sequence
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

# TYPE import
from array import *
import decimal
import string
import base64

from sqlalchemy.dialects.postgresql import psycopg2, BYTEA
from sqlalchemy.orm import sessionmaker

UPLOAD_FOLDER = 'C:/Users/Riccardo/Documents/PyCharmProjects/Cinema_Basi/static/img/Locandine/'
ALLOWED_EXTENSIONS = {'png'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = 'itsreallysecret'
app.config['SECRET_KEY'] = 'secretcinemaucimg'

# ATTENZIONE!!! DA CAMBIARE A SECONDA DEL NOME UTENTE E NOME DB IN POSTGRES
engineVisistatore = create_engine('postgres+psycopg2://visitatore:0000@localhost:5432/CinemaBasi')
engineCliente = create_engine('postgres+psycopg2://clienteloggato:1599@localhost:5432/CinemaBasi')
engineAdmin = create_engine('postgres+psycopg2://adminloggato:12358@localhost:5432/CinemaBasi',
                            isolation_level='REPEATABLE READ')

metadata = MetaData()

film = Table('film', metadata,
             Column('idfilm', Integer, primary_key=True),
             Column('titolo', String),
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
               Column('ruolo', Integer)
               )

persona = Table('persona', metadata,
                Column('idpersona', Integer, primary_key=True),
                Column('nomecognome', String)
                )

sala = Table('sala', metadata,
             Column('idsala', Integer, primary_key=True),
             Column('numfila', Integer),
             Column('numcolonne', Integer),
             )

proiezione = Table('proiezione', metadata,
                   Column('orario', Time),
                   Column('idsala', Integer),
                   Column('idfilm', Integer),
                   Column('idproiezione', Integer, primary_key=True),
                   Column('data', Date),
                   Column('is3d', Boolean)
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
                   Column('idattore', Integer, ForeignKey(persona.c.idpersona)),
                   Column('idfilm', Integer, ForeignKey(film.c.idfilm))
                   )

registafilm = Table('registafilm', metadata,
                    Column('idregista', Integer, ForeignKey(persona.c.idpersona)),
                    Column('idfilm', Integer, ForeignKey(film.c.idfilm))
                    )

metadata.create_all(engineVisistatore)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

log_try = False

# variabile globale che mi serve per sapere se ci sono errori senza il bisogno (problematico) di passarli attraverso la redirect
erroriCompilazione = ''


class User(UserMixin):
    def __init__(self, id, email, ruolo):
        self.id = id
        self.email = email
        self.ruolo = ruolo

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

    def get_ruolo(self):
        return self.ruolo

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
        self.data.append(str(n))

    def tostr(self):
        return [str(num) for num in self.data]

    def __str__(self):
        return str(self.idfilm) + " " + self.name + " " + str([str(num) for num in self.data])


@login_manager.user_loader
def load_user(user_id):
    conn = engineCliente.connect()
    user = conn.execute(select([utente]).where(utente.c.idutente == user_id)).fetchone()
    conn.close()
    if user is None:
        return None
    else:
        real_id = int(user[1])
        real_email = str(user[0]).strip()
        real_ruolo = user['ruolo']
        return User(real_id, real_email, real_ruolo)


# fun: permette di serializzare i dati per le conversioni json
def alchemyencoder(obj):
    if isinstance(obj, datetime.date):  # data
        return obj.isoformat()
    elif isinstance(obj, datetime.time):  # ora
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


# render alla pagina principale
@app.route('/', methods=['GET', 'POST'])
def home_page():
    # apertura connessione al DB
    conn = engineVisistatore.connect()

    global erroriCompilazione
    errore = None
    if erroriCompilazione != '':
        errore = erroriCompilazione
        erroriCompilazione = ''

    oggi = date.today()
    inputGenere = None
    inputTitle = None
    try:
        inputGenere = request.form["inputGenere"]
    except:
        print("")
    try:
        inputTitle = (request.form["inputTitle"]).upper()
    except:
        print("")

    queryGeneri = select([film.c.genere])
    genere = conn.execute(queryGeneri).fetchall()
    array = []

    for g in genere:
        temp = g[0].split(', ')
        for t in temp:
            array.append(t)
    array = set(array)

    queryFilms = select([film]).where(and_(film.c.datainizio <= oggi, film.c.datafine >= oggi))
    films = conn.execute(queryFilms).fetchall()

    if inputGenere != None:
        removeFilms = []
        for f in films:
            if (f.genere).find(inputGenere) == -1:
                removeFilms.append(f)
        for f in removeFilms:
            films.remove(f)
    if inputTitle != None:
        removeFilms = []
        for f in films:
            if (f.titolo).find(inputTitle) == -1:
                removeFilms.append(f)
        for f in removeFilms:
            films.remove(f)

    conn.close()

    if current_user.is_authenticated:
        return render_template('login.html', movies=films,
                               availableGeneri=array)  # stessa pagina rimossa dei btn log in e register
    else:
        return render_template('index.html', movies=films, availableGeneri=array, log=log_try)


@app.route('/film/<idFilm>', methods=['GET'])
@login_required
def base_film(idFilm):
    now = datetime.now()
    conn = engineCliente.connect()
    # query a db per recuperare entità film con id idFilm
    queryFilm = select([film.c.titolo, film.c.trama, film.c.genere]).where(
        film.c.idfilm == bindparam("idFilmRecuperato"))
    filmPage = conn.execute(queryFilm, {'idFilmRecuperato': idFilm}).fetchone()

    queryProiezioni = select([proiezione.c.idproiezione, proiezione.c.data, proiezione.c.orario, proiezione.c.is3d]) \
        .where(and_(proiezione.c.idfilm == bindparam("idProiezioneRecuperato"),
                    proiezione.c.data >= datetime.date(now)))
    proiezioni = conn.execute(queryProiezioni, {'idProiezioneRecuperato': idFilm})

    conn.close()
    return render_template('base_film.html', movie=filmPage, spettacoli=proiezioni)


# render alla pagina di prenotazione dei biglietti
@app.route('/prenotazione/<idProiezione>', methods=['GET'])
@login_required
def prenotazione(idProiezione):
    conn = engineCliente.connect()

    queryProiezione = select([proiezione]).where(proiezione.c.idproiezione == idProiezione)
    proiezioni = conn.execute(queryProiezione).fetchone()

    queryFilmToBeBooked = select([film]).where(film.c.idfilm == (proiezioni.idfilm))
    filmToBeBooked = conn.execute(queryFilmToBeBooked).fetchone()

    querySeats = select([sala]).where(sala.c.idsala == proiezioni.idsala)
    seats = conn.execute(querySeats).fetchone()

    riga = seats.numfila
    colonna = seats.numcolonne

    # select posto from posto join biglietto where b.idposto=p.idposto and b.idproiezione= "idProiezione"

    queryBiglietti = select([posto]).order_by(asc(biglietto.c.idposto)).select_from(posto.join(biglietto)) \
        .where(and_(biglietto.c.idproiezione == idProiezione, biglietto.c.idposto == posto.c.idposto))
    biglietti = conn.execute(queryBiglietti).fetchall()
    posti = []

    for i in range(riga + 1):
        posti.append([])
        for j in range(colonna + 1):
            posti[i].append(False)

    for b in biglietti:
        posti[int(ord(b.fila) - ord('A'))][int(b.numero)] = True

    conn.close()
    return render_template('prenotazione.html', movie=filmToBeBooked, proiezione=proiezioni, riga=riga, colonna=colonna,
                           string=string, ticket=biglietti, posti=posti)
    # default=alchemyencoder


def revertAcquista(postiAcquistati, idProiezione, lastX, idUtente, idSala):
    delete = biglietto.delete()
    conn = engineCliente.connect()
    for x in range(0, lastX - 1):
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
    eng = create_engine('postgresql+psycopg2://clienteloggato:1599@localhost:5432/CinemaBasi',
                        isolation_level='REPEATABLE READ')
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
        queryBiglietto = select([biglietto]). \
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
    return render_template('biglietto.html', numSala=idSala, orario=orarioProiezione, posto=postiAcquistati,
                           len=len(postiAcquistati))


# AREA UTENTE
@app.route('/areaUtente', methods=['GET', 'POST'])
@login_required
def areaUtente():
    conn = engineCliente.connect()
    queryUser = select([utente.c.nome, utente.c.cognome, utente.c.email]) \
        .where(utente.c.idutente == current_user.id)
    userInfo = conn.execute(queryUser).fetchone()

    queryBigliettiTot = select([posto.c.fila, posto.c.numero, proiezione.c.orario, proiezione.c.data, film.c.titolo]). \
        select_from(posto.join(biglietto, biglietto.c.idposto == posto.c.idposto). \
                    join(proiezione, proiezione.c.idproiezione == biglietto.c.idproiezione). \
                    join(film, film.c.idfilm == proiezione.c.idfilm)). \
                    where(biglietto.c.idutente == current_user.id).\
        order_by(desc(proiezione.c.data))
    biglietti = conn.execute(queryBigliettiTot).fetchall()
    conn.close()
    return render_template('areaUtente.html', biglietti=biglietti, u=userInfo)


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    metadata.create_all(engineCliente)
    conn = engineCliente.connect()
    if request.method == 'POST':
        form_email = request.form['mailLogin']
        form_passw = request.form['passwordLogin']
        queryControlUser = select([utente]).where(
            and_(utente.c.email == bindparam('expectedEmail'), utente.c.password == bindparam('expectedPAss')))
        utente_log = conn.execute(queryControlUser, expectedEmail=form_email, expectedPAss=form_passw).fetchone()
        conn.close()
        global erroriCompilazione
        if utente_log is None:
            global log_try
            log_try = 1
            erroriCompilazione = "Errore inserimento dati"
            return redirect("/")  # home_page()
        login_user(User(utente_log['idutente'], utente_log['email'], utente_log['ruolo']))  # appoggio a flask_login
        if int(current_user.get_ruolo()) == 0:
            return redirect("/")
        else:
            metadata.create_all(engineAdmin)
            return redirect("/admin")
    return render_template('login.html')


log_change = 0


# CHANGE PSW
@app.route('/areaUtente/changePsw', methods=['GET', 'POST'])
@login_required
def changePsw():
    global log_change
    conn = engineCliente.connect()
    queryUser = select([utente.c.nome, utente.c.cognome, utente.c.email]) \
        .where(utente.c.idutente == current_user.id)
    userInfo = conn.execute(queryUser).fetchone()

    form_oldpws = str(request.form['oldpassword'])
    form_newpws = str(request.form['newpassword'])
    form_newpws2 = str(request.form['newpassword2'])
    queryPsw = select([utente.c.password]) \
        .where(utente.c.idutente == current_user.id)
    oldPsw = conn.execute(queryPsw).fetchone()[0]

    if form_oldpws == oldPsw:
        if form_newpws == form_newpws2:
            queryUpdate = update(utente).where(utente.c.idutente == bindparam("utente")).values(
                password=bindparam("nuovaPassword"))
            conn.execute(queryUpdate, utente=current_user.id, nuovaPassword=form_newpws)
            conn.close()
            return redirect("/logout")
        else:
            log_change = 2
    else:
        log_change = 1
    conn.close()
    return render_template("areaUtente.html", u=userInfo,
                           log=log_change)


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = engineVisistatore.connect()
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
    ruoloreg = 0

    conn.execute(insreg, [
        {
            'email': mailreg, 'idutente': myid,
            'password': passwordreg, 'nome': namereg,
            'cognome': surnamereg, 'datanascita': birthreg,
            'sesso': sexreg, 'numfigli': sonsreg,
            'residenza': addressreg, 'numcell': cellphonereg, 'ruolo': ruoloreg
        }

    ])
    conn.close()
    User.authenticated = True
    login_user(User(myid, mailreg, 0))  # appoggio a flask_login
    return home_page()


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect("/")


################################################## GESTIONE STATISTICHE #############################################################

# STATISTICA: definizione per la funzione usata per calcolare quanti biglietti sono stati venduti per film
@app.route("/ticket_sold", methods=['GET', 'POST'])
@login_required
def biglietti_venduti():
    eng = create_engine('postgres+psycopg2://adminloggato:12358@localhost:5432/CinemaBasi',
                        isolation_level='REPEATABLE READ')
    conn = eng.connect()
    # query di divisione dei giorni per ogni proiezione
    # somma dei biglietti divisi per film e data
    query = conn.execute(
        "SELECT film.idfilm, film.titolo, date.data, (SELECT SUM(visite) AS somma\
                                                        FROM proiezione LEFT JOIN(SELECT COUNT(*) AS visite, biglietto.idproiezione\
                                                                                   FROM biglietto GROUP BY idproiezione) AS visitatori ON\
                                                                        proiezione.idproiezione = visitatori.idproiezione \
                                                                        WHERE proiezione.idfilm = film.idfilm AND proiezione.data = date.data)\
        FROM film,(SELECT DISTINCT proiezione.data FROM proiezione) AS date \
        ORDER BY film.idfilm, date.data\
        ")

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
    return render_template("admin_pages/stats/biglietti_venduti.html", stats=stats, giorni=giorni)


# STATISTICA: definizione per la funzione usata per calcolare la percentuale di occupazione delle sale per film
@app.route("/occupazione_sala", methods=['GET', 'POST'])
@login_required
def occupazione_sala():
    conn = engineAdmin.connect()

    numPostoPerSala = conn.execute(
        select([sala.c.idsala, sala.c.numfila, sala.c.numcolonne]).order_by(sala.c.idsala)).fetchall()

    arrayPostiTot = []
    for b in numPostoPerSala:
        arrayPostiTot.append([b["idsala"], b["numfila"] * b["numcolonne"]])

    bigliettiPerProiezione = conn.execute(select(
        [func.count(biglietto.c.idproiezione), proiezione.c.idsala, biglietto.c.idproiezione,
         proiezione.c.idfilm]).select_from(
        biglietto.join(proiezione, biglietto.c.idproiezione == proiezione.c.idproiezione).
            join(sala, proiezione.c.idsala == sala.c.idsala)).
                                          group_by(proiezione.c.idproiezione, biglietto.c.idproiezione,
                                                   proiezione.c.idfilm)).fetchall()

    listaFilms = conn.execute(select([film]).order_by(film.c.idfilm)).fetchall()
    totPostiFilm = []
    totBigFilm = []
    for f in listaFilms:
        totPostiFilm.append(0)
        totBigFilm.append(0)

    for b in bigliettiPerProiezione:
        totPostiFilm[b["idfilm"] - 1] += arrayPostiTot[b["idsala"] - 1][1]
        totBigFilm[b["idfilm"] - 1] += b[0]

    percentuali = []
    i = 0
    for b in totBigFilm:
        if totPostiFilm[i] != 0:
            percentuali.append(round((b / totPostiFilm[i]) * 100, 1))
        else:
            percentuali.append(0)
        i = i + 1

    conn.close()

    return render_template("/admin_pages/stats/occupazione_sale.html", films=listaFilms, media=percentuali)


# STATISTICA: definizione per la funzione usata per calcolare quale genere viene preferito dai clienti
def dividi_generi(array_generi):
    array = array_generi.split(', ')
    array = list(set(array))
    return array


@app.route("/genere_preferito", methods=['GET', 'POST'])
@login_required
def genere_preferito():
    conn = engineAdmin.connect()
    # array contenente (totale biglietti per film, titolo film, genere del film)
    bigliettiPerFilm = conn.execute(
        select([func.count(biglietto.c.idposto), film.c.titolo, film.c.genere]).select_from(biglietto.
                                                                                            join(proiezione,
                                                                                                 biglietto.c.idproiezione == proiezione.c.idproiezione).
                                                                                            join(film,
                                                                                                 proiezione.c.idfilm == film.c.idfilm)). \
            group_by(film.c.titolo, film.c.genere)).fetchall()

    # vado a prendermi e suddividermi tutti i generi
    queryGeneri = select([film.c.genere])
    generi = conn.execute(queryGeneri).fetchall()
    arrayGeneri = []
    for g in generi:
        temp = g[0].split(', ')
        for t in temp:
            arrayGeneri.append(t)
    arrayGeneri = list(set(arrayGeneri))

    for n in bigliettiPerFilm:
        generiFilmSingolo = dividi_generi(n[2])

    # Il contenuto di questo array all'indice 'x' corrisponde al numero di biglietti venduti al genere che troviamo allo stesso indice (x) dell'array 'generi'
    bigliettiPerGenere = [0] * len(arrayGeneri)
    for n in bigliettiPerFilm:
        totBigliettiPerFilm = n[0]
        generiFilmSingolo = dividi_generi(n[2])
        i = 0
        while i < len(generiFilmSingolo):
            j = 0
            trovato = 0
            while j < len(arrayGeneri) and trovato == 0:
                if generiFilmSingolo[i] == arrayGeneri[j]:
                    bigliettiPerGenere[j] = bigliettiPerGenere[j] + totBigliettiPerFilm
                    i = i + 1
                    trovato = 1
                else:
                    j = j + 1

    totBiglietti = 0
    for n in bigliettiPerGenere:
        totBiglietti = totBiglietti + n

    percentualiPerGenere = [0] * len(arrayGeneri)
    i = 0
    for biglietti in bigliettiPerGenere:
        percentualiPerGenere[i] = round((biglietti / totBiglietti) * 100, 1)
        i = i + 1

    conn.close()

    return render_template("/admin_pages/stats/generi_preferiti.html", arrayPerc=percentualiPerGenere,
                           arrayPerGeneri=arrayGeneri)


##################################### GESTIONE TABELLA FILM ############################################

@app.route('/admin')
@login_required
def tabella_film():
    if current_user.ruolo == 0:
        return redirect("/")
    else:
        conn = engineAdmin.connect()
        takenFilms = select([film]).order_by(film.c.idfilm.asc())
        queryTakenFilms = conn.execute(takenFilms).fetchall()
        conn.close()
        return render_template('admin_pages/tabelle_admin/tabella_film.html', arrayFilms=queryTakenFilms,
                               adminLogged=current_user.get_email(), error=erroriCompilazione)


@app.route('/film/update/<idFilm>', methods=['GET', 'POST'])
@login_required
def updateFilm(idFilm):
    global erroriCompilazione
    try:
        inputTitle = request.form["inputTitle" + idFilm]
        inputGenre = request.form["inputGenre" + idFilm]
        inputPlot = request.form["inputPlot" + idFilm]
        inputStartData = request.form["inputStartDate" + idFilm]
        inputEndData = request.form["inputEndDate" + idFilm]
        inputDuration = request.form["inputDuration" + idFilm]
        inputCountry = request.form["inputCountry" + idFilm]
        inputYearPubb = request.form["inputYear" + idFilm]
        if request.form["inputVM" + idFilm] == 'True':
            inputMinAge = True
        else:
            inputMinAge = False
        eng = create_engine('postgres+psycopg2://adminloggato:12358@localhost:5432/CinemaBasi',
                            isolation_level='REPEATABLE READ')
        conn = eng.connect()
        queryUpdate = update(film). \
            where(film.c.idfilm == bindparam("expectedFilm")).values(titolo=bindparam("newInputTitle"),
                                                                     genere=bindparam("newInputGenre"),
                                                                     trama=bindparam("newInputPlot"),
                                                                     datainizio=bindparam("newInputStartDate"),
                                                                     datafine=bindparam("newInputEndDate"),
                                                                     durata=bindparam("newInputDuration"),
                                                                     paese=bindparam("newInputCountry"),
                                                                     anno=bindparam("newInputYear"),
                                                                     vm=bindparam("newInputVm"))
        conn.execute(queryUpdate, expectedFilm=idFilm, newInputTitle=inputTitle, newInputGenre=inputGenre,
                     newInputPlot=inputPlot,
                     newInputStartDate=inputStartData, newInputEndDate=inputEndData, newInputDuration=inputDuration,
                     newInputCountry=inputCountry,
                     newInputYear=inputYearPubb, newInputVm=inputMinAge)
        conn.close()
        erroriCompilazione = ''
        return redirect("/admin")
    except:
        erroriCompilazione = "Errore nell'inserimento dei dati"
        return redirect("/admin")


def immagini_permesse(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('C:/Users/Riccardo/Documents/PyCharmProjects/Cinema_Basi/static/img/Locandine/',
                               filename)


@app.route('/film/insert', methods=['GET', 'POST'])
def insert_film():
    global erroriCompilazione
    try:
        newTitle = request.form["newTitle"]
        newGenre = request.form["newGenre"]
        newPlot = request.form["newPlot"]
        newStartData = request.form["newStartData"]
        newLastData = request.form["newLastData"]
        newDuration = request.form["newDuration"]
        newCountry = request.form["newCountry"]
        newYearPubb = request.form["newYearPubb"]
        newMinAge = request.form["newMinAge"]
        newMovDir = request.form["newMovDir"]
        newActors = request.form["newActors"]

        conn = engineAdmin.connect()

        queruyIdFilmDB = select([func.max(film.c.idfilm)])
        idFilmDBres = conn.execute(queruyIdFilmDB).fetchone()
        idFilmDB = idFilmDBres[0] + 1
        # Controllo se il film sia già presente nel database
        isThereQuery = select([film.c.titolo, film.c.anno]). \
            where(and_(film.c.anno == bindparam('annoFilm'), film.c.titolo == bindparam('titoloFilm')))
        isThere = conn.execute(isThereQuery, titoloFilm=newTitle, annoFilm=newYearPubb).fetchone()

        if isThere is None:
            # QUERY DI AGGIUNTA DI UN FILM
            insNewFilm = film.insert()
            conn.execute(insNewFilm, [
                {
                    'idfilm': idFilmDB, 'titolo': newTitle, 'genere': newGenre,
                    'trama': newPlot, 'datainizio': newStartData,
                    'datafine': newLastData, 'durata': newDuration,
                    'paese': newCountry, 'anno': newYearPubb,
                    'vm': bool(newMinAge)
                }
            ])

        ############ AGGIORNAMENTO DIRECTOR MOVIE ############
        arrayNewDirectors = list(newMovDir.split(', '))
        for director in arrayNewDirectors:
            queryDbDirector = select([persona.c.idpersona]). \
                where(persona.c.nomecognome == bindparam('nomeRegista'))
            dbDirector = conn.execute(queryDbDirector, nomeRegista=director).fetchall()  # eseguo la ricerca
            insNewDirectorMovie = registafilm.insert()
            if dbDirector:  # se è già presente
                conn.execute(insNewDirectorMovie, [
                    {
                        'idregista': int(dbDirector[0][0]), 'idfilm': idFilmDB
                    }
                ])
            else:  # se invece non c'è

                # inserisco prima la persona
                queryMaxPersonaDB = select([func.max(persona.c.idpersona)])
                idMaxPersonaDB = list(conn.execute(queryMaxPersonaDB).fetchone())[0] + 1
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
        arrayNewActors = list(newActors.split(', '))
        for actor in arrayNewActors:
            queryDbActor = select([persona.c.idpersona]). \
                where(persona.c.nomecognome == bindparam('nomeAttore'))
            dbActors = list(conn.execute(queryDbActor, nomeAttore=actor).fetchall())  # eseguo la ricerca
            insNewActorsMovie = attorefilm.insert()
            if dbActors:  # se è già presente
                print(dbActors)
                conn.execute(insNewActorsMovie, [
                    {
                        'idattore': int(dbActors[0][0]), 'idfilm': idFilmDB
                    }
                ])
            else:  # se invece non c'è

                # inserisco prima la persona
                queryMaxPersonaDB = select([func.max(persona.c.idpersona)])
                idMaxPersonaDB = list(conn.execute(queryMaxPersonaDB).fetchone())[0] + 1
                insNewActors = persona.insert()
                conn.execute(insNewActors, [
                    {
                        'idpersona': idMaxPersonaDB, 'nomecognome': actor
                    }
                ])
                # poi aggiungo il collegamento ad attorefilm
                conn.execute(insNewActorsMovie, [
                    {
                        'idattore': idMaxPersonaDB, 'idfilm': idFilmDB
                    }
                ])

        conn.close()

        # inserimento locandine
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and immagini_permesse(file.filename):
            filename = secure_filename(file.filename)
            file.save(
                os.path.join('C:/Users/Riccardo/Documents/PyCharmProjects/Cinema_Basi/static/img/Locandine/', filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
        erroriCompilazione=''
        return redirect("/admin")
    except:
        erroriCompilazione = "Errore inserimento dati"
        return redirect("/admin")


@app.route('/film/unpublish/<idFilm>', methods=['GET'])
@login_required
def cancellazionePubblicazioneFilm(idFilm):
    conn = engineAdmin.connect()
    queryDelete = film.update().where(film.c.idfilm == bindparam("filmTaken")).values({"shown": 0})
    conn.execute(queryDelete, {'filmTaken': idFilm})
    conn.close()
    return redirect("/admin")


@app.route('/film/publish/<idFilm>', methods=['GET'])
@login_required
def ripubblicazione(idFilm):
    conn = engineAdmin.connect()
    queryDelete = film.update().where(film.c.idfilm == bindparam("filmTaken")).values({"shown": 1})
    conn.execute(queryDelete, filmTaken=idFilm)
    conn.close()
    return redirect("/admin")


############################################# GESTIONE TABELLA PROIEZIONE ##############################################

@app.route("/admin/tabella_proiezioni")
def tabella_proiezioni():
    if current_user.ruolo == 0:
        return redirect("/")
    else:
        global erroriCompilazione
        errore = None
        now = datetime.now()
        if erroriCompilazione != '':
            errore = erroriCompilazione
            erroriCompilazione = ''
        conn = engineAdmin.connect()
        queryFilms = select([film.c.titolo])
        films = conn.execute(queryFilms).fetchall()
        takenScreening = select([proiezione.c.idproiezione, proiezione.c.idfilm, proiezione.c.idsala, proiezione.c.data,
                                 proiezione.c.orario, proiezione.c.is3d, film.c.titolo]).where(
            and_(proiezione.c.idfilm == film.c.idfilm, proiezione.c.data >= datetime.date(now))).order_by(
            desc(proiezione.c.idproiezione))
        queryTakenScreening = conn.execute(takenScreening).fetchall()
        conn.close()
        print(queryTakenScreening)
        return render_template('admin_pages/tabelle_admin/tabella_proiezioni.html', arrayScreening=queryTakenScreening,
                               adminLogged=current_user.get_email(), films=films, error=errore)


@app.route('/proiezione/update/<idProiezione>', methods=['GET', 'POST'])
@login_required
def updateScreening(idProiezione):
    global erroriCompilazione
    try:
        inputSala = int(request.form["inputRoom" + idProiezione])
        inputData = request.form["inputDay" + idProiezione]
        inputOra = request.form["inputTime" + idProiezione]
        input3d = request.form["input3d" + idProiezione]

        giorno = list(inputData.split('-'))
        giornoScelto = datetime(int(giorno[0]), int(giorno[1]), int(giorno[2]))

        global erroriCompilazione

        if isinstance(inputSala, int) == False:
            erroriCompilazione = "Input della sala non corretto"
            return redirect("/admin/tabella_proiezioni")

        if giornoScelto >= datetime.today():
            print("giorno ok")
        elif giornoScelto <= datetime.today():
            erroriCompilazione = "Giorno nel passato non valido"
            return redirect("/admin/tabella_proiezioni")
        else:
            erroriCompilazione = "Input della data non corretto"
            return redirect("/admin/tabella_proiezioni")

        if input3d == "Si":
            nuovoInput3d = True
        elif input3d == "No":
            nuovoInput3d = False
        else:
            erroriCompilazione = "Input 3D non corretto"
            return redirect("/admin/tabella_proiezioni")

        eng = create_engine('postgres+psycopg2://adminloggato:12358@localhost:5432/CinemaBasi',
                            isolation_level='REPEATABLE READ')
        conn = eng.connect()
        queryUpdate = update(proiezione). \
            where(proiezione.c.idproiezione == bindparam("proiezione")).values(idsala=bindparam("newInputRoom"),
                                                                               data=bindparam("newInputDay"),
                                                                               orario=bindparam("newInputTime"),
                                                                               is3d=bindparam("new3d"))
        conn.execute(queryUpdate, proiezione=idProiezione, newInputRoom=inputSala, newInputDay=inputData,
                     newInputTime=inputOra, new3d=nuovoInput3d)
        conn.close()
        erroriCompilazione = ''
        return redirect("/admin/tabella_proiezioni")
    except:
        erroriCompilazione = "Errore nell'inserimento dei dati"
        return redirect("/admin/tabella_proiezioni")


@app.route('/proiezione/insert', methods=['GET', 'POST'])
@login_required
def insertScreening():
    global erroriCompilazione
    try:
        conn = engineAdmin.connect()

        inputTitolo = request.form["titolo"]
        inputOra = request.form["ora"]
        inputSala = int(request.form["sala"])
        inputGiorno = request.form["giorno"]
        input3d = request.form["3d"]

        if isinstance(inputSala, int) == False:
            print("Input della sala non corretto")
            return redirect("/admin/tabella_proiezioni")

        if inputGiorno >= str(date.today()):
            print("giorno ok")
        elif inputGiorno <= str(date.today()):
            print("Giorno nel passato non valido")
            return redirect("/admin/tabella_proiezioni")
        else:
            print("Input della data non corretto")
            return redirect("/admin/tabella_proiezioni")

        if input3d == "Si":
            nuovoInput3d = True
        elif input3d == "No":
            nuovoInput3d = False
        else:
            print("Input 3D non corretto")
            return redirect("/admin/tabella_proiezioni")

        queryIdFilm = select([film.c.idfilm]).where(film.c.titolo == bindparam("nuovoTitolo"))
        nuovoIdFilm = conn.execute(queryIdFilm, nuovoTitolo=inputTitolo).fetchone()[0]
        maxId = conn.execute(func.max(proiezione.c.idproiezione)).fetchone()
        insertProiezione = insert(proiezione).values(orario=bindparam("nuovoOrario"),
                                                     idfilm=bindparam("nuovoFilm"),
                                                     idproiezione=bindparam("nuovaIdproiezione"),
                                                     idsala=bindparam("nuovaSala"),
                                                     data=bindparam("nuovaData"),
                                                     is3d=bindparam("nuovo3d"))
        conn.execute(insertProiezione, nuovoOrario=inputOra, nuovoFilm=nuovoIdFilm, nuovaIdproiezione=maxId[0] + 1,
                     nuovaSala=inputSala, nuovaData=inputGiorno, nuovo3d=nuovoInput3d)
        erroriCompilazione = ''
        return redirect("/admin/tabella_proiezioni")
    except:
        erroriCompilazione = "Errore nell'inserimento dei dati"
        return redirect("/admin/tabella_proiezioni")


############################################# GESTIONE TABELLA UTENTI ##############################################


@app.route("/admin/tabella_utenti", methods=['GET', 'POST'])
def tabella_utenti():
    if current_user.ruolo == 0:
        return redirect("/")
    else:
        conn = engineAdmin.connect()
        takenUsers = select([utente]).order_by(asc(utente.c.idutente))
        queryTakenUsers = conn.execute(takenUsers).fetchall()
        conn.close()
        return render_template('admin_pages/tabelle_admin/tabella_utenti.html', arrayUsers=queryTakenUsers,
                               adminLogged=current_user.get_email())


@app.route('/admin/grant/<idUtente>', methods=['GET', 'POST'])
def rendi_admin(idUtente):
    global erroriCompilazione
    try:
        if current_user.ruolo == 0:
            return redirect("/")
        else:
            #### rendere un utente admin
            conn = engineAdmin.connect()
            inputMail = request.form["inputMail" + idUtente]
            inputPassword = request.form["inputPassword" + idUtente]
            queryUpdate = update(utente). \
                where(utente.c.idutente == bindparam("userTaken")).values(email=bindparam("newEmail"),
                                                                          password=bindparam("newPassword"),
                                                                          ruolo=bindparam("newAdminSelected"))
            conn.execute(queryUpdate, userTaken=idUtente, newEmail=inputMail, newPassword=inputPassword,
                         newAdminSelected=1)
            conn.close()
            erroriCompilazione = ''
            return redirect("/admin/tabella_utenti")
    except:
        erroriCompilazione = "Errore nell'inserimento dei dati"
        return redirect("/admin/tabella_utenti")


@app.route('/admin/ungranted/<idUtente>', methods=['GET', 'POST'])
def degrada_admin(idUtente):
    global erroriCompilazione
    try:
        if current_user.ruolo == 0:
            return redirect("/")
        else:
            #### revocare a un utente il permesso di essere admin
            conn = engineAdmin.connect()
            inputMail = request.form["inputMail" + idUtente]
            inputPassword = request.form["inputPassword" + idUtente]
            queryUpdate = update(utente). \
                where(utente.c.idutente == bindparam("userTaken")).values(email=bindparam("newEmail"),
                                                                          password=bindparam("newPassword"),
                                                                          ruolo=bindparam("newAdminSelected"))
            conn.execute(queryUpdate, userTaken=idUtente, newEmail=inputMail, newPassword=inputPassword,
                         newAdminSelected=0)
            conn.close()
            erroriCompilazione = ''
            return redirect("/admin/tabella_utenti")
    except:
        erroriCompilazione = "Errore nell'inserimento dei dati"
        return redirect("/admin/tabella_utenti")


if __name__ == '__main__':
    app.run(debug=True)
