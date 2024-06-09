#!/bin/bash
# 
# Installieren der Fontänensteuerung
#

# Alle Ausgaben zusätzlich in ein Logfile schreiben
LOG_FILE="$HOME/install_FontaenenSteuerung.log"
ip_address=$(hostname -I | awk '{print $1}')

# Schreibe die Raspberry Pi Revision und IP-Adresse ins Logfile
{
    echo "------------------------------------------------------------"
    echo "Inhalt von /proc/cpuinfo:"
    echo "------------------------------------------------------------"
	cat /proc/cpuinfo
    echo "------------------------------------------------------------"
    echo "IP-Adresse: $ip_address"
    echo "------------------------------------------------------------"
} > "$LOG_FILE"

# alle weiteren Ausgaben in das Logfile clonen
exec > >(tee -a "$LOG_FILE") 2>&1

# https://patorjk.com/software/taag/#p=testall&f=Twiggy&t=Font%C3%A4nensteuerung
echo -e "\e[0m"
echo '                                                                              '
echo ' $$$$$$$$\                   $$\       $\ $\                                  '
echo ' $$  _____|                  $$ |      \_|\_|                                 '
echo ' $$ |    $$$$$$\  $$$$$$$\ $$$$$$\    $$$$$$\  $$$$$$$\   $$$$$$\  $$$$$$$\   '
echo ' $$$$$\ $$  __$$\ $$  __$$\\_$$  _|   \____$$\ $$  __$$\ $$  __$$\ $$  __$$\  '
echo ' $$  __|$$ /  $$ |$$ |  $$ | $$ |     $$$$$$$ |$$ |  $$ |$$$$$$$$ |$$ |  $$ | '
echo ' $$ |   $$ |  $$ |$$ |  $$ | $$ |$$\ $$  __$$ |$$ |  $$ |$$   ____|$$ |  $$ | '
echo ' $$ |   \$$$$$$  |$$ |  $$ | \$$$$  |\$$$$$$$ |$$ |  $$ |\$$$$$$$\ $$ |  $$ | '
echo ' \__|    \______/ \__|  \__|  \____/  \_______|\__|  \__| \_______|\__|  \__| '
echo '                                                                              '
echo -e "\e[0m"

# ------------------------------------------------------------------
# parameter Verarbeitung
# ------------------------------------------------------------------

# Überprüfen, ob das Skript mit dem Parameter "apply" aufgerufen wird
# Nur dann werden die Installations Kommandos tatsächlich ausgeführt

SIMULATE=true

# Überprüfen, wie das Skript gestartet wurde
# Das Skript kann auf dem Raspberry direkt aufgerufen worden sein (FontaenenSteuerung Repository wurde vorher schon geklont) oder
# das Skript wird über "bash -c ... curl ..." aufgerufen, also ohne vorheriges Klonen.
# entprechend muss der Parameter apply anders erkannt werden
#
# Aufrunf Raspberry:	/home/pi/FontaenenSteuerung/install_Fontaenensteuerung.sh
# Aufruf remote: 		bash -c  "$(curl -sL https://raw.githubusercontent.com/spitzlbergerj/FontaenenSteuerung/development/install_Fontaenensteuerung.sh) apply"

p0=$0
# start ohne "bash -c" und es gibt einen Parameter
if [ $0 != 'bash' -a "$1." != "." ]; then
	# wird lokal ausgeführt
	# $1 enthält den Parameter
	p0=$1
fi

# Den Parameter in Kleinbuchstaben umwandeln
p0=$(echo $p0 | awk '{print tolower($0)}')

# Entsprechend dem Parameter handeln
if [ "$p0" == "apply" ]; then
	SIMULATE=false
fi

# ------------------------------------------------------------------
# Variable definieren
# ------------------------------------------------------------------

BOOT_CONFIG_FILE_OLD="/boot/config.txt"
BOOT_CONFIG_FILE_NEW="/boot/firmware/config.txt"
BOOT_CONFIG_FILE="$BOOT_CONFIG_FILE_NEW"

STD_HOSTNAME="Fontaenensteuerung"

WIFI_CONFIG_FILE="/etc/wpa_supplicant/wpa_supplicant.conf"
WIFI_BASIC_CONFIG="ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=DE"

FONTAENENSTEUERUNG_DIR="$HOME/FontaenenSteuerung"
FONTAENENSTEUERUNG_LOCAL_BACKUP="$HOME/FontaenenSteuerunglocalBackup"
FONTAENENSTEUERUNG_MARIADB_CREATE_TABLES="$FONTAENENSTEUERUNG_DIR/installation/FontaenenSteuerungValues.sql"

RASPBERRY_PI_BACKUP_CLOUD_DIR="$HOME/Raspberry-Pi-Backup-Cloud"

# ANSI Farbcodes
no_color='\033[0m' # Keine Farbe
nc="$no_color"

red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'

read_colored() {
	local color_code="$1"
	local prompt="$2"
	local var_name="$3"
	
	# Wähle die Farbe basierend auf dem Parameter
	case "$color_code" in
		red) color=$red ;;
		green) color=$green ;;
		yellow) color=$yellow ;;
		blue) color=$blue ;;
		magenta) color=$magenta ;;
		cyan) color=$cyan ;;
		*) color=$no_color ;; # Standardfarbe, falls keine Übereinstimmung gefunden wurde
	esac

	# Zeige den farbigen Prompt an und lese die Eingabe
	echo -en "${color}${prompt}${no_color}"
	read -r "$var_name"
}

echo_colored() {
	local color_code="$1"
	local output="$2"
	
	# Wähle die Farbe basierend auf dem Parameter
	case "$color_code" in
		red) color=$red ;;
		green) color=$green ;;
		yellow) color=$yellow ;;
		blue) color=$blue ;;
		magenta) color=$magenta ;;
		cyan) color=$cyan ;;
		*) color=$no_color ;; # Standardfarbe, falls keine Übereinstimmung gefunden wurde
	esac

	# Zeige den farbigen Prompt an und lese die Eingabe
	echo -e "${color}${output}${no_color}"
}


note() {
	# Paramter $1 enthält die Beschreibung des nächsten Schrittes
	local description=$1

	# Paramter $2 enthält den Switch für rote Schrift
	local color=$2

	# Prüfen, ob die Ausgabe in Rot erfolgen soll
	if [ "$color" == "red" ]; then
		echo -e "${red}"
	elif [ "$color" == "green" ]; then
		echo -e "${green}"
	elif [ "$color" == "yellow" ]; then
		echo -e "${yellow}"
	elif [ "$color" == "blue" ]; then
		echo -e "${blue}"
	elif [ "$color" == "magenta" ]; then
		echo -e "${magenta}"
	elif [ "$color" == "cyan" ]; then
		echo -e "${cyan}"
	else
		echo -e "${nc}"
	fi

	# Ausgabe einer Trennlinie mit Sternen zur visuellen Trennung
	echo ""
	echo "********************************************************************************"
	echo "   $description"
	echo "********************************************************************************"

	# Farbe zurücksetzen
	echo -e "${nc}"
}


# Funktion, um Kommandos basierend auf der SIMULATE-Variable auszuführen oder anzuzeigen
run_cmd() {
	if [ "$SIMULATE" = true ]; then
		echo -e "${red}Simuliere:${nc} $@"
	else
		echo -e "${red}Führe aus:${nc} $@"
		eval "$@"
	fi
}

# Funktion zur Überprüfung der Installation
check_installed() {
	dpkg -s $1 &> /dev/null

	if [ $? -eq 0 ]; then
		return 0 # Installiert
	else
		return 1 # Nicht installiert
	fi
}

# Backup-Funktion, die das Skript localBackup.sh aufruft
backup_fontaenensteuerung() {
	echo "Starte Backup für Fontänenesteuerung..."
	# Pfad zum Backup-Skript (angepasst an Ihre Struktur)
	local backup_script="$FONTAENENSTEUERUNG_DIR/localBackup.sh"
	if [ -f "$backup_script" ]; then
		run_cmd "bash \"$backup_script\""
	else
		echo "Backup-Skript nicht gefunden: $backup_script"
	fi
}


list_configured_ssids() {
	# Überprüfen, ob die Konfigurationsdatei existiert
	if [ ! -f "$WIFI_CONFIG_FILE" ]; then
		echo "keine Wifi SSIDs konfiguriert"
		return 1
	fi
	
	echo "aktuell konfigurierte SSIDs:"
	# Extrahieren und auflisten aller SSIDs
	sudo grep 'ssid=' "$WIFI_CONFIG_FILE" | sed -e 's/.*ssid="\([^"]*\)".*/\1/'
}

#m Funktion zum Updaten des Raspberry OS
update_raspberry_os() {
	echo "Aktualisiere Paketquellen..."
	run_cmd "sudo apt-get update -y"
	
	echo "Führe ein Upgrade aller installierten Pakete durch..."
	run_cmd "sudo apt-get upgrade -y"
	
	echo "Führe ein dist-upgrade durch, um sicherzustellen, dass auch Kernel und Firmware aktualisiert werden..."
	run_cmd "sudo apt-get dist-upgrade -y"
	
	echo "Bereinige nicht mehr benötigte Pakete..."
	run_cmd "sudo apt-get autoremove -y"
	
}

# Funktion zum Konfigurieren des Raspberry OS
config_raspberry_os() {
	echo -e "${red}Achtung: Das setzen der Sprache wird erst nach eine Reboot fehlerfrei sein.${nc}"
	echo "Ignorieren Sie daher eventuell auftretende Fehler zur Spracheinstellung."
	echo "Führen Sie jedoch nach diesem Kapitel einen reboot durch"
	echo
	echo "Land, Sprache und Zeitzone einstellen"
	run_cmd "sudo raspi-config nonint do_change_locale de_DE.UTF-8"
	run_cmd "sudo raspi-config nonint do_change_timezone Europe/Berlin"

	echo "Booten zum Desktop einstellen"	
	run_cmd "sudo raspi-config nonint do_boot_behaviour B4"
	
	echo "Hostnamen setzen"
	read_colored "cyan" "Geben Sie den neuen Hostnamen ein (Default: $STD_HOSTNAME): " answer
	if [[ -z $answer ]]; then
		answer=$STD_HOSTNAME
	fi
	run_cmd "sudo raspi-config nonint do_hostname $answer"
	
	echo "SSH aktivieren"
	run_cmd "sudo raspi-config nonint do_ssh 0"

	# Reboot anfordern
	# es ist noch zu prüfen, ob das immer gemacht werden muss
	#
	sudo touch /var/run/reboot-required
}

# Funktion zum Konfigurieren des WLAN
config_wifi() {
	# Überprüfen, ob die Konfigurationsdatei existiert
	if [ ! -f "$WIFI_CONFIG_FILE" ]; then
		echo "Konfigurationsdatei nicht gefunden. Erstelle eine neue mit Grundkonfiguration."
		run_cmd "echo \"$WIFI_BASIC_CONFIG\" | sudo tee \"$WIFI_CONFIG_FILE\" > /dev/null"
	fi

	while true; do
		echo
		list_configured_ssids
		echo

		read_colored "cyan" "Möchten Sie die Wifi-Konfiguration ergänzen? (j/N): " answer
		if ! [[ "$answer" =~ ^[Jj]$ ]]; then
			break
   		fi

		# Eingabe der WIFI Daten
		echo
		echo "Geben Sie die notwendigen Daten ein"
		read_colored "cyan" "SSID: " ssid
		read_colored "cyan" "Passwort: " password
		echo

		# Überprüfen, ob SSID bereits konfiguriert ist
		if sudo grep -q "ssid=\"$ssid\"" "$WIFI_CONFIG_FILE"; then
			echo "Eine Konfiguration für SSID $ssid existiert bereits. Nichts zu tun!"
		else
			# Wenn die SSID noch nicht konfiguriert ist, hinzufügen
			run_cmd "wpa_passphrase \"$ssid\" \"$password\" | sudo tee -a \"$WIFI_CONFIG_FILE\" > /dev/null"
			echo "Neue Konfiguration für $ssid hinzugefügt."
			
			# WLAN-Dienst neu starten, um die neue Konfiguration zu übernehmen
			run_cmd "sudo systemctl restart wpa_supplicant"
			
			echo "WLAN-Konfiguration aktualisiert."
		fi
	done
}


# Funktion zum Kponfigurieren des Raspberry OS
config_protocolls() {
	echo "I2C aktivieren"
	run_cmd "sudo raspi-config nonint do_i2c 0"
	echo "erkannte Devices am I2C:"
	run_cmd "i2cdetect -y 1"
}

# Funktion zum Klonen/Aktualisieren des FontaenenSteuerung Repositories
install_update_fontaenensteuerung() {
	if [ -d "$FONTAENENSTEUERUNG_DIR" ]; then
		cd "$FONTAENENSTEUERUNG_DIR"
		# Ermittle den aktuellen Branch
		local current_branch=$(git rev-parse --abbrev-ref HEAD)

		echo
		echo "FontaenenSteuerung Repository ist bereits auf diesem Gerät vorhanden."
		echo "Lokal wird der Branch - $current_branch - benutzt. Dieser wird mit dem entsprechenden Branch auf github verglichen"
		echo
		read_colored "cyan" "Möchten Sie das Repository aktualisieren? (j/N): " answer
		if [[ "$answer" =~ ^[Jj]$ ]]; then
			cd "$FONTAENENSTEUERUNG_DIR"
			echo "Prüfe Änderungen..."
			git fetch

			local target_branch="master"
			if [[ "$current_branch" == "development" ]]; then
				target_branch="development"
			fi

			local changes=$(git diff HEAD..origin/$target_branch)

			if [ -n "$changes" ]; then
				"Änderungen verfügbar auf $target_branch Branch:"
				git diff --stat HEAD..origin/$target_branch
				echo
				read_colored "cyan" "Möchten Sie diese Änderungen anwenden? (j/n): " apply_changes
				if [[ "$apply_changes" =~ ^[Jj]$ ]]; then
					echo "Backup der bisherigen Konfigurationen wird ausgeführt"
					backup_fontaenensteuerung
					echo "Aktualisiere FontaenenSteuerung Repository von $target_branch..."
					run_cmd "git merge origin/$target_branch"
				else
					echo "Aktualisierung abgebrochen."
				fi
			else
				echo "Keine Änderungen verfügbar. Repository ist aktuell."
			fi
		else
			echo "Aktualisierung nicht gewünscht."
		fi
	else
		echo "FontaenenSteuerung Repository wird heruntergeladen..."
		# Klonen des Repositories in den spezifizierten Branch
		run_cmd "git clone https://github.com/spitzlbergerj/FontaenenSteuerung.git \"$FONTAENENSTEUERUNG_DIR\""
		run_cmd "cd \"$FONTAENENSTEUERUNG_DIR\""
  		run_cmd "git fetch origin development:development"

		# Ermittle die verfügbaren Branches vom Remote-Repository
		echo "Verfügbare Branches:"
		run_cmd "git branch"

		# nachfolgendes nur falls nicht nur simuliert (zu komplex für run_cmd)
		if [ "$SIMULATE" = false ]; then
			while true; do
				# Frage nach dem gewünschten Branch
				echo "Im Regelfall nutzen Sie bitte den master Branch!"
				read_colored "cyan" "Welchen Branch möchten Sie nutzen? (default: master) " target_branch

				if [[ -z $target_branch ]]; then
					target_branch="master"
				fi

				# Überprüfen, ob der eingegebene Branch existiert
				if git rev-parse --verify "$target_branch" > /dev/null 2>&1; then
					echo "Wechsle zu Branch '$target_branch'..."
					git checkout "$target_branch"
					break
				else
					echo "Der Branch '$target_branch' existiert nicht. Überprüfen Sie die Eingabe und versuchen Sie es erneut."
					echo
				fi
			done
		fi
	fi

	# git hooks aktivieren
	echo "git hooks anlegen"
	cd "$FONTAENENSTEUERUNG_DIR"
	run_cmd "cp .git_hooks/*commit .git/hooks"
	run_cmd "chmod +x .git/hooks/*commit"
	run_cmd "mkdir ~/FontaenenSteuerung/.git_sensible_backup"

}

install_apache() {
	echo "Apache installieren ...."
	run_cmd "sudo apt-get install apache2 -y"

	echo "Starte Apache2 und aktiviere den Autostart..."
	run_cmd "sudo systemctl start apache2"
	run_cmd "sudo systemctl enable apache2"

	# Überprüfe den Status des Apache2-Service
	echo "Überprüfe den Status des Apache2-Dienstes..."
	run_cmd "sudo systemctl status apache2"

	echo "Apache2 wurde erfolgreich installiert und läuft."
}

install_mosquitto() {
	echo "Mosquitto installieren ...."
	run_cmd "sudo apt install mosquitto mosquitto-clients"

	echo "Starte Mosquitto und aktiviere den Autostart..."
	run_cmd "sudo systemctl start mosquitto"
	run_cmd "sudo systemctl enable mosquitto"

	# Überprüfe den Status des Apache2-Service
	echo "Überprüfe den Status des Mosquitto-Dienstes..."
	run_cmd "sudo systemctl status mosquitto"

	echo "Mosquitto wurde erfolgreich installiert und läuft."
}

install_mqtt_logging() {
	echo "MQTT Logging installieren ...."
	cd "$FONTAENENSTEUERUNG_DIR"
	run_cmd "sudo cp .systemd-files/mqtt-logging.service /etc/systemd/system/"
	run_cmd "sudo systemctl daemon-reload"

	echo "Starte Mosquitto und aktiviere den Autostart..."
	run_cmd "sudo systemctl start mqtt-logging.service"
	run_cmd "sudo systemctl enable mqtt-logging.service"

	# Überprüfe den Status des Apache2-Service
	echo "Überprüfe den Status des MQTT-Logging-Dienstes..."
	run_cmd "sudo systemctl status mqtt-logging.service"

	echo "MQTT Logging wurde erfolgreich installiert und läuft."
}

# Installation Geräte Librarys
install_libraries() {
	echo "Libraries installieren ...."
	cd "$FONTAENENSTEUERUNG_DIR/.lib"

	run_cmd "sudo apt-get install i2c-tools"

	run_cmd "pip3 install adafruit-circuitpython-motorkit --break-system-packages"
	run_cmd "pip3 install adafruit-circuitpython-mcp230xx --break-system-packages"

	# run_cmd "pip3 install adafruit-circuitpython-lis3dh --break-system-packages"
	# run_cmd "pip3 install adafruit-circuitpython-busdevice --break-system-packages"
	# run_cmd "pip3 install adafruit-circuitpython-adxl34x --break-system-packages"

}


# Installation Python Module
install_python_modules() {
	echo "Python Module für MariaDB, MQTT und Flask installieren ...."

	echo " ... mmqtt connector"
	run_cmd "sudo apt install python3-paho-mqtt"
	echo " ... Flask Framework"
	run_cmd "sudo apt install python3-flask"

	# Apache für Flask konfigurieren
	# Apache wird der Proxy, jedoch muss /phpmyadmin weiterhin erreichbar bleiben
	echo " ... Apache für Flask vorbereiten"
	run_cmd "sudo a2enmod proxy"
	run_cmd "sudo a2enmod proxy_http"

	# Füge ProxyPass zu 000-default.conf hinzu, um auf Flask-App zu verweisen
	# und sicherzustellen, dass phpMyAdmin weiterhin funktioniert
	run_cmd "echo \"<VirtualHost *:80>\" | sudo tee /etc/apache2/sites-available/000-default.conf"
	run_cmd "echo \"    ServerAdmin webmaster@localhost\" | sudo tee -a /etc/apache2/sites-available/000-default.conf"
	run_cmd "echo \"    DocumentRoot /var/www/html\" | sudo tee -a /etc/apache2/sites-available/000-default.conf"
	run_cmd "echo \"    ProxyPass /phpmyadmin !\" | sudo tee -a /etc/apache2/sites-available/000-default.conf"
	run_cmd "echo \"    ProxyPass / http://127.0.0.1:5000/\" | sudo tee -a /etc/apache2/sites-available/000-default.conf"
	run_cmd "echo \"    ProxyPassReverse / http://127.0.0.1:5000/\" | sudo tee -a /etc/apache2/sites-available/000-default.conf"
	run_cmd "echo \"</VirtualHost>\" | sudo tee -a /etc/apache2/sites-available/000-default.conf"

	echo "Flask als Systemdienst einrichten"
	run_cmd "sudo cp $FONTAENENSTEUERUNG_DIR/.systemd-files/flask.service /etc/systemd/system/"
	run_cmd "sudo systemctl daemon-reload"
	run_cmd "sudo systemctl enable flask.service"
	run_cmd "sudo systemctl start flask.service"

	echo "Apache neu starten"
	run_cmd "sudo service apache2 restart"

}

# Installation Backup Routinr
install_backup() {
	echo "Backup Routine installieren ...."

	if [ -d "$RASPBERRY_PI_BACKUP_CLOUD_DIR" ]; then
		# Routine beretis installiert
		cd "$RASPBERRY_PI_BACKUP_CLOUD_DIR"
		# Ermittle den aktuellen Branch
		local current_branch=$(git rev-parse --abbrev-ref HEAD)

		echo
		echo "Raspberry-Pi-Backup-Cloud Repository ist bereits auf diesem Gerät vorhanden."
		echo "Lokal wird der Branch - $current_branch - benutzt. Dieser wird mit dem entsprechenden Branch auf github verglichen"
		echo
		read_colored "cyan" "Möchten Sie das Repository aktualisieren? (j/N): " answer
		if [[ "$answer" =~ ^[Jj]$ ]]; then
			cd "$RASPBERRY_PI_BACKUP_CLOUD_DIR"
			echo "Prüfe Änderungen..."
			git fetch

			local target_branch="master"
			if [[ "$current_branch" == "development" ]]; then
				target_branch="development"
			fi

			local changes=$(git diff HEAD..origin/$target_branch)

			if [ -n "$changes" ]; then
				"Änderungen verfügbar auf $target_branch Branch:"
				git diff --stat HEAD..origin/$target_branch
				echo
				read_colored "cyan" "Möchten Sie diese Änderungen anwenden? (j/n): " apply_changes
				if [[ "$apply_changes" =~ ^[Jj]$ ]]; then
					echo "Aktualisiere Raspberry-Pi-Backup-Cloud Repository von $target_branch..."
					run_cmd "git merge origin/$target_branch"
				else
					echo "Aktualisierung abgebrochen."
				fi
			else
				echo "Keine Änderungen verfügbar. Repository ist aktuell."
			fi
		else
			echo "Aktualisierung nicht gewünscht."
		fi
	else
		echo "Raspberry-Pi-Backup-Cloud Repository wird heruntergeladen..."
		# Klonen des Repositories in den spezifizierten Branch
		run_cmd "git clone https://github.com/spitzlbergerj/Raspberry-Pi-Backup-Cloud.git \"$RASPBERRY_PI_BACKUP_CLOUD_DIR\""
		run_cmd "cd \"$RASPBERRY_PI_BACKUP_CLOUD_DIR\""

		# Ermittle die verfügbaren Branches vom Remote-Repository
		# echo "Verfügbare Branches:"
		# run_cmd "git branch"

		# nachfolgendes nur falls nicht nur simuliert (zu komplex für run_cmd)
		# if [ "$SIMULATE" = false ]; then
		# 	while true; do
		# 		# Frage nach dem gewünschten Branch
		# 		echo "Im Regelfall nutzen Sie bitte den main Branch!"
		#		read_colored "cyan" "Welchen Branch möchten Sie nutzen? (default: main)" target_branch

		#		if [[ -z $target_branch ]]; then
		#			target_branch="main"
		#		fi

		#		# Überprüfen, ob der eingegebene Branch existiert
		#		if git rev-parse --verify "$target_branch" > /dev/null 2>&1; then
		#			echo "Wechsle zu Branch '$target_branch'..."
		#			git checkout "$target_branch"
		#			break
		#		else
		#			echo "Der Branch '$target_branch' existiert nicht. Überprüfen Sie die Eingabe und versuchen Sie es erneut."
		#			echo
		#		fi
		#	done
		# fi
	fi

	run_cmd "ln -s $RASPBERRY_PI_BACKUP_CLOUD_DIR/backup /home/pi/backup"
	run_cmd "cp $FONTAENENSTEUERUNG_DIR/.backup-config/backup2ndScript.sh /home/pi/backup/.config/backup2ndScript.sh"
	run_cmd "cp $FONTAENENSTEUERUNG_DIR/.backup-config/backup_dirs.txt /home/pi/backup/.config/backup_dirs.txt"
	run_cmd "cp $FONTAENENSTEUERUNG_DIR/.backup-config/backup_name.txt /home/pi/backup/.config/backup_name.txt"
	run_cmd "cp $RASPBERRY_PI_BACKUP_CLOUD_DIR/backup/.config/rclone.conf-muster /home/pi/backup/.config/rclone.conf"

	run_cmd "chmod +x /home/pi/backup/backup.sh /home/pi/backup/.config/backup2ndScript.sh"

	# Installation von rclone
	echo "Installation von rclone"
	if [ "$SIMULATE" = false ]; then
		curl https://rclone.org/install.sh | sudo bash
	fi

	echo
	echo_colored "magenta" "rclone muss noch zwingend konfiguriert werden."
	echo_colored "magenta" "Eine Beschreibung hierzu finden Sie unter https://github.com/spitzlbergerj/Raspberry-Pi-Backup-Cloud"
	echo
	echo

}

# Installation StromPi3

install_stromPi3() {
	echo "Python Modul für StromPi3 installieren ...."
	run_cmd "sudo apt-get install python3-serial"

	echo "Boot Config um Serielle Kommunikation erweitern ...."

	# Zu appendende Zeilen
	LINES_TO_APPEND=(
	"dtoverlay=miniuart-bt"
	"enable_uart=1"
	"core_freq=250"
	)

	# Überprüfe, ob die Datei existiert
	if [ -f "$BOOT_CONFIG_FILE" ]; then
		for line in "${LINES_TO_APPEND[@]}"; do
			# Überprüfe, ob die Zeile bereits existiert
			if ! grep -qF -- "$line" "$BOOT_CONFIG_FILE"; then
				# Füge die Zeile hinzu, wenn sie nicht existiert
				run_cmd "echo \"$line\" | sudo tee -a \"$BOOT_CONFIG_FILE\" > /dev/null"
			fi
		done
		echo "Konfiguration wurde erfolgreich aktualisiert."
	fi

	echo "Serielle Konfigurationen in raspi-config"
	if [ "$SIMULATE" = false ]; then
		sudo sed -i 's/console=serial0,115200 //g' /boot/cmdline.txt
		sudo bash -c "echo 'enable_uart=1' >> /boot/config.txt"
		sudo bash -c "echo 'dtoverlay=miniuart-bt' >> /boot/config.txt"
		sudo apt-get install minicom
		# sudo minicom -D /dev/serial0 -b 38400
	fi

}

next_steps() {

	note "Abschluss und nächste Schritte" "cyan"

	echo
	echo
	echo_colored "magenta" "Sie haben es nun beinahe geschafft! Nun folgen noch manuelle Schritte"
	echo
	echo "- reboot durchführen"
	echo "     Sie sollten nach Abschluss der Installation einen reboot durchführen"
	echo "     Sie können sich diesen Text noch einmal ausgeben lassen, "
	echo "     wenn Sie dieses Installations-Skript noch einmal nur mit dem Paramter 'next' starten"
	echo
	echo "- rclone konfigurieren"
	echo "     Damit die Datensicherung klappt, müssen Sie noch rclone entsprechend konfigurieren"
	echo "     Eine gute Beschreibung hierfür finden Sie unter https://github.com/spitzlbergerj/Raspberry-Pi-Backup-Cloud"
	echo
	echo "- FontaenenSteuerung Konfiguration durchführen"
	echo "     Vieles am FontaenenSteuerung wird über eine Konfigruationsdatei gesteuert. Diese json Datei können Sie komfortabel"
	echo "     über die Fontänensteuerung Website befüllen. Gehen Sie dazu auf http://$ip_address/configs und führen Sie"
	echo "     nacheinander alle Konfigurationsschritte durch"
	echo
	echo "- Crontabs kontrollieren und anpassen"
	echo "     Dieses Skript hat für die Crontabs meine Muster Crontabs eingesetzt. Spätestens nach dem Booten werden"
	echo "     die FontaenenSteuerung Programme beginnen, die Sensoren abzufragen und in Datei, Datenbank zu schreiben"
	echo "     und an den MQTT Broker zu senden."
	echo "     Ändern Sie die Crontab nach Ihren Bedürfnissen. Nehmen Sie z.B. Programme außer Betrieb, falls noch"
	echo "     entsprechenden Sensoren verbaut wurden."
	echo
	echo
	echo
}




# ########################################################################################
# ########################################################################################
# ##                                                                                    ##
# ##                                     Skriptanfang                                   ##
# ##                                                                                    ##
# ########################################################################################
# ########################################################################################

# Wenn der Parameter next lautet, dann nur noch den Abschluss Text ausgeben
if [ "$p0" == "next" ]; then
	next_steps
	exit
fi

if [ "$SIMULATE" = true ]; then
	note "Kommandos werden NICHT ausgeführt, lediglich Simulation" "green"
else
	note "ACHTUNG - Kommandos werden ausgeführt !!! " "red"
fi

cd "$HOME"

echo "Die Installation von FontaenenSteuerung erfolgt in mehreren Schritten. Für das Funktionieren der FontaenenSteuerung sind alle Schritte vonnöten."
echo "Überspringen Sie Schritte nur, wenn Sie wissen was Sie tun bzw. wenn Sie nach einem erforderlichen Reboot alle Schritte "
echo "überspringen, die Sie schon ausgeführt haben."
echo
echo "Die Reihenfolge der einzelnen Schritte ist ebenfalls wichtig und einzuhalten."
echo
echo "Die einzelnen Kommados geben sehr viele Daten aus. Um die Übersicht zu erhöhen folge ich diesen Farb-Codex:"
echo_colored "cyan" "CYAN für Kapitelüberschriften und Abfragen an Sie"
echo_colored "magenta" "MAGENTA für wichtige Informationen"
echo_colored "red" "ROT für die Kommandos, die dieses Skript ausführt"
echo
echo

# --------------------------------------------------------------------------
# Raspberry OS updaten
# --------------------------------------------------------------------------
note "Update Raspberry OS" "cyan"

read_colored "cyan" "Möchten Sie Raspberry OS zunächst updaten? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	update_raspberry_os

	echo "Überprüfe, ob ein Neustart erforderlich ist..."
	if [ -f /var/run/reboot-required ]; then
		echo
		echo
		echo "Ein Neustart ist erforderlich, um die Aktualisierungen zu vervollständigen."
		echo "Bitte führen Sie 'sudo reboot' aus."
		echo "Anschließend starten Sie das Installationsskript erneut und überspringen die Sektionen bis Konfiguration Raspberry OS."
		echo
		echo
		exit
	else
		echo "Kein Neustart erforderlich."
	fi
fi

cd "$HOME"

# --------------------------------------------------------------------------
# Raspberry OS konfigurieren
# --------------------------------------------------------------------------
note "Konfiguration Raspberry OS" "cyan"

echo "Die nachfolgenden Konfigurationen werden in der Regel vom Raspberry Pi Imager bereits vorgenommen."
echo
read_colored "cyan" "Möchten Sie Raspberry OS konfigurieren (Sprache, Zeitzone, Hostname, SSH, ...)? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	config_raspberry_os

	echo "Überprüfe, ob ein Neustart erforderlich ist..."
	if [ -f /var/run/reboot-required ]; then
		echo
		echo
		echo "Ein Neustart ist erforderlich, um die Aktualisierungen zu vervollständigen."
		echo "Bitte führen Sie 'sudo reboot' aus."
		echo "Anschließend starten Sie das Installationsskript erneut und überspringen die Sektionen bis Wifi."
		echo
		echo
		exit
	else
		echo "Kein Neustart erforderlich."
	fi
fi

cd "$HOME"

# --------------------------------------------------------------------------
# WLAN konfigurieren (mehrere WLANs über eine Schleife)
# --------------------------------------------------------------------------
note "Konfiguration Wifi - mehrere Eingaben möglich" "cyan"

config_wifi

cd "$HOME"

# --------------------------------------------------------------------------
# Raspberry OS erweitern
# --------------------------------------------------------------------------
note "Konfiguration benötigter Kommunikationsprotokolle" "cyan"

read_colored "cyan" "Möchten Sie die benötigten Kommunikationsprotokolle aktivieren (i2c, ...)? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	config_protocolls
fi
cd "$HOME"

# --------------------------------------------------------------------------
# FontaenenSteuerung Repository installieren
# --------------------------------------------------------------------------
note "Installation FontaenenSteuerung Repository" "cyan"

read_colored "cyan" "Möchten Sie das FontaenenSteuerung Repository von GitHub klonen? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_update_fontaenensteuerung
fi

cd "$HOME"

# --------------------------------------------------------------------------
# Mosquitto installieren
# --------------------------------------------------------------------------
note "Installation Mosquitto"  "cyan"

read_colored "cyan" "Möchten Sie den Mosquitto installieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_mosquitto

	echo
	echo_colored "magenta" "Sie haben nun einen lokalen MQTT Broker."
	echo

fi

cd "$HOME"

# --------------------------------------------------------------------------
# MQTT Logging installieren
# --------------------------------------------------------------------------
note "Installation MQTT Logging"  "cyan"

read_colored "cyan" "Möchten Sie den MQTT Logging installieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_mqtt_logging

	echo
	echo_colored "magenta" "Alle MQTT Messages werden nun protokolliert."
	echo

fi

cd "$HOME"

# --------------------------------------------------------------------------
# Apache Webserver installieren
# --------------------------------------------------------------------------
note "Installation Apache Webserver"  "cyan"

read_colored "cyan" "Möchten Sie den Apache Webserver installieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_apache

	echo
	echo_colored "magenta" "Sie sollten nun auf die Website Ihres FontaenenSteuerung zugreifen können."
	echo "Rufen Sie dazu die Website http://$ip_address/ auf."
	echo

fi

cd "$HOME"

# --------------------------------------------------------------------------
# diverse Libraries installieren
# --------------------------------------------------------------------------
note "Installation diverser Libraries" "cyan"

read_colored "cyan" "Möchten Sie die notwendigen Libraries installieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_libraries
fi

cd "$HOME"

# --------------------------------------------------------------------------
# Python Module installieren
# --------------------------------------------------------------------------
note "Installation Python Module für MariaDB, MQTT und Flask" "cyan"

read_colored "cyan" "Möchten Sie die Python Module installieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_python_modules
	
	echo
	echo_colored "magenta" "Sie sollten nun auf die FontaenenSteuerung Bedienungs-Website zugreifen können."
	echo "Rufen Sie dazu jetzt erneut die Website http://$ip_address auf."
	echo
	echo_colored "magenta" "Sie können dort bereits jetzt den bisherigen Installationsstatus einsehen."
	echo "Klicken Sie dazu auf den Button 'Status'"
	echo "Achtung: Sie werden dabei vermutlich einen Fehler bei der MariaDB bekommen."
	echo "Dies liegt daran, dass Sie in der FontaenenSteuerung Konfiguration die User Daten noch nicht gesetzt haben."
	echo "Rufen Sie hierzu folgende Seite auf: http://$ip_address/config_caravanpi"

fi

cd "$HOME"

# --------------------------------------------------------------------------
# Backup Routine clonen und einrichten
# --------------------------------------------------------------------------
note "Backup Routine installieren" "cyan"

read_colored "cyan" "Möchten Sie die Backup Routine installieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_backup
fi

cd "$HOME"


# --------------------------------------------------------------------------
# logrotate einrichten
# --------------------------------------------------------------------------
note "Logrotate konfigurieren" "cyan"

read_colored "cyan" "Möchten Sie logrotate für FontaenenSteuerung aktivieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	run_cmd "echo -e \"\n# FontaenenSteuerung\ninclude /home/pi/FontaenenSteuerung/logrotate/logrotate-FontaenenSteuerung.conf\" | sudo tee -a /etc/logrotate.conf > /dev/null"
	run_cmd "sudo find \"$FONTAENENSTEUERUNG_DIR\" -type f -name \"*logrotate*.conf\" -exec chown root:root {} \;"
fi

cd "$HOME"

# --------------------------------------------------------------------------
# Crontabs
# --------------------------------------------------------------------------
note "Crontabs einrichten" "cyan"

read_colored "cyan" "Möchten Sie die Crontabs von pi und root aktivieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	run_cmd "crontab $FONTAENENSTEUERUNG_DIR/.crontabs/crontab-pi"
	run_cmd "sudo crontab $FONTAENENSTEUERUNG_DIR/.crontabs/crontab-root"
fi

cd "$HOME"

# --------------------------------------------------------------------------
# StromPi3 installieren
# --------------------------------------------------------------------------
note "StromPi3 installieren" "cyan"

read_colored "cyan" "Möchten Sie die Software für den StromPi3 installieren? (j/N): " answer
if [[ "$answer" =~ ^[Jj]$ ]]; then
	install_stromPi3
fi

cd "$HOME"

# --------------------------------------------------------------------------
# nächste Schritte
# --------------------------------------------------------------------------

next_steps