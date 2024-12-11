import json
import random
import pygame
import sys
import time
import csv
import os


class Entity:
    """
    Basisklasse für alle beweglichen Entitäten im Spiel (z. B. Pac-Man und Geister).

    Attribute:
        start_pos (list[float]): Die Startposition der Entität als [x, y].
        pos (list[float]): Aktuelle Position der Entität als [x, y].
        speed (float): Bewegungsgeschwindigkeit der Entität.
        current_direction (str): Aktuelle Bewegungsrichtung ("up", "down", "left", "right").
        alive (bool): Gibt an, ob die Entität "lebendig" ist.
        frightened (bool): Gibt an, ob die Entität erschrocken ist (nur für Geister relevant).
        respawn_time (float): Zeitstempel für den Respawn nach dem Tod.
        original_speed (float): Ursprüngliche Geschwindigkeit der Entität.
        images (dict): Wörterbuch mit Bildern, die die Entität repräsentieren.

    Methoden:
        __init__(position, speed, images):
            Initialisiert die Entität mit Startposition, Geschwindigkeit und Bildern.

        kill(mygame, sound):
            Setzt die Entität in den "tot"-Zustand und plant den Respawn.

        respawn():
            Setzt die Entität auf ihre Startposition zurück und initialisiert die Standardwerte.

        move(mygame, is_pacman=False):
            Bewegt die Entität in die aktuelle Richtung, falls möglich.
    """

    def __init__(self, position, speed, images):
        self.start_pos = position
        self.pos = position.copy()  # Startposition kopieren
        self.speed = speed
        self.current_direction = "right"
        self.alive = True
        self.frightened = False  # Nur für Geister, wird bei Pac-Man ignoriert
        self.respawn_time = 0
        self.original_speed = speed
        self.images = images

    def kill(self, mygame, sound):
        """Setzt die Entity in den 'tot'-Zustand und plant seinen Respawn."""
        if self.alive:
            if sound in mygame.sounds:
                mygame.sounds[sound].play()  # Sound abspielen
            self.respawn_time = time.time()
            self.alive = False
            self.pos = self.start_pos.copy()  # Startposition zurücksetzen
            self.current_direction = "right"

    def respawn(self):
        """
        Setzt den Geist auf seine Startposition zurück und initialisiert seine Werte.
        """
        self.pos = self.start_pos.copy()  # Setze die Position auf die Startposition
        self.respawn_time = 0
        self.alive = True  # Markiere  als lebendig
        self.frightened = False  # ist nicht mehr erschrocken
        self.speed = self.original_speed  # Setze die Geschwindigkeit zurück
        self.current_direction = "right"


    def move(self, mygame, is_pacman=False):
        """Bewegt die Entität in die aktuelle Richtung, wenn möglich."""
        if not check_collision_wall(mygame, self.current_direction, self.speed, self.pos, is_pacman):
            if self.current_direction == "up":
                self.pos[1] -= self.speed
            elif self.current_direction == "down":
                self.pos[1] += self.speed
            elif self.current_direction == "left":
                self.pos[0] -= self.speed
            elif self.current_direction == "right":
                self.pos[0] += self.speed


class Ghost(Entity):
    """
    Klasse für Geister.

    Attribute:
        original_speed (float): Ursprüngliche Geschwindigkeit des Geistes.
        image (pygame.Surface): Bild des Geistes im normalen Zustand.
        image_frightened (pygame.Surface): Bild des Geistes im erschrockenen Zustand.

    Methoden:
        __init__(mygame, position, images):
            Initialisiert einen Geist mit Position, Geschwindigkeit und Bildern.

        create_ghosts_from_matrix(mygame, images):
            Klassenmethode, die Geister basierend auf der Matrix erstellt.

        move(mygame):
            Bewegt den Geist basierend auf der aktuellen Richtung und Umgebung.

        is_intersection(mygame):
            Überprüft, ob sich der Geist an einer Kreuzung befindet.

        change_direction_random():
            Wählt eine neue zufällige Bewegungsrichtung (keine Rückwärtsbewegung).
    """

    def __init__(self, mygame, position, images):
        super().__init__(position, speed=int(mygame.convert_to_pixels(1) / 5), images=images)
        self.original_speed = self.speed
        self.image = random.choice(self.images["normal"])
        self.image_frightened = self.images["frightened"]

    @classmethod
    def create_ghosts_from_matrix(cls, mygame, images):
        """
        Erstellt Geister basierend auf spezifischen Zellenwerten in der Matrix.

        :param matrix: Zweidimensionale Liste, die das Spielfeld repräsentiert.
                    5 steht für 'random' Geister
        :param images: Wörterbuch mit Geisterbildern.
        :return: Liste von Ghost-Instanzen.
        """
        ghosts = []
        for y, row in enumerate(mygame.matrix):
            for x, cell in enumerate(row):
                if cell == 5:  # 'random'-Geist
                    ghosts.append(
                        cls(mygame, position=[mygame.convert_to_pixels(
                            x), mygame.convert_to_pixels(y)], images=images)
                    )
        return ghosts

    def move(self, mygame):
        """
        Bewegt den Geist basierend auf seiner aktuellen Richtung und seinem Typ.
        Ändert die Richtung an Kreuzungen oder bei Hindernissen.
        """

        # Überprüfen, ob der Geist sich in der aktuellen Richtung bewegen kann
        if not check_collision_wall(mygame, self.current_direction, self.speed, self.pos):
            super().move(mygame)
            if self.is_intersection(mygame):
                self.change_direction_random()
        else:
            # Kollision: Richtung ändern
            self.change_direction_random()

    def is_intersection(self, mygame):
        """Überprüft, ob der Geist sich an einer Kreuzung befindet, ohne die Rückwärtsrichtung zu zählen."""
        possible_directions = []

        # Überprüfe mögliche Bewegungsrichtungen
        if self.current_direction != "up" and not check_collision_wall(mygame, "up", self.speed, self.pos) and not check_for_teleport(mygame, self.pos, self.current_direction):
            possible_directions.append("up")
        if self.current_direction != "down" and not check_collision_wall(mygame, "down", self.speed, self.pos) and not check_for_teleport(mygame, self.pos, self.current_direction):
            possible_directions.append("down")
        if self.current_direction != "left" and not check_collision_wall(mygame, "left", self.speed, self.pos) and not check_for_teleport(mygame, self.pos, self.current_direction):
            possible_directions.append("left")
        if self.current_direction != "right" and not check_collision_wall(mygame, "right", self.speed, self.pos) and not check_for_teleport(mygame, self.pos, self.current_direction):
            possible_directions.append("right")

        # Eine Kreuzung ist ein Punkt, an dem mehr als eine Richtung möglich ist
        return len(possible_directions) > 1

    def change_direction_random(self):
        """
        Wählt eine zufällige Richtung für randome Geister, ohne die Rückwärtsrichtung zuzulassen.
        Aktualisiert die Richtung des Geistes direkt.
        """
        directions = ["up", "down", "left", "right"]
        direction = self.current_direction

        # Verhindere, dass der Geist in die gleiche Richtung zurückgeht
        if direction == "up" and "down" in directions:
            directions.remove("down")
        elif direction == "down" and "up" in directions:
            directions.remove("up")
        elif direction == "left" and "right" in directions:
            directions.remove("right")
        elif direction == "right" and "left" in directions:
            directions.remove("left")

        # Wähle eine neue zufällige Richtung aus
        self.current_direction = random.choice(directions)


class Pacman(Entity):
    """
    Klasse für den Spielercharakter (Pac-Man).

    Attribute:
        lives (int): Anzahl der verbleibenden Leben von Pac-Man.

    Methoden:
        __init__(mygame, position, images):
            Initialisiert Pac-Man mit Position, Geschwindigkeit, Bildern und Leben.

        create_pacman_from_matrix(mygame, images):
            Klassenmethode, die Pac-Man basierend auf der Matrix erstellt.

        move(mygame, keys):
            Bewegt Pac-Man basierend auf Nutzereingaben (Pfeiltasten).

        kill(mygame, sound):
            Reduziert die Anzahl der Leben um eins und setzt Pac-Man zurück.
    """

    def __init__(self, mygame, position, images):
        super().__init__(position, speed=mygame.convert_to_pixels(1) / 4, images=images)

        self.lives = 3

    @classmethod
    def create_pacman_from_matrix(cls, mygame, images):
        """
        Erstellt ein PacMan-Objekt basierend auf der Matrix.
        Der Wert 7 in der Matrix gibt die Startposition von Pac-Man an.
        """
        pacman_position = find_coordinates_of_value(mygame, 7)
        if pacman_position:
            start_pos = pacman_position[0]  # Es gibt nur einen Pac-Man
            return cls(mygame, position=start_pos, images=images)
        else:
            raise ValueError(
                "Pac-Man-Position (7) wurde in der Matrix nicht gefunden! Bitte füge in der Level-Datei einen Eintrag '7' hinzu, um die Startposition festzulegen.")

    def move(self, mygame, keys):
        """
        Bewegt Pac-Man basierend auf Nutzereingaben und Kollisionserkennung.

        :param matrix: Spielmatrix, die Wände und andere Felder darstellt.
        :param keys: Aktuelle Tasteneingaben (pygame.key.get_pressed()).
        """
        next_direction = self.current_direction
        # Nutzerinput: Richtung ändern
        if keys[pygame.K_UP]:
            next_direction = "up"
        elif keys[pygame.K_DOWN]:
            next_direction = "down"
        elif keys[pygame.K_LEFT]:
            next_direction = "left"
        elif keys[pygame.K_RIGHT]:
            next_direction = "right"

        # Richtung wechseln, wenn möglich
        if not next_direction == self.current_direction:
            if not check_collision_wall(mygame, next_direction, self.speed, self.pos, True):
                self.current_direction = next_direction

        # Bewegung ausführen, wenn möglich
        super().move(mygame, True)

    def kill(self, mygame, sound):
        self.lives -= 1
        super().kill(mygame, sound)


class Game:
    """
    Hauptklasse des Spiels. Verarbeitet den Spielfortschritt, verwaltet Entitäten, Ressourcen und Level.

    Attribute:
        config (dict): Konfigurationswerte des Spiels (aus config.json geladen).
        images (dict): Geladene Bilder für verschiedene Spielressourcen.
        sounds (dict): Geladene Sounds für das Spiel.
        pacman_images (dict): Bilder für Pac-Man in verschiedenen Richtungen.
        ghost_images (dict): Bilder für Geister im normalen und erschrockenen Zustand.
        item_images (dict): Bilder für Items (z. B. Punkte, Früchte, Pillen).
        pacman (Pacman): Instanz von Pac-Man.
        ghosts (list[Ghost]): Liste der Geister im aktuellen Level.
        matrix (list[list[int]]): Die aktuelle Spielmatrix des Levels.
        level (str): Aktuelles Level als String (z. B. "0").
        width (int): Breite des Spielfensters.
        height (int): Höhe des Spielfensters.
        tile_size (int): Größe eines Spielfelds in Pixeln.
        available_resolutions (list[list[int]]): Liste der verfügbaren Auflösungen.
        settings (dict): Einstellungen des Spiels (z. B. Lautstärke).
        score (int): Aktueller Punktestand.
        lives (int): Anzahl der verbleibenden Leben des Spielers.
        power_pill_active (bool): Gibt an, ob eine Kraftpille aktiv ist.
        power_pill_start_time (float): Zeitstempel für den Start der Kraftpillenwirkung.
        game_over (bool): Gibt an, ob das Spiel beendet ist.
        clock (pygame.time.Clock): Clock-Objekt für die FPS-Verwaltung.

    Methoden:
        __init__():
            Initialisiert das Spiel, lädt Konfigurationen, Bilder, Sounds und Entitäten.

        _load_pacman_images():
            Lädt die Pac-Man-Animationsbilder basierend auf der Konfiguration.

        _load_ghost_images():
            Lädt die Geisterbilder basierend auf der Konfiguration.

        _load_item_images():
            Lädt die Bilder für Items basierend auf der Konfiguration.

        _load_config_with_defaults(config_path):
            Lädt die Konfigurationsdatei und ergänzt fehlende Werte mit Standardwerten.

        _init_levels():
            Lädt die Spielmatrix für das aktuelle Level.

        _init_colors():
            Initialisiert die Farben basierend auf der Konfigurationsdatei.

        _init_fonts():
            Lädt die Schriftarten basierend auf der Konfiguration oder verwendet Standardwerte.

        _init_screen():
            Setzt das Spielfenster basierend auf der Auflösung.

        _init_music():
            Lädt und spielt die Hintergrundmusik.

        _init_background():
            Initialisiert die Hintergrundgeschwindigkeit und -position.

        _init_game_state():
            Initialisiert den Spielfortschritt und die FPS.

        _init_settings():
            Initialisiert Audioeinstellungen, Auflösung und Highscores.

        _scale_images():
            Skaliert Bilder (Pac-Man, Geister, Items, Hintergrund) basierend auf der Tile-Größe.

        adjust_resolution(direction):
            Ändert die Auflösung basierend auf der angegebenen Richtung (links/rechts).

        level_up():
            Wechselt zum nächsten Level oder beendet das Spiel, wenn keine weiteren Level vorhanden sind.

        kor(zahl):
            Konvertiert einen Matrixwert in Pixelkoordinaten.
    """

    def __init__(self):

        self.config = self._load_config_with_defaults("config.json")
        self._init_settings()
        self._init_colors()

        # Bilder und Sounds
        self.images = load_images_safe(self.config["images"])
        self.sounds = load_sounds_safe(self.config["sounds"])
        self.pacman_images = self._load_pacman_images()
        self.ghost_images = self._load_ghost_images()
        self.item_images = self._load_item_images()
        self._scale_images()

        self._init_fonts()
        self._init_screen()
        self._init_background()
        self._init_game_state()
        self._init_music()

        # Level und Entitäten laden
        self._init_levels()
        # Geister erstellen
        self.ghosts = Ghost.create_ghosts_from_matrix(self, self.ghost_images)

        # Pac-Man erstellen
        self.pacman = Pacman.create_pacman_from_matrix(
            self, self.pacman_images)

    def _load_pacman_images(self):
        """
        Lädt die Pac-Man-Animationsbilder basierend auf der Config.
        """
        pacman_images_config = self.config["images"]["pacman"]
        pacman_images = {}

        for direction, paths in pacman_images_config.items():
            pacman_images[direction] = [load_image_safe(
                path, self.YELLOW) for path in paths]

        return pacman_images

    def _load_ghost_images(self):
        """
        Lädt die Geisterbilder basierend auf der Config.
        """
        ghost_images_config = self.config["images"]["ghosts"]

        # Bilder für normale und erschreckte Geister laden
        ghost_images = {
            "normal": [load_image_safe(path) for path in ghost_images_config["normal"]],
            "frightened": load_image_safe(ghost_images_config["frightened"])
        }
        return ghost_images

    def _load_item_images(self):
        """
        Lädt die Item-Bilder basierend auf der Config.
        """
        item_images_config = self.config["images"]["items"]
        item_images = {}

        for item_name, path in item_images_config.items():
            item_images[item_name] = load_image_safe(
                path)  # Sichere Ladefunktion nutzen

        return item_images

    def _load_config_with_defaults(self, config_path):
        """
        Lädt die Konfigurationsdatei und ersetzt fehlende oder ungültige Werte durch Standardwerte.
        Fehlt ein Wert, wird die Konfigurationsdatei mit den Standardwerten ergänzt.

        :param config_path: Pfad zur Konfigurationsdatei.
        :return: Ein Dictionary mit Konfigurationswerten.
        """
        # Standardwerte
        default_config = {
            "colors": {
            "BACKGROUNDCOLOR": [9, 5, 27],
            "WHITE": [255, 255, 255],
            "YELLOW": [255, 204, 0],
            "GRAY": [100, 100, 100],
            "DARKGRAY": [90, 90,90],
            "RED": [255, 0, 0],
            "BLUE": [51, 173, 255
        ]
            },
            "fonts": {
            "main": "assets/font/ARCADE.TTF",
            "size_small": 40,
            "size_medium": 50,
            "size_large": 75
            },
            "levels":{
                "0": "assets/levels/lvl0.csv",
                "1": "assets/levels/lvl1.csv",
                "2": "assets/levels/lvl2.csv"
            },
            "images": {
            "pacman": {
                "up": ["assets/pacman-up/1.png", "assets/pacman-up/2.png", "assets/pacman-up/3.png"],
                "down": ["assets/pacman-down/1.png", "assets/pacman-down/2.png", "assets/pacman-down/3.png"],
                "left": ["assets/pacman-left/1.png", "assets/pacman-left/2.png", "assets/pacman-left/3.png"],
                "right": ["assets/pacman-right/1.png", "assets/pacman-right/2.png", "assets/pacman-right/3.png"]
            },
            "ghosts": {
                "normal": ["assets/ghosts/1.png", "assets/ghosts/2.png", "assets/ghosts/3.png", "assets/ghosts/4.png"],
                "frightened": "assets/ghosts/blue_ghost.png"
            },
            "items": {
                "dot_image": "assets/other/dot.png",
            "strawberry_image": "assets/other/strawberry.png",
            "apple_image": "assets/other/apple.png",
            "pill_image": "assets/other/pill.png"
            },
            "title_image": "assets/menu/logoYellow.png",
            "background_image_overlay1": "assets/menu/Moving.png",
            "background_image_overlay2": "assets/menu/MovingStars.png"
            },
            "sounds": {
            "chomp_sound": "assets/sounds/eating.mp3",
            "fruit_sound": "assets/sounds/eatingFruit.mp3",
            "game_over_sound": "assets/sounds/gameOver.mp3",
            "ghost_eaten_sound": "assets/sounds/ghostEaten.mp3",
            "ghosts_scared_sound": "assets/sounds/ghostsScared.mp3",
            "highscore_sound": "assets/sounds/highscore.mp3",
            "theme_sound": "assets/sounds/themeSound.mp3"
            },
            "music": {
            "main": "assets/sounds/pac-man_theme_remix.mp3"
            },
            "background": {
                "speed": 4,
                "speed_overlay": 1
            },
            "performance": {
                "FPS": 30
            },
            "audio": {
                "sound_volume": 0.5,
                "music_volume": 0.5
            },
            "resolution": {
                "default": [800, 600, 20],
                "options": [
                    [800, 600, 20],
                    [1280, 720, 25],
                    [1280, 800, 30],
                    [1920, 1080, 40]
                ]
            }
        }

        # Versuche, die Konfigurationsdatei zu laden
        try:
            with open(config_path, "r") as config_file:
                loaded_config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Fehler beim Laden der Konfiguration. Verwende Standardwerte.")
            with open(config_path, "w") as config_file:
                json.dump(default_config, config_file, indent=4)
            return default_config

        # Rekursive Funktion zum Überprüfen und Ergänzen von Defaults
        def merge_with_defaults(default, actual):
            if isinstance(default, dict):
                # Falls ein Wert ein Dictionary ist, rekursiv prüfen
                for key, value in default.items():
                    if key not in actual:
                        print(
                            f"Fehlender Schlüssel in der Konfiguration: {key}. Standardwert wird verwendet.")
                        actual[key] = value
                    else:
                        actual[key] = merge_with_defaults(value, actual[key])
            return actual

        # Die geladenen Werte mit den Standardwerten zusammenführen
        merged_config = merge_with_defaults(default_config, loaded_config)

        # Aktualisierte Konfiguration zurück in die Datei schreiben
        with open(config_path, "w") as config_file:
            json.dump(merged_config, config_file, indent=4)

        return merged_config


    def _init_levels(self):
        self.level = "0"
        self.matrix = load_level_from_csv(self.config["levels"][self.level])

    def _init_colors(self):
        # Farben aus der Konfiguration laden
        colors = self.config["colors"]
        self.BACKGROUNDCOLOR = tuple(colors["BACKGROUNDCOLOR"])
        self.WHITE = tuple(colors["WHITE"])
        self.YELLOW = tuple(colors["YELLOW"])
        self.GRAY = tuple(colors["GRAY"])
        self.DARKGRAY = tuple(colors["DARKGRAY"])
        self.BLUE = tuple(colors["BLUE"])
        self.RED = tuple(colors["RED"])

    def _init_fonts(self):
        try:
            font_path = self.config["fonts"]["main"]
            self.font = pygame.font.Font(
                font_path, self.config["fonts"]["size_medium"])
            self.title_font = pygame.font.Font(
                font_path, self.config["fonts"]["size_large"])
            self.credits_font = pygame.font.Font(
                font_path, self.config["fonts"]["size_small"])
        except:
            print(
                f"Ein Fehler ist beim Laden der Schriftart aufgetreten: Verwende Standard-Schriftart.")
            self.font = pygame.font.SysFont(
                "arial", self.config["fonts"]["size_medium"])
            self.title_font = pygame.font.SysFont(
                "arial", self.config["fonts"]["size_large"])
            self.credits_font = pygame.font.SysFont(
                "arial", self.config["fonts"]["size_small"])

    def _init_screen(self):
        self.screen = pygame.display.set_mode((self.width, self.height))

    def _init_music(self):
        path = self.config["music"]["main"]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.settings["music_volume"])
            pygame.mixer.music.play(-1)
        except:
            print("Fehler beim Laden der Hintergrundmusik")

    def _init_background(self):
        """
        Initialisiert die Hintergrundgeschwindigkeit basierend auf der Konfigurationsdatei.
        """
        config_background = self.config.get("background", {})
        self.background_x = 0
        self.background_x2 = 0
        self.background_speed = config_background.get(
            "speed", 4)  # Standardwert 4
        self.background_speed2 = config_background.get(
            "speed_overlay", 1)  # Standardwert 1

    def _init_game_state(self):
        """
        Initialisiert den Spielfortschritt und die FPS basierend auf der Konfigurationsdatei.
        """
        config_performance = self.config.get("performance", {})
        self.FPS = config_performance.get("FPS", 30)  # Standardwert 30

        # Spielzustand-Defaults
        self.power_pill_active = False
        self.power_pill_start_time = 0
        self.score = 0
        self.game_over = False

        self.clock = pygame.time.Clock()

    def _init_settings(self):
        """
        Initialisiert die Menüeinstellungen, Audio-Lautstärke und Auflösung basierend auf der Konfigurationsdatei.
        """
        # Input-Delay und Menü-Status
        self.last_input_time = 0
        self.input_delay = 0.2
        self.current_menu = "main"

        # Audio-Einstellungen aus der Konfigurationsdatei laden
        config_audio = self.config.get("audio", {})
        self.settings = {
            # Standardwert 0.5
            "sound_volume": config_audio.get("sound_volume", 0.5),
            # Standardwert 0.5
            "music_volume": config_audio.get("music_volume", 0.5)
        }

        # Auflösungswerte aus der Konfigurationsdatei laden

        config_resolution = self.config.get("resolution", {})
        default_resolution = config_resolution.get("default", [800, 600, 20])
        self.available_resolutions = config_resolution.get(
            "options", [[800, 600, 20]])  # Fallback-Werte
        self.width, self.height, self.tile_size = default_resolution
        self.screen = pygame.display.set_mode((self.width, self.height))
        assert all(len(
            res) == 3 for res in self.available_resolutions), "Alle Auflösungen müssen [width, height, tile_size] enthalten."

        # Einstellungen laden und ggf. überschreiben
        self.SETTINGS_FILE = "settings.csv"
        load_settings(self)  # Bestehende Einstellungen aus der Datei laden

        # Highscore-Datei initialisieren
        self.HIGHSCORES_FILE = "highscores.csv"
        self.highscores = []
        load_highscores(self)

    def _scale_images(self):
        """
        Skaliert alle Bilder (Pacman, Geister und Items) basierend auf der Tile-Größe.
        """
        # Skalierung für Pacman-Bilder
        for direction, frames in self.pacman_images.items():
            self.pacman_images[direction] = [
                pygame.transform.scale(frame, (self.tile_size, self.tile_size))
                for frame in frames
            ]

        # Skalierung für Geister-Bilder
        self.ghost_images["normal"] = [
            pygame.transform.scale(image, (self.tile_size, self.tile_size))
            for image in self.ghost_images["normal"]
        ]
        self.ghost_images["frightened"] = pygame.transform.scale(
            self.ghost_images["frightened"], (self.tile_size, self.tile_size)
        )

        # Skalierung für Item-Bilder
        for item, image in self.item_images.items():
            self.item_images[item] = pygame.transform.scale(
                image, (self.tile_size, self.tile_size)
            )

        # Skalierung für Hintergrund und Overlays
        new_width = self.width - 100
        new_height = int(self.images["title_image"].get_height() *
                         (new_width / self.images["title_image"].get_width()))
        self.images["title_image"] = pygame.transform.scale(
            self.images["title_image"], (new_width, new_height))

        for overlay_key in ["background_image_overlay1", "background_image_overlay2"]:
            new_height = self.height
            new_width = int(self.images[overlay_key].get_width() *
                            (new_height / self.images[overlay_key].get_height()))
            self.images[overlay_key] = pygame.transform.scale(
                self.images[overlay_key], (new_width, new_height))

    def adjust_resolution(self, direction):
        """
        Ändert die Bildschirmauflösung und passt die Tile-Größe an.

        :param direction: "left" oder "right", um durch die verfügbaren Auflösungen zu navigieren.
        """
        # Aktuelle Auflösung und Tile-Size suchen
        current_config = [self.width, self.height, self.tile_size]
        try:
            current_index = self.available_resolutions.index(current_config)
        except ValueError:
            print("Aktuelle Auflösung nicht in den verfügbaren Optionen. Standardauflösung wird verwendet.")
            current_index = 0

        # Neue Auflösung bestimmen
        if direction == "left":
            new_index = (current_index - 1) % len(self.available_resolutions)
        elif direction == "right":
            new_index = (current_index + 1) % len(self.available_resolutions)
        else:
            return  # Ungültige Richtung

        # Neue Auflösung setzen
        self.width, self.height, self.tile_size = self.available_resolutions[new_index]
        self.screen = pygame.display.set_mode((self.width, self.height))

        # Skaliere die Bilder erneut
        self._scale_images()

        # Einstellungen speichern
        save_settings(self)
        os.environ['SDL_VIDEO_CENTERED'] = '1' # Positioniert das Fenster in der Mitte des Monitors

    def level_up(self):
        # -1 da erstes lvl 0 ist
        if int(self.level) < (len(self.config["levels"]) - 1):
            self.level = str(int(self.level) + 1)
            try:
                self.matrix = load_level_from_csv(self.config["levels"][self.level])
                self.pacman = Pacman.create_pacman_from_matrix(
                self, self.pacman_images)
                self.pacman.lives += 1
                self.pacman.kill(self,"theme_sound") # stoppt kurz das Game
                self.ghosts = Ghost.create_ghosts_from_matrix(
                self, self.ghost_images)
            except FileNotFoundError:
                print(f"Level {self.level} konnte nicht geladen werden. Spiel wird beendet.")
                self.game_over = True
        else:
            self.game_over = True

    def convert_to_pixels(self, zahl):
        """Gibt Matrixstelle in Pixeln an."""
        zahl = zahl * self.tile_size
        return zahl

#############################################################################################################################################################

# Utility-Funktionen für Datenmanagement und Ressourcenverwaltung

def load_image_safe(file_path, fallback_color=(255, 0, 0)):
    """
    Lädt ein Bild sicher. Falls das Laden fehlschlägt, wird ein Platzhalterbild erstellt.

    :param file_path: Pfad zur Bilddatei.
    :param fallback_color: Farbe des Platzhalterbildes (RGB).
    :param size: Größe des Platzhalterbildes (Breite, Höhe).
    :return: Pygame Surface-Objekt (Bild oder Platzhalter).
    """
    try:
        return pygame.image.load(file_path)
    except:
        print(
            f"Warnung: Bild konnte nicht geladen werden: {file_path}. Platzhalter wird verwendet.")
        placeholder = pygame.Surface((20, 20))
        placeholder.fill(fallback_color)
        return placeholder


def load_images_safe(images_config):
    """
    Lädt Sounds sicher und gibt ein Dictionary mit den geladenen Sounds zurück.

    :param images_config: Dictionary mit Bildpfaden.
    :return: Dictionary mit geladenen Bildern.
    """
    loaded_images = {}
    for key, value in images_config.items():
        if isinstance(value, list):  # Für Listen von Pfaden (z. B. Animationen)
            loaded_images[key] = [load_image_safe(path) for path in value]
        elif isinstance(value, dict):  # Für verschachtelte Strukturen (z. B. Pacman, Ghosts)
            loaded_images[key] = load_images_safe(value)  # Rekursiver Aufruf
        else:  # Einzelne Pfade
            loaded_images[key] = load_image_safe(value)

    return loaded_images


def load_sounds_safe(sound_paths):
    """
    Lädt Sounds sicher und gibt ein Dictionary mit den geladenen Sounds zurück.

    :param sound_paths: Ein Wörterbuch mit den Soundnamen als Schlüssel und den Pfaden als Werte.
    :return: Ein Wörterbuch mit den geladenen Sounds oder None, falls ein Sound nicht geladen werden konnte.
    """
    sounds = {}
    for sound_name, sound_path in sound_paths.items():
        try:
            sounds[sound_name] = pygame.mixer.Sound(sound_path)
        except:
            print(
                f"Fehler beim Laden von Sound '{sound_name}' aus '{sound_path}'")
    return sounds


def load_level_from_csv(file_path):
    """
    Liest ein Level aus einer CSV-Datei ein und gibt die Level-Matrix zurück,
    wobei die Matrix mit einer Schicht von 3ern umrandet wird.

    :param file_path: Pfad zur CSV-Datei mit den Level-Daten.
    :return: Zweidimensionale Liste, die die umrandete Level-Matrix darstellt.
    """
    default_matrix = [[3, 3, 3, 3, 3, 3, 3, 3],
                      [3, 1, 1, 1, 1, 1, 1, 3],
                      [3, 1, 0, 0, 0, 0, 1, 3],
                      [3, 1, 0, 7, 0, 0, 1, 3],
                      [3, 1, 0, 0, 0, 0, 1, 3],
                      [3, 1, 1, 1, 1, 1, 1, 3],
                      [3, 3, 3, 3, 3, 3, 3, 3]]

    level_matrix = []
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                # Konvertiere jede Zeile in eine Liste von Integern, wenn sie nicht leer ist
                if row:
                    level_matrix.append([int(cell) for cell in row])

        # Überprüfe, ob alle Zeilen gleich lang sind
        if not all(len(row) == len(level_matrix[0]) for row in level_matrix):
            raise ValueError("Die CSV-Datei enthält ungleichmäßige Zeilen.")

        # Breite der Matrix bestimmen
        width = len(level_matrix[0]) if level_matrix else 0

        # Horizontale Ränder hinzufügen (oben und unten)
        horizontal_border = [3] * (width + 2)
        level_matrix.insert(0, horizontal_border)  # Oben
        level_matrix.append(horizontal_border)     # Unten

        # Vertikale Ränder hinzufügen (links und rechts)
        for i in range(1, len(level_matrix) - 1):
            level_matrix[i] = [3] + level_matrix[i] + [3]

    except FileNotFoundError:
        print(f"Fehler: Datei '{file_path}' wurde nicht gefunden.")
        return default_matrix
    except ValueError as ve:
        print(f"Fehler: {ve}")
        return default_matrix
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        return default_matrix

    return level_matrix


def save_settings(mygame):
    """
    Speichert die aktuellen Einstellungen des Spiels in einer CSV-Datei.

    :param mygame: Das Spielobjekt.
    """
    with open(mygame.SETTINGS_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        # Schreibe die Lautstärkeeinstellungen
        writer.writerow(["sound_volume", mygame.settings["sound_volume"]])
        writer.writerow(["music_volume", mygame.settings["music_volume"]])
        # Schreibe die Auflösungseinstellungen
        writer.writerow(["resolution_width", mygame.width])
        writer.writerow(["resolution_height", mygame.height])
        writer.writerow(["tile_size", mygame.tile_size])


def load_settings(mygame):
    """
    Lädt die Spieleinstellungen aus einer CSV-Datei.

    - Unterstützte Schlüssel: "sound_volume", "music_volume", "resolution_width", "resolution_height", "tile_size".
    - Wenn die Datei fehlt oder beschädigt ist, wird sie mit Standardwerten ersetzt.

    :param mygame: Instanz des Spiels.
    """

    if os.path.exists(mygame.SETTINGS_FILE):
        try:
            with open(mygame.SETTINGS_FILE, mode="r") as file:
                reader = csv.reader(file)
                for row in reader:
                    key, value = row
                    if key in ["sound_volume", "music_volume"]:
                        mygame.settings[key] = float(value)
                    elif key == "resolution_width":
                        mygame.width = int(value)
                    elif key == "resolution_height":
                        mygame.height = int(value)
                    elif key == "tile_size":
                        mygame.tile_size = int(value)
        except Exception as e:
            print(f"Warnung: Fehler beim Laden der Einstellungen: {e}")
            print("Beschädigte settings.csv wurde ersetzt.")
            os.remove(mygame.SETTINGS_FILE)
            save_settings(mygame)
    else:
        save_settings(mygame)


def save_highscores(mygame):
    with open(mygame.HIGHSCORES_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        for i in range(len(mygame.highscores)):
            writer.writerow(mygame.highscores[i])


def load_highscores(mygame):
    mygame.highscores.clear()
    if os.path.exists(mygame.HIGHSCORES_FILE):
        try:
            with open(mygame.HIGHSCORES_FILE, mode="r") as file:
                reader = csv.reader(file)
                for row in reader:
                    name, score = row
                    mygame.highscores.append((name, int(score)))
        except:
            os.remove(mygame.HIGHSCORES_FILE)
            load_highscores(mygame)
            print("Corupted highscore.csv was replaced")
    else:
        with open(mygame.HIGHSCORES_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows([["AAA", 1500], ["BBB", 1200], ["CCC", 900]])
        load_highscores(mygame)


def add_highscore(mygame, score):
    """Fügt einen neuen Highscore hinzu und fragt den Spielernamen ab."""
    # Erlaubte Zeichen
    ALLOWED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    # Namen abfragen (max. 3 Zeichen)
    name = ""
    input_active = True
    while input_active:
        draw_background(mygame)  # Hintergrund aktualisieren

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Eingabe abbrechen
                    return
                elif event.key == pygame.K_RETURN:  # Eingabe abschließen
                    if len(name) > 0:  # Eingabe nicht leer
                        input_active = False
                        mygame.last_input_time = time.time()  # Zeit des letzten Inputs speichern
                elif event.key == pygame.K_BACKSPACE:  # Zeichen löschen
                    name = name[:-1]
                elif event.unicode.upper() in ALLOWED_CHARS and len(name) < 3:  # Nur erlaubte Zeichen
                    name += event.unicode.upper()

        # Bildschirm aktualisieren
        game_over_text = mygame.title_font.render(
            "GAME OVER", True, mygame.YELLOW)
        score_text = mygame.font.render(
            f"Your Score: {score}", True, mygame.WHITE)
        prompt_text = mygame.font.render(
            "Enter Name (3 Letters):", True, mygame.WHITE)
        name_text = mygame.font.render(name, True, mygame.WHITE)

        # Texte anzeigen
        mygame.screen.blit(game_over_text, (mygame.width // 2 -
                           game_over_text.get_width() // 2, mygame.height // 6))
        mygame.screen.blit(score_text, (mygame.width // 2 -
                           score_text.get_width() // 2, mygame.height // 3))
        mygame.screen.blit(prompt_text, (mygame.width // 2 -
                           prompt_text.get_width() // 2, mygame.height // 2))
        mygame.screen.blit(name_text, (mygame.width // 2 -
                           name_text.get_width() // 2, mygame.height // 2 + 50))

        pygame.display.flip()

    # Highscore zur Liste hinzufügen und sortieren
    mygame.highscores.append((name, int(score)))
    mygame.highscores = sorted(mygame.highscores, key=lambda x: x[1], reverse=True)[
        :5]  # Nur Top 5 behalten
    save_highscores(mygame)


def find_coordinates_of_value(mygame, value):
    """
    Findet die Koordinaten aller Positionen in der Matrix, die den angegebenen Wert enthalten.

    :param mygame: Instanz des Spiels mit der Matrix-Attribut.
    :param value: Der Wert, nach dem gesucht werden soll (z. B. 7 für Pac-Man).
    :return: Liste der Koordinaten als [x, y], skaliert mit `mygame.convert_to_pixels()`.
    """

    coordinates = []
    for y, row in enumerate(mygame.matrix):
        for x, cell in enumerate(row):
            if cell == value:
                # (x, y) entspricht (Spalte, Zeile)
                coordinates.append([mygame.convert_to_pixels(x), mygame.convert_to_pixels(y)])
    return coordinates


#############################################################################################################################################################

# Menü handling:

def draw_background(mygame):
    """Zeichnet den animierten Hintergrund auf den Bildschirm."""
    overlay2 = mygame.images["background_image_overlay2"]
    overlay1 = mygame.images["background_image_overlay1"]

    # Statischer Hintergrund
    mygame.screen.fill(mygame.BACKGROUNDCOLOR)

    # Overlay 2 (langsam)
    mygame.background_x2 -= mygame.background_speed2
    if mygame.background_x2 <= -overlay2.get_width():
        mygame.background_x2 = 0
    mygame.screen.blit(overlay2,
                       (mygame.background_x2, 0))
    mygame.screen.blit(overlay2,
                       (mygame.background_x2 + overlay2.get_width(), 0))

    # Overlay 1 (schnell)
    mygame.background_x -= mygame.background_speed
    if mygame.background_x <= -overlay1.get_width():
        mygame.background_x = 0
    mygame.screen.blit(overlay1,
                       (mygame.background_x, 0))
    mygame.screen.blit(overlay1,
                       (mygame.background_x + overlay1.get_width(), 0))


def draw_menu_options(mygame, options, selected_option):
    """Zeichnet die Menüoptionen und hebt die ausgewählte hervor."""
    menu_spacing = 50  # Abstand zwischen den Optionen
    # Dynamisch berechneter Startpunkt (50px vom unteren Rand)
    menu_y_start = mygame.height - 50

    for i, option in enumerate(options):
        color = mygame.YELLOW if i == selected_option else mygame.GRAY
        option_text = mygame.font.render(option, True, color)
        option_rect = option_text.get_rect(midbottom=(
            mygame.width // 2, menu_y_start - i * menu_spacing))
        mygame.screen.blit(option_text, option_rect)


def draw_volume_bar(mygame, label, volume, y_position):
    """Zeichnet eine Lautstärkeleiste."""
    yellow_bars = int(10 * volume)
    white_bars = 10 - yellow_bars
    yellow_part = "X" * yellow_bars
    white_part = "X" * white_bars
    text = f"{label}: "
    text_surface = mygame.font.render(text, True, mygame.WHITE)
    text_surface1 = mygame.font.render(yellow_part, True, mygame.YELLOW)
    text_surface2 = mygame.font.render(white_part, True, mygame.WHITE)

    total_width = (text_surface.get_width() +
                   text_surface1.get_width() +
                   text_surface2.get_width())
    x_position = mygame.width // 2 - total_width // 2

    mygame.screen.blit(text_surface, (x_position, y_position))
    mygame.screen.blit(text_surface1,
                       (x_position + text_surface.get_width(), y_position))
    mygame.screen.blit(text_surface2,
                       (x_position + text_surface.get_width() + text_surface1.get_width(), y_position))


def draw_resolution_option(mygame):
    """
    Zeigt die aktuelle Bildschirmauflösung im Einstellungsmenü an.
    """
    resolution_text = f"RESOLUTION: {mygame.width}x{mygame.height}"
    resolution_surface = mygame.font.render(
        resolution_text, True, mygame.WHITE)
    mygame.screen.blit(resolution_surface, (mygame.width //
                       2 - resolution_surface.get_width() // 2, 250))


def draw_credits(mygame, line1, line2):
    """Zeichnet die Credits."""
    max_width = mygame.width - 40
    text_lines1 = wrap_text(line1, max_width, mygame.credits_font)
    text_lines2 = wrap_text(line2, max_width, mygame.credits_font)

    y_offset = mygame.height // 4
    for line in text_lines1 + text_lines2:
        text_surface = mygame.credits_font.render(line, True, mygame.WHITE)
        mygame.screen.blit(
            text_surface, (mygame.width // 2 - text_surface.get_width() // 2, y_offset))
        y_offset += text_surface.get_height() + 10


def draw_highscores(mygame):
    """Zeichnet die Highscores."""
    for i, (name, score) in enumerate(mygame.highscores[:10]):
        score_text = mygame.font.render(
            f"{i + 1}. {name} - {score}", True, mygame.WHITE)
        mygame.screen.blit(score_text, (mygame.width // 2 -
                                        score_text.get_width() // 2, 150 + i * 50))


def reset_confirmation(mygame):
    """Zeigt die Bestätigungsabfrage für das Resetten der Highscores."""
    confirmation_running = True
    options = ["YES", "NO"]
    selected_option = 1  # Standardmäßig "NO"

    while confirmation_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        # Tastatureingaben
        selected_option, confirmed, left_action, right_action = handle_menu_input(
            mygame, options, selected_option)

        if left_action or right_action:
            selected_option = (selected_option + 1) % len(options)

        if confirmed:
            if selected_option == 1:  # NO
                confirmation_running = False
            elif selected_option == 0:  # YES
                # Highscores löschen
                if os.path.exists(mygame.HIGHSCORES_FILE):
                    os.remove(mygame.HIGHSCORES_FILE)
                load_highscores(mygame)
                confirmation_running = False

        # Hintergrund zeichnen
        draw_background(mygame)

        # Bestätigungsfrage anzeigen
        confirmation_text = mygame.font.render(
            "Are you sure you want to", True, mygame.WHITE)
        confirmation_text2 = mygame.font.render(
            "reset all Highscores?", True, mygame.WHITE)
        mygame.screen.blit(confirmation_text, (mygame.width // 2 -
                           confirmation_text.get_width() // 2, mygame.height // 3))
        mygame.screen.blit(confirmation_text2, (mygame.width // 2 -
                           confirmation_text2.get_width() // 2, mygame.height // 3 + 50))

        # Optionen "YES" und "NO" nebeneinander anzeigen
        for i, option in enumerate(options):
            color = mygame.YELLOW if i == selected_option else mygame.GRAY
            option_text = mygame.font.render(option, True, color)
            x_position = mygame.width // 2 - 100 + i * 200  # Abstand zwischen den Optionen
            option_rect = option_text.get_rect(
                center=(x_position, mygame.height // 3 + 150))
            mygame.screen.blit(option_text, option_rect)

        pygame.display.flip()
        mygame.clock.tick(mygame.FPS)


def adjust_sound(mygame, change):
    """
    Passt die Lautstärke der Soundeffekte an.

    :param mygame: Das Spielobjekt.
    :param change: Die Änderung der Lautstärke (z. B. +0.1 oder -0.1).
    """
    # Lautstärke anpassen und innerhalb von 0.0 bis 1.0 begrenzen
    mygame.settings["sound_volume"] = max(
        0.0, min(1.0, mygame.settings["sound_volume"] + change))

    # Lautstärke für alle Sounds aktualisieren
    for sound_name in mygame.sounds:
        mygame.sounds[sound_name].set_volume(mygame.settings["sound_volume"])

    # Feedback-Sound abspielen
    if "chomp_sound" in mygame.sounds:
        mygame.sounds["chomp_sound"].play()

    save_settings(mygame)


def adjust_music(mygame, change):
    """
    Passt die Lautstärke für Musik an.

    :param mygame: Das Spielobjekt.
    :param change: Die Änderung der Lautstärke (z. B. +0.1 oder -0.1).
    """
    # Lautstärke anpassen und innerhalb von 0.0 bis 1.0 begrenzen
    mygame.settings["music_volume"] = max(
        0.0, min(1.0, mygame.settings["music_volume"] + change))

    pygame.mixer.music.set_volume(
        mygame.settings["music_volume"])  # Lautstärke aktualisieren

    save_settings(mygame)


def handle_menu_input(mygame, menu_options, selected_option):
    """
    Behandelt die Eingaben im Menü und gibt die aktualisierte Auswahl und Aktionen zurück.

    :param mygame: Das Spielobjekt.
    :param menu_options: Liste der Menüoptionen.
    :param selected_option: Der aktuell ausgewählte Menüpunkt.
    :return: Die aktualisierte Auswahl und welche Tasten gedrückt wurden (confirmed(Enter), left, right).
    """
    keys = pygame.key.get_pressed()
    current_time = time.time()

    # Navigation nach oben
    if keys[pygame.K_UP] and current_time - mygame.last_input_time > mygame.input_delay:
        selected_option = (selected_option + 1) % len(menu_options)
        mygame.last_input_time = current_time  # Zeit des letzten Inputs speichern

    # Navigation nach unten
    if keys[pygame.K_DOWN] and current_time - mygame.last_input_time > mygame.input_delay:
        selected_option = (selected_option - 1) % len(menu_options)
        mygame.last_input_time = current_time  # Zeit des letzten Inputs speichern

    # Auswahl bestätigen
    if keys[pygame.K_RETURN] and current_time - mygame.last_input_time > mygame.input_delay:
        mygame.last_input_time = current_time  # Zeit des letzten Inputs speichern
        return selected_option, True, False, False  # Auswahl getroffen

    # Links-Eingabe
    if keys[pygame.K_LEFT] and current_time - mygame.last_input_time > mygame.input_delay:
        mygame.last_input_time = current_time  # Zeit des letzten Inputs speichern
        return selected_option, False, True, False  # Left-Action

    # Rechts-Eingabe
    if keys[pygame.K_RIGHT] and current_time - mygame.last_input_time > mygame.input_delay:
        mygame.last_input_time = current_time  # Zeit des letzten Inputs speichern
        return selected_option, False, False, True  # Right-Action

    return selected_option, False, False, False  # Keine Aktion


def wrap_text(text, max_width, font):
    """Hilfsfunktion zum Umbruch von Text."""
    words = text.split(' ')
    lines, current_line = [], ""
    for word in words:
        if font.size(current_line + ' ' + word)[0] <= max_width:
            current_line += ' ' + word
        else:
            lines.append(current_line.strip())
            current_line = word
    if current_line:
        lines.append(current_line.strip())
    return lines


def open_menu(mygame, menu):
    """"Zeigt die Menüs an und handelt den input"""
    selected_option = 0  # Standardmäßig auf "BACK"
    options = ["BACK"]

    if menu == "HIGHSCORES":
        options.append("RESET")
    if menu == "CREDITS":
        # Der Text für die Credits
        credits_text1 = "Thank you for Playing!"
        credits_text2 = "This game was developed by Riley as part of a DHBW programming assignment, supervised by Prof. V. Schenk. I do not own any copyrights to the music nor the images."
    if menu == "SETTINGS":
        options.extend(["< RESOLUTION >", "< SOUND >", "< MUSIC >"])

    title = menu
    running = True
    while running:
        # Hintergrund zeichnen
        draw_background(mygame)
        # Titel zeichnen
        title_text = mygame.title_font.render(title, True, mygame.WHITE)
        mygame.screen.blit(title_text, (mygame.width // 2 -
                           title_text.get_width() // 2, 50))

        if menu == "HIGHSCORES":
            draw_highscores(mygame)

        if menu == "CREDITS":
            draw_credits(mygame, credits_text1, credits_text2)

        if menu == "SETTINGS":
            draw_volume_bar(mygame, "MUSIC",
                            mygame.settings["music_volume"], 150)
            draw_volume_bar(mygame, "SOUND",
                            mygame.settings["sound_volume"], 200)
            draw_resolution_option(mygame)

        draw_menu_options(mygame, options, selected_option)

        running = handle_exit()

        # Tastatureingaben
        selected_option, confirmed, left_action, right_action = handle_menu_input(
            mygame, options, selected_option)

        if confirmed:
            if selected_option == 0:  # QUIT
                running = False  # Zurück ins Menü
            if menu == "HIGHSCORES":
                if selected_option == 1:  # RESET HIGHSCORES
                    reset_confirmation(mygame)  # Bestätigungsabfrage
        elif left_action and menu == "SETTINGS":
            if selected_option == 1:  # Resolution anpassen
                mygame.adjust_resolution("left")
            elif selected_option == 3:  # Decrease Music
                adjust_music(mygame, -0.1)
            elif selected_option == 2:  # Decrease Sound
                adjust_sound(mygame, -0.1)
        elif right_action and menu == "SETTINGS":
            if selected_option == 1:  # Resolution anpassen
                mygame.adjust_resolution("right")
            elif selected_option == 3:  # Increase Music
                adjust_music(mygame, 0.1)
            elif selected_option == 2:  # Increase Sound
                adjust_sound(mygame, 0.1)

        pygame.display.flip()
        mygame.clock.tick(mygame.FPS)


def main_menu(mygame):

    for sound_name in mygame.sounds:
        mygame.sounds[sound_name].set_volume(mygame.settings["sound_volume"])

    menu_options = ["QUIT", "CREDITS", "SETTINGS", "HIGHSCORES", "START GAME"]
    selected_option = 4  # Index der aktuell ausgewählten Option
    running = True


    while running:

        draw_background(mygame)  # Zeichne den animierten Hintergrund
        # Überschrift
        image_y_offset = 100
        mygame.screen.blit(mygame.images["title_image"], (mygame.width // 2 -
                           mygame.images["title_image"].get_width() // 2, image_y_offset))
        draw_menu_options(mygame, menu_options, selected_option)
        pygame.display.flip()

        running = handle_exit()
        selected_option, confirmed, l, r = handle_menu_input(
            mygame, menu_options, selected_option)
        if confirmed:
            if selected_option == 4:  # "Start Game"
                running = False
                start_game(mygame)
            elif selected_option == 3:  # "Highscore"
                open_menu(mygame, "HIGHSCORES")
            elif selected_option == 2:  # "Settings"
                open_menu(mygame, "SETTINGS")
            elif selected_option == 1:  # "Credits"
                open_menu(mygame, "CREDITS")
            elif selected_option == 0:  # "Quit"
                pygame.quit()
                sys.exit()


#######################################################################################################################################################

# Game logic

def draw_hud(mygame, current_score, elapsed_time, highscore):
    """
    Zeichnet das HUD (Heads-Up Display), das dynamisch an die Bildschirmauflösung angepasst wird.

    :param mygame: Das Spielobjekt.
    :param current_score: Der aktuelle Punktestand.
    :param elapsed_time: Die vergangene Spielzeit.
    :param highscore: Der aktuelle Highscore.
    """
    # Dynamische Skalierungsfaktoren basierend auf der Auflösung
    scale_factor_x = mygame.width / 800  # Basisbreite ist 800
    scale_factor_y = mygame.height / 600  # Basishöhe ist 600

    # Position und Abstand anpassen
    start_x = int(10 * scale_factor_x)
    y_position = int(10 * scale_factor_y)
    spacing = int(240 * scale_factor_x)

    # Dynamische Schriftgrößen
    font_size = int(mygame.config["fonts"]["size_small"] * scale_factor_y)
    dynamic_font = pygame.font.Font(mygame.config["fonts"]["main"], font_size)

    # Texte rendern
    score_text = dynamic_font.render(
        f"Score: {current_score}", True, mygame.WHITE)
    timer_text = dynamic_font.render(
        f"Time: {elapsed_time}s", True, mygame.WHITE)
    highscore_text = dynamic_font.render(
        f"Highscore: {highscore}", True, mygame.WHITE)
    life_text = dynamic_font.render(
        f"Lifes: {mygame.pacman.lives}", True, mygame.WHITE)

    # Texte anzeigen
    mygame.screen.blit(score_text, (start_x, y_position))
    mygame.screen.blit(timer_text, (start_x + spacing, y_position))
    mygame.screen.blit(highscore_text, (start_x + 2 * spacing, y_position))
    mygame.screen.blit(
        life_text,
        (start_x, mygame.height - life_text.get_height() - y_position),
    )


def draw_game_field(mygame):
    """
    Zeichnet das Spielfeld in der Mitte des Bildschirms.
    """
    # Spielfeldgröße in Pixeln berechnen
    field_width = len(mygame.matrix[0]) * mygame.convert_to_pixels(1)  # Breite in Pixel
    field_height = len(mygame.matrix) * mygame.convert_to_pixels(1)   # Höhe in Pixel

    # Offset für zentrierte Position
    offset_x = (mygame.width - field_width) // 2
    offset_y = (mygame.height - field_height) // 2

    # Spielfeld zeichnen
    for y, row in enumerate(mygame.matrix):
        for x, cell in enumerate(row):
            draw_x = offset_x + x * mygame.convert_to_pixels(1)
            draw_y = offset_y + y * mygame.convert_to_pixels(1)

            if cell == 1:  # Wand
                pygame.draw.rect(mygame.screen, mygame.BLUE, [
                                 draw_x, draw_y, mygame.convert_to_pixels(1), mygame.convert_to_pixels(1)])
            elif cell == 0:  # Punkt
                mygame.screen.blit(
                    mygame.item_images["dot_image"], (draw_x, draw_y))
            elif cell == -3:  # Kraftpille
                mygame.screen.blit(
                    mygame.item_images["pill_image"], (draw_x, draw_y))
            elif cell == -2:  # Frucht
                mygame.screen.blit(
                    mygame.item_images["apple_image"], (draw_x, draw_y))


def draw_characters(mygame, animation_index):
    """
    Zeichnet Pac-Man und die Geister basierend auf ihren Positionen und der aktuellen Animation.
    Zentriert die Charaktere relativ zum Spielfeld.
    """
    # Berechne Offsets für zentrierte Darstellung
    offset_x = (mygame.width - len(mygame.matrix[0]) * mygame.convert_to_pixels(1)) // 2
    offset_y = (mygame.height - len(mygame.matrix) * mygame.convert_to_pixels(1)) // 2

    # Pac-Man zeichnen
    pacman_image = mygame.pacman.images[mygame.pacman.current_direction][animation_index]
    mygame.screen.blit(
        pacman_image,
        (offset_x + mygame.pacman.pos[0], offset_y + mygame.pacman.pos[1])

    )

    # Geister zeichnen
    for ghost in mygame.ghosts:
        ghost_image = ghost.image if not ghost.frightened else ghost.image_frightened
        mygame.screen.blit(
            ghost_image,
            (offset_x + ghost.pos[0], offset_y + ghost.pos[1])
        )


def draw_ready(mygame):
    """
    Zeigt den "Ready?"-Text dynamisch zentriert auf dem Spielfeld an,
    angepasst an die Spielfeldgröße.

    :param mygame: Das Spielobjekt.
    """
    # Berechnung der Schriftgröße basierend auf Spielfeldhöhe
    dynamic_font_size = int(len(mygame.matrix) * mygame.convert_to_pixels(1) * 0.2)  # 20% der Spielfeldhöhe
    dynamic_font = pygame.font.Font(mygame.config["fonts"]["main"], dynamic_font_size)

    # Text rendern
    game_over_text = dynamic_font.render("Ready?", True, mygame.YELLOW)

    # Zentrierte Position basierend auf Spielfeld
    offset_x = (mygame.width - len(mygame.matrix[0]) * mygame.convert_to_pixels(1)) // 2
    offset_y = (mygame.height - len(mygame.matrix) * mygame.convert_to_pixels(1)) // 2

    text_x = offset_x + (len(mygame.matrix[0]) * mygame.convert_to_pixels(1)) // 2 - game_over_text.get_width() // 2
    text_y = offset_y + (len(mygame.matrix) * mygame.convert_to_pixels(1)) // 2 - game_over_text.get_height() // 2

    mygame.screen.blit(game_over_text, (text_x, text_y))


def update_ghosts(mygame):
    """
    Aktualisiert die Bewegung und den Zustand der Geister im Spiel.
    """
    for ghost in mygame.ghosts:
        # Respawn nach 3 Sekunden
        if not ghost.alive and (time.time() - ghost.respawn_time > 3):
            ghost.respawn()
        elif ghost.alive:
            ghost.move(mygame)


def check_for_teleport(mygame, pos, direction):
    """
    Prüft, ob sich eine Entität auf einem Teleporter befindet und führt die Teleport-Logik aus.

    :param mygame: Das Spielobjekt.
    :param pos: Die aktuelle Position der Entität (z. B. Pac-Man oder Geist).
    :param direction: Die Bewegungsrichtung der Entität.
    :return: True, wenn teleportiert wurde, False andernfalls.
    """
    x, y = pos

    # Prüfen, ob die aktuelle Position ein Teleporter ist (3 in der Matrix)
    if mygame.matrix[int(y / mygame.convert_to_pixels(1))][int(x / mygame.convert_to_pixels(1))] == 3:
        if direction == "right":
            pos[0] = mygame.convert_to_pixels(1)  # Teleportiere zur linken Seite
        elif direction == "left":
            # Teleportiere zur rechten Seite
            pos[0] = mygame.convert_to_pixels(len(mygame.matrix[0]) - 2)
        elif direction == "up":
            # Teleportiere nach unten
            pos[1] = mygame.convert_to_pixels(len(mygame.matrix) - 2)
        elif direction == "down":
            pos[1] = mygame.convert_to_pixels(1)  # Teleportiere nach oben
        return True  # Teleportiert
    return False  # Keine Teleportation


def collision_pacman_ghost(mygame, pacman, ghosts):
    """
    Überprüft und behandelt die Kollision zwischen Pac-Man und den Geistern.

    Diese Funktion prüft, ob sich Pac-Man und ein Geist überlappen. Je nach Zustand
    des Geistes (`frightened`) wird der Geist "gefressen" oder Pac-Man verliert ein Leben.
    Bei einer verlorenen Kollision werden die Geister zurückgesetzt, und bei Verlust
    aller Leben wird das Spiel beendet.

    :param mygame: Das Spielobjekt, das die Spiellogik und Zustände enthält.
    :param pacman: Das Pac-Man-Objekt, das die Position und Attribute von Pac-Man enthält.
    :param ghosts: Liste der Geisterobjekte, die im Spiel aktiv sind.

    """

    pacman_rect = pygame.Rect(pacman.pos[0], pacman.pos[1], mygame.convert_to_pixels(
        1), mygame.convert_to_pixels(1))  # Pacman-Kollisionsbox
    for ghost in ghosts:
        ghost_rect = pygame.Rect(ghost.pos[0], ghost.pos[1], mygame.convert_to_pixels(
            1), mygame.convert_to_pixels(1))  # Geist-Kollisionsbox
        if pacman_rect.colliderect(ghost_rect):  # Kollision festgestellt
            if ghost.frightened:
                # Geist wird bei Kraftpillen-Effekt "gefressen"
                ghost.kill(mygame, "ghost_eaten_sound")
                mygame.score += 200  # Punkte für den besiegten Geist
            else:
                # Pac-Man verliert ein Leben
                pacman.kill(mygame, "game_over_sound")
                ghosts.clear()
                ghosts.extend(Ghost.create_ghosts_from_matrix(
                    mygame, mygame.ghost_images))
                # Pac-Man zurücksetzen
                mygame.power_pill_active = False
                if mygame.pacman.lives <= 0:
                    mygame.game_over = True  # Spiel beenden



def check_collision_wall(mygame, direction, speed, pos, is_pacman=False):
    """
    Überprüft, ob die Bewegung in eine Richtung durch eine Wand blockiert wird.

    :param matrix: Die Spielmatrix.
    :param direction: Die Bewegungsrichtung ("up", "down", "left", "right").
    :param speed: Die Bewegungsgeschwindigkeit.
    :param pos: Die aktuelle Position des Objekts.
    :param is_pacman: True wenn es Pacman ist, default False
    :return: True, wenn die Bewegung blockiert ist, False andernfalls.
    """
    position = pos
    size = mygame.convert_to_pixels(1)
    matrix = mygame.matrix

    # Pac-Man's zukünftige Position basierend auf Richtung berechnen
    if direction == "up":
        rect = pygame.Rect(position[0], position[1] - speed, size, size)
    elif direction == "down":
        rect = pygame.Rect(position[0], position[1] + speed, size, size)
    elif direction == "left":
        rect = pygame.Rect(position[0] - speed, position[1], size, size)
    elif direction == "right":
        rect = pygame.Rect(position[0] + speed, position[1], size, size)
    else:
        return False  # Keine Bewegung, keine Kollision

    # Kollision mit Wänden und Teleporten überprüfen
    for y in range(len(matrix)):
        for x in range(len(matrix[0])):
            if matrix[y][x] == 1:  # 1 ist Wand
                wall_rect = pygame.Rect(mygame.convert_to_pixels(x), mygame.convert_to_pixels(
                    y), mygame.convert_to_pixels(1), mygame.convert_to_pixels(1))
                if rect.colliderect(wall_rect):
                    return True  # Kollision mit Wand
            if matrix[y][x] == 2 and is_pacman:
                wall_rect = pygame.Rect(mygame.convert_to_pixels(x), mygame.convert_to_pixels(
                    y), mygame.convert_to_pixels(1), mygame.convert_to_pixels(1))
                if rect.colliderect(wall_rect):
                    return True  # Kollision mit unsichtbarer Wand für den Geister Hud
    return False  # Keine Kollision


def activate_power_pill(mygame):
    """Aktiviert den Power-Pill-Effekt und versetzt Geister in den 'frightened'-Zustand."""
    if not mygame.power_pill_active:  # Zweites Fressen einer Power-Pille verlischt
        mygame.power_pill_active = True
        # Zeitpunkt der Aktivierung speichern
        mygame.power_pill_start_time = time.time()
        for ghost in mygame.ghosts:
            # Geister in den 'frightened'-Zustand versetzen
            ghost.frightened = True
            # Geister werden langsamer während des Power-Pill-Effekts
            ghost.speed /= 2


def update_power_pill(mygame):
    """Aktualisiert den Zustand der Kraftpille."""
    if mygame.power_pill_active and (time.time() - mygame.power_pill_start_time > 5):  # Effekt dauert 8 Sekunden
        for ghost in mygame.ghosts:
            if ghost.frightened:
                # Geister kehren zurück zu ihrer normalen Geschwindigkeit und normalem Zustand
                ghost.frightened = False
                # Geister zurück auf ihre ursprüngliche Geschwindigkeit setzen
                ghost.speed = ghost.original_speed
        mygame.power_pill_active = False


def handle_exit():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False  # Spiel beenden
    return True


def handle_collisions_and_points(mygame, current_score):
    pacman_x, pacman_y = int(
        mygame.pacman.pos[0] / mygame.convert_to_pixels(1)), int(mygame.pacman.pos[1] / mygame.convert_to_pixels(1))
    if mygame.matrix[pacman_y][pacman_x] == 0:  # Dot fressen
        if "chomp_sound" in mygame.sounds:
            mygame.sounds["chomp_sound"].play()
        current_score += 10
        mygame.matrix[pacman_y][pacman_x] = -1
        if not any(0 in row for row in mygame.matrix):  # Alles Dots wurden gefressen
            return True, current_score
    elif mygame.matrix[pacman_y][pacman_x] == -2:  # Frucht fressen
        if "fruit_sound" in mygame.sounds:
            mygame.sounds["fruit_sound"].play()
        current_score += 100
        mygame.matrix[pacman_y][pacman_x] = -1
    elif mygame.matrix[pacman_y][pacman_x] == -3:  # Kraftpille fressen
        activate_power_pill(mygame)
        if "ghosts_scared_sound" in mygame.sounds:
            mygame.sounds["ghosts_scared_sound"].play()
        mygame.matrix[pacman_y][pacman_x] = -1
    return False, current_score


def place_fruits(mygame, fruit_count):
    if fruit_count < 2 and random.randint(0, 200) == 0:
        x = random.randint(0, len(mygame.matrix) - 1)
        y = random.randint(0, len(mygame.matrix[0]) - 1)
        if mygame.matrix[x][y] < 1:
            mygame.matrix[x][y] = -2  # Früchtchen
            fruit_count += 1
    return fruit_count


def handle_background(mygame):
    """
    Füllt den Hintergrund basierend auf dem Zustand der Kraftpille.
    """
    if not mygame.power_pill_active:
        mygame.screen.fill(mygame.BACKGROUNDCOLOR)
    else:
        mygame.screen.fill(mygame.DARKGRAY)

def handle_pacman_logic(mygame):
    """
    Verarbeitet die Logik von Pac-Man, einschließlich Bewegung und Respawn.
    """
    keys = pygame.key.get_pressed()
    if not mygame.pacman.alive and (time.time() - mygame.pacman.respawn_time > 3):
        mygame.pacman.respawn()
    elif mygame.pacman.alive:
        mygame.pacman.move(mygame, keys)
        update_ghosts(mygame)
    else:
        draw_ready(mygame)

def update_highscore(mygame, current_score, highscore, already_highcore):
    """
    Aktualisiert den Highscore, wenn der aktuelle Punktestand ihn übertrifft.
    """
    if current_score > highscore and not already_highcore:
        if "highscore_sound" in mygame.sounds:
            mygame.sounds["highscore_sound"].play()
        return True


def play_game(mygame):
    animation_index = 0
    animation_delay = 3
    frame_count = 0
    highscore = int(mygame.highscores[0][1])
    fruit_count = 0
    already_highcore = False
    current_score = 0
    start_time = pygame.time.get_ticks()
    running = True

    while running:

        handle_background(mygame)
        draw_game_field(mygame)

        if not handle_exit():
            running = False

        draw_characters(mygame, animation_index)
        handle_pacman_logic(mygame)
        collision_pacman_ghost(mygame, mygame.pacman, mygame.ghosts)

        check_for_teleport(mygame, mygame.pacman.pos, mygame.pacman.current_direction)
        update_power_pill(mygame)

        game_won, current_score = handle_collisions_and_points(mygame, current_score)
        if game_won:
            mygame.level_up()

        fruit_count = place_fruits(mygame, fruit_count)
        if mygame.game_over:
            running = False

        elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
        draw_hud(mygame, current_score, elapsed_time, highscore)
        if update_highscore(mygame, current_score, highscore, already_highcore):
            already_highcore = True

        pygame.display.flip()
        mygame.clock.tick(mygame.FPS)

        frame_count += 1
        if frame_count >= animation_delay:
            animation_index = (animation_index + 1) % len(mygame.pacman.images[mygame.pacman.current_direction])
            frame_count = 0

    return current_score


def start_game(mygame):
    mygame.level_up()
    score = play_game(mygame)  # Spiel starten und Score zurückgeben
    add_highscore(mygame, score)  # Highscore hinzufügen
    newgame = Game()  # neues Spiel laden
    main_menu(newgame)


def main():
    """Pygame iniziirung und Hauptmenü"""

    # Initialisierung
    os.environ['SDL_VIDEO_CENTERED'] = '1' # Positioniert das Fenster in der Mitte des Monitors
    pygame.init()
    pygame.mixer.init()  # Initialisiere die Sound-Bibliothek
    mygame = Game()
    pygame.display.set_caption("Pac-Man")
    main_menu(mygame)


# Programm starten
if __name__ == "__main__":
    main()