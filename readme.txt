__________________|      |_________________________________________________________________________________
     ,--.    ,--.          ,--.   ,--.
    |oo  | _  \  `.       | oo | |  oo|
o  o|~~  |(_) /   ;       | ~~ | |  ~~|o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o  o 
    |/\/\|   '._,'        |/\/\| |/\/\|
__________________        _________________________________________________________________________________
                  |      |


Willkommen zu deinem eigenen Pac-Man-Spiel! Hier findest du alle wichtigen Informationen zur Steuerung, zum
Hinzufügen eigener Karten und Hinweise zum Spiel. Viel Spaß beim Spielen!



! Settings, Highscore und die config werden erst beim ersten mal starten geladen !

-----------------------------------------------------------------------------------------------------------
Steuerung:

Pfeiltasten (↑ ↓ ← →): Bewege Pac-Man durch das Labyrinth.
ESC: Öffnet das Hauptmenü oder beendet das Spiel.
ENTER: Bestätige Auswahl im Menü und beim Namen eingeben
UP/DOWN im Menü: Navigiere durch die Menüoptionen.
LEFT/RIGHT (im Einstellungsmenü): Passe die Lautstärke oder Auflösung an.

-----------------------------------------------------------------------------------------------------------
Hinzufügen von Karten:

Möchtest du dein eigenes Level erstellen? Kein Problem! Hier erfährst du, wie du Karten hinzufügen kannst:

Design der Karte: Verwende folgende Werte, um das Spielfeld zu erstellen:

1: Wand
0: Punkt (10 Punkte beim Einsammeln, Level up wenn alle gefressen wurden)
-3: Kraftpille (alle Geister werden für kurze Zeit schreckhaft)
-2: Frucht (100 Punkte bei Einsammeln)
2: Geistertür (Geister können hier passieren, Pac-Man nicht)
5: Spawnpunkt für zufällige Geister
7: Startposition für Pac-Man
3: Teleporter oder Rand (erlaubt Geistern und Pac-Man, von einer Seite zur anderen zu teleportieren)
Beispielkarten siehst

1, 1, 1, 1, 1
1, 0, 7, 0, 1
1, -3, 5, -2, 1
1, 1, 1, 1, 1

Speichern der Datei:
Speichere die Karte als .csv-Datei (z. B. my_level.csv).
Lege die Datei im Ordner ./Pacman/pacman-art/levels/ ab.

Aktivieren der Karte:
Öffne die Konfigurationsdatei config.json im Spielverzeichnis.
Füge den Pfad zur neuen Karte unter levels hinzu, die keys sollten dabei numerisch nach oben zählen damit
die lvl korrekt geladen werden. lvl0 wird dabei nicht geladen.
Die Tile-Größe wird automatisch an die Auflösung angepasst.

---------------------------------------------------------------------------------------------------------
Auflösungswechsel:

Du kannst die Auflösung im Einstellungsmenü anpassen.
Falls mit der config-Datei eigene Auflösungen hinzugefügt werden sollen, muss auch die Größe der Kachelfelder
manuell dahinter angegeben werden. Also achte auf das Format [Breite, Höhe, Feldgroesse]
Die Feldgröße darf nicht kleiner als 10 sein und muss durch 5 teilbar sein.


Vielen Dank, dass du dieses Spiel spielst! Genieße die spannende Jagd durch das Labyrinth, knacke den Highscore
und erstelle deine eigenen Herausforderungen!