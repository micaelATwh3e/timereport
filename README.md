# Tidrapporteringssystem

Ett Flask-baserat webbsystem för tidrapportering med stöd för:
- Användarhantering med inloggning
- Projekt hantering
- Tidrapportering per dag och projekt
- Semester- och sjukdomsregistrering
- Svenska helgdagar och helger
- Månadsöversikter med arbetsdag-beräkningar
- Rapporter och statistik

## Installation

1. Installera beroenden:
```bash
pip install -r requirements.txt
```

2. Starta applikationen:
```bash
python app.py
```

3. Öppna webbläsaren och gå till: `http://localhost:5000`

## Funktioner

### Användarhantering
- Registrera nytt konto
- Logga in/ut
- Varje användare har sin egen tidrapportering

### Projekt
- Lägg till och hantera projekt
- Aktivera/inaktivera projekt
- Standard projekt: xPM och Xonnectopia

### Tidrapportering
- Månadsvy med alla dagar
- Lägg in timmar per projekt och dag
- Automatisk beräkning av totalt arbetade timmar
- Visar arbetsdagar, behövd arbetstid och differens
- Färgkodning:
  - Röd: Helgdagar
  - Gul: Helger (lördag/söndag)
  - Blå: Semester
  - Orange: Sjukdom

### Frånvaro
- Registrera semesterperioder
- Registrera sjukdomsperioder
- Visa alla registrerade frånvaroperioder
- Automatisk markering i månadsvyn

### Rapporter
- Sammanställning av timmar per projekt
- Översikt över semester och sjukdom
- Årlig statistik

## Användning

1. **Första gången**: Registrera ett konto
2. **Logga in** med ditt användarnamn och lösenord
3. **Projekt**: Lägg till eller hantera projekt
4. **Dashboard**: Navigera till aktuell månad och fyll i arbetade timmar
5. **Frånvaro**: Registrera semester eller sjukdom
6. **Rapporter**: Se sammanfattningar och statistik

## Teknisk information

- Backend: Flask (Python)
- Databas: SQLite
- Frontend: HTML, CSS, JavaScript
- Autentisering: Flask-Login
- ORM: SQLAlchemy

## Standardprojekt

Vid första körningen skapas automatiskt:
- xPM
- Xonnectopia

## Svenska helgdagar 2026

Systemet inkluderar alla svenska helgdagar för 2026:
- Nyårsdagen, Trettondedag jul
- Långfredagen, Påskhelgen
- Första maj, Kristi himmelfärd, Pingst
- Nationaldagen, Midsommarafton
- Julhelgen, Nyårsafton
