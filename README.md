# Fontänensteuerung
Remote Steuerung der Wasserfontänen in der historischen Schlossanlage Schleißheim bei München. Die analoge/ursprüngliche Steuerung wird mit Schlüsselschaltern bedient. Die neue Remote Steuerung verfügt über drei Motoren, die die Schlüssel der originalen Schlüsselschalter drehen, um Eingriffe in die historische / bisherige Steuerungsanlage zu vermeiden.

## Systemübersicht
### Komponenten:
Drei Motoren zur Steuerung der Fontänen.
Jede Einheit (Motor, Taster, LEDs) besteht aus:
3 Taster (Handbetrieb, Aus, Automatikbetrieb)
3 Zustands-LEDs (Handbetrieb, Aus, Automatikbetrieb)
1 Aktivitäts-LED
Eine zusätzliche Fehler-LED
Jeweils 3 Mikroschalter pro Motor für die Positionsüberwachung, zwei davon als Endlagenschalter verkabelt
Raspberry Pi 4 als zentrale Steuereinheit.
1 Adafruit Motor Hat
1 Adafruit MCP23017 Board
1 StromPi 3 um die 12 V Versorgung, die für die Motoren benüötigt wird, auch für den Raspberry nutzen zu können.

### Steuerungsmethoden
Vor-Ort-Benutzung: Taster an der Steuerungseinheit.
Remote-Benutzung: Kommunikation über einen Cloud MQTT Broker
Interne Kommunikation: Lokaler MQTT Broker zur Sicherstellung der Funktionalität auch bei fehlender Internetverbindung.

## Benennung und Funktionen
### Einheiten:
FOB: Fontänen oberes Becken
FUB: Fontänen unteres Becken
FPA: Fontänen Parterre

### Zustände:
Automatikbetrieb (AUTO)
Handbetrieb (HAND)
Aus (OFF)
Blockiert (BLOCKED)
Fehler (ERROR)

## Steuerkommandos
### MQTT Nachrichtenschema:
#### 3 Zeichen (e.g., "a0H"):
Zeichen 1: Motor für oberes Becken
Zeichen 2: Motor für unteres Becken
Zeichen 3: Motor für Parterre

#### Zeichenbedeutungen:
a: Automatik
h: Handbetrieb
0: Aus
b: Motor blockieren
u: Motor entblockieren
-: Keine Aktion

### Sonderkommandos:
shutdown: Raspberry Pi herunterfahren
hey: Status als SMS zurücksenden


## Konfigurationsdatei (JSON)
### Lokaler MQTT Broker:
IP Adresse
Port
User
Passwort

### Cloud MQTT Broker:
Webadresse
Port
User
Passwort

### MCP23017 Konfiguration:

I2C Adresse sowie GPIO Port Nummern für die LEDs der Einheiten FOB, FUB, FPA und Fehler-LED
I2C Adresse sowie GPIO Port Nummern für die Taster der Einheiten FOB, FUB, FPA

### Autorisierung:
Liste von Mobiltelefonnummern, IMEIs der berechtigten externen Nutzer

## User Stories
### Vor-Ort-Benutzung:
Benutzer schaltet Motoren vor Ort von Automatik auf Handbetrieb.
Motoren durchlaufen den Zustand "Aus" und warten jeweils eine Minute zwischen den Zustandswechseln.

### Remote-Benutzung:
Benutzer schickt eine MQTT Nachricht, um die Zustände der Motoren zu ändern.
Motoren durchlaufen Zustände basierend auf den empfangenen Befehlen, inklusive Übergangszeiten und Wartezeiten.

### Gleichzeitige Bedienung:
Kombination von Vor-Ort-Bedienung und Remote-Bedienung.
Priorisierung und Abarbeitung der Befehle in der Reihenfolge ihres Eingangs, unter Berücksichtigung von Wartezeiten.

# Software Architektur

## Komponentenübersicht
### Hauptkomponenten
FS_Communication: Verwaltung der Kommunikation mit der Außenwelt über MQTT.
MotorStateMachine: Verwaltung der Zustände der einzelnen Motoren.
FS_Files: Verwaltung der Konfigurationsdatei (JSON) zur Speicherung und Abfrage von Konfigurationsdaten.
Main-Skript: Initialisierung und Orchestrierung der Komponenten.

### Externe Systeme
Lokaler MQTT Broker: Zur internen Kommunikation zwischen den Prozessen auf dem Raspberry Pi.
Cloud MQTT Broker: Für die externe Kommunikation, z.B. für das Empfangen von Steuerkommandos und das Senden von Statusmeldungen.

## Datenfluss
### Initialisierung
#### Konfiguration laden:
Das Main-Skript lädt die Konfigurationsdaten über die FS_Files Klasse.

#### MQTT-Clients initialisieren:
Der FS_Communication-Client wird mit den Konfigurationsdaten für den lokalen und den Cloud MQTT Broker initialisiert.

#### Zustandsmaschinen initialisieren:
Die MotorStateMachine-Instanzen werden für jede Fontäne initialisiert und mit dem FS_Communication-Client verknüpft.

### Steuerung und Kommunikation
#### Empfangen von Kommandos:
Der FS_Communication-Client abonniert relevante Themen beim MQTT Broker.
Bei Empfang eines Kommandos wird die command_callback-Funktion aufgerufen.

#### Verarbeitung von Kommandos:
Die command_callback-Funktion parst das empfangene Kommando und leitet es an die entsprechende MotorStateMachine weiter.
Die MotorStateMachine führt die Zustandsübergänge basierend auf dem empfangenen Kommando durch.

#### Zustandsübergänge:
Die MotorStateMachine aktualisiert den Motorzustand und triggert die entsprechenden Aktionen (z.B. Motorsteuerung und LED-Steuerung) über MQTT.
Wartezeiten und Übergänge werden intern verwaltet.

## Systeminteraktionen
### Interne Kommunikation
#### Lokaler MQTT Broker:
Dient der Kommunikation zwischen den verschiedenen Prozessen auf dem Raspberry Pi.
Beispiel: Ein Prozess kann eine Nachricht veröffentlichen, um den Zustand eines Motors zu ändern.

#### Externe Kommunikation
Cloud MQTT Broker:
Ermöglicht die Steuerung der Fontänen über externe Geräte (z.B. Smartphones).
Beispiel: Ein Benutzer sendet ein Kommando über den Cloud MQTT Broker, welches vom FS_Communication-Client empfangen und verarbeitet wird.

## Fehlerbehandlung und Überwachung
### Systemd:
Alle notwendigen Prozesse werden beim Booten des Raspberry Pi gestartet und überwacht.
Bei einem Absturz wird der Prozess neu gestartet.
Bei wiederholtem Absturz wechselt das System in den Fehlerzustand und ignoriert weitere Kommandos.

### Logging:
Umfassendes Logging zur Fehlerdiagnose, Überwachung und Debugging.
Protokolliert wichtige Ereignisse, Zustandsübergänge und Fehler.

## Konfigurationsmanagement
### FS_Files:
Lädt die Konfiguration aus einer JSON-Datei.
Bietet Funktionen zum Lesen und Aktualisieren einzelner Konfigurationswerte.
Unterstützt die Verwaltung autorisierter Benutzer und die Aktualisierung der Konfigurationsdatei.

# Technische Umsetzung

## Motorenansteuerung
### Endlagenschalter
An den beiden Endpositionen (Automatik und Handbetrieb) sorgen Endlagenschalter dafür, dass sich der Motor durch Mikroschalter, die den Stromkreis unterbrechen, nicht mehr weiter in diese Richtung bewegen kann. Über entsprechend geschaltete Dioden Parallel zu den Kontakten NO und NC des Mikroschalters sorgen dafür, dass sich der Motor in die andere Richtung gewegen kann.

Das Prinzip wird hier erklärt https://sgs-electronic.de/tipps-und-tricks/fo-modul/anschluss-von-endlagenschaltern

### Mittelschalter

Die Position Aus liegt mittig zwischen den beiden Endpositionen. Hier wird ein Mikroschalter bei der Motorbewegung permanent abgefragt, um an der Mittelposition, die durch Betätigen des Mittelschalters markiert wird, anhält. Dies ist rein softwaregesteuert.

### Getriebemotoren stoppen nicht sofort - Nachlauf
Dieses Problem muss über entsprechend Positionierung der Mikroschalter und geringe Motorgeschwindigkeiten gelöst werden.
