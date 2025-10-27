# DAVideoflix

Ein Backend-Projekt mit Django + Django REST framework, das eine Netflix-ähnliche Video-Streaming-Plattform simuliert.  
Ziel: Aufgabenverwaltung von Film-/Video-Inhalten, Kategorisierung nach Genres („newOnVideoflix“, „documentary“ etc.), Verlinkung zu Video­dateien und Thumbnails.

## Features

- REST-API für Video-Inhalte, mit Metadaten wie Titel, Genre, Beschreibung, Thumbnail, Video-Link  
- Strukturierung nach Gruppen/Kategorien (z. B. „newOnVideoflix“, „documentary“, …)  
- Dockerised Setup mit `docker-compose`  
- Konfigurierbar via Environment-Variablen  
- Aufbau basiert auf modularen Django Apps (z. B. `auth_app`, `service_app`, `core`)  

## Voraussetzungen

- Docker & Docker Compose installiert  
- Git (zum Klonen des Repositories)  
- Optional: Python + virtuelle Umgebung, falls du ohne Docker arbeiten willst  
- Eine `.env` (umbenannt aus `.env.template`) mit den notwendigen Umgebungsvariablen  

## Installation & Ausführung
<ul>
<li>1. Repository klonen |   
   git clone https://github.com/MarcelArndt/DAVideoflix.git</li>

<li>2. Bearbeiten der .env.template und umbennnen in .env. | 
Danach im .env z.B. Datenbank-Host, Nutzer, Passwort, SECRET_KEY etc eintragen</li>

<li>3. virtuelle umgebung ertsellen | 
python -m venv env</li>

<li>4.requirements installieren | 
pip install -r requirements.txt</li>

<li>5.Docker-Compose ausführen | 
docker-compose up --build</li>

<li>6.Nach erfolgreichem Build und Start sollte der Server lokal erreichbar sein (z. B. http://localhost:8000)</li>
</ul>

API-Endpunkte entsprechend der Dokumentation im Projekt
Admin-Interface (sofern konfiguriert) unter /admin

## Struktur des Projekts

<ul>
    <li>auth_app/ – Authentifizierung & Benutzerverwaltung</li>
    <li>core/ – Kern-Django-Einstellungen, globale Modelle/Logik</li>
    <li>docker-compose.yml, backend.Dockerfile, backend.entrypoint.sh – Docker Setup</li>
    <li>.env.template – Vorlage für Umgebungsvariablen</li>
    <li>requirements.txt – Python-Abhängigkeiten</li>
</ul>

## Hinweise & Tipps

<ul>
    <li>Stelle sicher, dass deine .env korrekt ist, bevor du docker-compose up ausführst. Fehler wie falsche DB-Zugangsdaten oder fehlender SECRET_KEY führen sonst zu Build/Startup-Fehlern</li>
    <li>Für Produktion: Achte darauf, DEBUG=FALSE, sichere SECRET_KEY, HTTPS, „allowed hosts“ korrekt setzen</li>
    <li>Dokumentation der API Endpunkte <a href="https://cdn.developerakademie.com/courses/Backend/EndpointDoku/index.html?name=videoflix"></a> </li>
    <li>.env.template – Vorlage für Umgebungsvariablen</li>
    <li>requirements.txt – Python-Abhängigkeiten</li>
</ul>

## Kontakt
Bei Fragen oder Anmerkungen: Marcel Arndt
 - Email: info@arndt-marcel.de
 - Webseite: www.arndt-marcel.de