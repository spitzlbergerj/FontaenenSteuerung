# FontaenenSteuerung
Steuerung der Fontänen einer Schlossanlage über MQTT Messages. Die Steuerung der Fontänenanlage erfolgt über eine alte Schlüsselsteuerung. Diese Steuerung dreht die Schlüssel mithilfe von Motoren

## Motorsteuerung

### Endlagenschalter
An den beiden Endpositionen (Automatik und Handbetrieb) sorgen Endlagenschalter dafür, dass sich der Motor durch Mikroschalter, die den Stromkreis unterbrechen, nicht mehr weiter in diese Richtung bewegen kann. Über entsprechend geschaltete Dioden Parallel zu den Kontakten NO und NC des Mikroschalters sorgen dafür, dass sich der Motor in die andere Richtung gewegen kann.

Das Prinzip wird hier erklärt https://sgs-electronic.de/tipps-und-tricks/fo-modul/anschluss-von-endlagenschaltern

### Mittelschalter

Die Position Aus liegt mittig zwischen den beiden Endpositionen. Hier wird ein Mikroschalter bei der Motorbewegung permanent abgefragt, um an der Mittelposition, die durch Betätigen des Mittelschalters markiert wird, anhält. Dies ist rein softwaregesteuert.

### Getriebemotoren stoppen nicht sofort - Nachlauf
Dieses Problem muss über entsprechend Positionierung der Mikroschalter und geringe Motorgeschwindigkeiten gelöst werden.
