from flask import Flask, render_template, request, jsonify
import sqlite3
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


@app.route('/')
def pocetna():
    return render_template('index.html')


@app.route('/about.html')
def about():
    return render_template('about.html')


@app.route('/login.html')
def admin():
    return render_template('login.html')


@app.route('/contact.html')
def contact():
    return render_template('contact.html')


@app.route('/reserv.html')
def reserv():
    return render_template('reserv.html')


@app.route('/video.html')
def video():
    return render_template('video.html')


@app.route('/index.html')
def pocetnaa():
    return render_template('index.html')


def send_email(subject, recipient, message):
    # SMTP Configuration
    smtp_host = 'smtp-mail.outlook.com'
    smtp_port = 587
    smtp_username = 'karlo-domladovac@hotmail.com'  # Replace with your Hotmail email address
    smtp_password = 'karlothe13latino'  # Replace with your Hotmail password

    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = recipient
    msg['Subject'] = subject

    # Attach the message body
    msg.attach(MIMEText(message, 'plain'))

    # Create an SMTP client
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        # Start the TLS encryption
        server.starttls()

        # Login to the SMTP server
        server.login(smtp_username, smtp_password)

        # Send the email
        server.send_message(msg)

    app.logger.info(f"Email sent to {recipient}")


@app.route('/rezervacija', methods=['GET', 'POST'])
def rezervacija():
    if request.method == 'POST':
        # Handle POST request
        ime_prezime = request.form.get('visitor_name')
        email = request.form.get('visitor_email')
        broj_mobitela = request.form.get('visitor_phone')
        datum = request.form.get('checkin')

        if not is_datum_dostupan(datum):
            return jsonify(message='Odabrani datum je već rezerviran.')

        spremi_rezervaciju(ime_prezime, email, broj_mobitela, datum)

        # Send email notification
        subject = 'Nova rezervacija'
        message = f'Nova rezervacija:\nIme i prezime: {ime_prezime}\nEmail: {email}\nBroj mobitela: {broj_mobitela}\nDatum: {datum}'
        send_email(subject, 'donna.kliska@hotmail.com', message)

        return jsonify(message='Rezervacija je uspješno spremljena.')
    else:
        # Handle GET request
        return render_template('reserv.html')


def is_datum_dostupan(datum):
    # Connect to the SQLite database
    connection = sqlite3.connect('baza.db')
    cursor = connection.cursor()

    # Execute the query
    cursor.execute("SELECT * FROM rezervacije WHERE datum = ?", (datum,))
    rezultat = cursor.fetchone()

    # Close the database connection
    cursor.close()
    connection.close()

    return rezultat is None


def spremi_rezervaciju(ime_prezime, email, broj_mobitela, datum):
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect('baza.db')
        cursor = connection.cursor()

        # Execute the query to save the reservation
        cursor.execute("INSERT INTO rezervacije (ime_prezime, email, broj_mobitela, datum) VALUES (?, ?, ?, ?)",
                       (ime_prezime, email, broj_mobitela, datum))

        # Commit the changes to the database
        connection.commit()

        # Close the database connection
        cursor.close()
        connection.close()

        app.logger.info("Rezervacija je uspješno spremljena.")
    except Exception as e:
        app.logger.error("Greška pri spremanju rezervacije: " + str(e))


def provjeri_prijavu(korisnicko_ime, lozinka):
    try:
        with open('users.json') as file:
            users = json.load(file)

        for user in users:
            if user.get('username') == korisnicko_ime and user.get('password') == lozinka:
                return True
    except (FileNotFoundError, json.JSONDecodeError):
        # Error occurred while opening the file or decoding JSON
        pass

    return False


def dohvati_rezervacije():
    try:
        connection = sqlite3.connect('baza.db')
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM rezervacije")
        rezervacije = cursor.fetchall()

        cursor.close()
        connection.close()

        return rezervacije
    except Exception as e:
        app.logger.error("Greška pri dohvaćanju rezervacija: " + str(e))
        return []


@app.route('/login', methods=['POST'])
def login():
    korisnicko_ime = request.form['username']
    lozinka = request.form['password']

    if provjeri_prijavu(korisnicko_ime, lozinka):
        return render_template('sucesfull_login.html')
    else:
        poruka = 'Pogrešno korisničko ime ili lozinka.'
        return render_template('login.html', rezervacije=None, poruka=poruka)

@app.route('/listreservations', methods=['GET', 'POST'])
def list_reservations():
    rezervacije = dohvati_rezervacije()
    return render_template('sucesfull_login.html', rezervacije=rezervacije, poruka=None)

@app.route('/deletereservation', methods=['POST'])
def delete_reservation():
    reservation_id = request.form.get('reservationId')
    app.logger.info(f"reserzacija za brisanje {reservation_id}")

    try:
        connection = sqlite3.connect('baza.db')
        cursor = connection.cursor()

        # Execute the query to delete the reservation
        cursor.execute("DELETE FROM rezervacije WHERE id = ?", (reservation_id,))

        # Commit the changes to the database
        connection.commit()

        # Close the database connection
        cursor.close()
        connection.close()

        return render_template('sucesfull_login.html', poruka=f'obrisana je rezervacija broj {reservation_id}')
    except Exception as e:
        app.logger.error("Greška pri brisanju rezervacije: " + str(e))
        return jsonify(message='Došlo je do pogreške prilikom brisanja rezervacije.')
if __name__ == '__main__':
    # Create the database and table if they don't exist
    connection = sqlite3.connect('baza.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS rezervacije (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ime_prezime TEXT,
                        email TEXT,
                        broj_mobitela TEXT,
                        datum TEXT
                    )''')
    cursor.close()
    connection.close()

    app.run(debug=True)
