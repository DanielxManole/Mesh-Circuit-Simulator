# Motorul de simulare

Documentația motorului de calcul `calculate_sys` (`src/calculation/`).

## 1. Prezentare

Motorul determină **punctul static de funcționare (DC)** al unui circuit: tensiunile în noduri, curenții și tensiunile pe componente și puterea disipată. Se bazează pe **Analiza Nodală Modificată (MNA)**, metoda folosită și de simulatoarele de tip SPICE.

Analiza tranzitorie (variația în timp a mărimilor) nu este implementată. Interfețele de calcul acceptă deja parametrii `t` și `dt`, dar motorul le apelează cu valoarea `0`.

## 2. Contract

| | |
|---|---|
| **Intrare** | `ParsedCircuit`, produs de `data_parsing.parse_circuit(scene)` |
| **Ieșire** | `SimulationResult`: tensiuni nodale, mărimi per componentă, lista de erori și avertismente, timpul de rulare |
| **Erori** | Motorul nu aruncă excepții către interfață. Orice problemă devine un `SimError` cu locație, motiv și (opțional) sugestie |
| **Nivel** | `error` oprește simularea, `warning` o lasă să continue |

## 3. Etapele simulării

### 3.1. Parsare (`data_parsing.py`)

1. Se colectează componentele și firele din scenă.
2. Pinii conectați prin fire sunt grupați într-un **nod electric** folosind structura **Union-Find**.
3. Se alege nodul de referință (masa). Dacă există componente GND, toate sunt unificate în nodul 0. Dacă nu există, se alege automat nodul cu cele mai multe conexiuni și se emite un avertisment.
4. Se detectează erorile de topologie (de exemplu circuit gol, pini neconectați).
5. Fiecare componentă este transformată într-un **element** de calcul (`build_element`). Componentele compuse (Arduino, potențiometru, releu, senzori) pot genera mai multe elemente.

### 3.2. Construirea sistemului MNA

Pentru un circuit cu `n` noduri (fără masă) și `m` necunoscute de curent, sistemul este:

```
A · x = z
```

- `x` conține tensiunile nodale (`n - 1` valori, masa fiind 0) urmate de curenții necunoscuți (`m` valori);
- `A` și `z` se construiesc prin **stampile**: fiecare element își adaugă contribuția la matrice (`stamp(A, z, v_prev, t, dt)`);
- elementele care introduc o necunoscută de curent (`needs_current`) sunt sursele de tensiune și ampermetrul.

Dacă un nod rămâne fără nicio contribuție pe diagonală, se adaugă o conductanță foarte mică (`1 / R_OPEN`) pentru ca matricea să fie inversabilă.

Sistemul se rezolvă cu `numpy.linalg.solve`.

### 3.3. Circuite liniare și neliniare

- **Circuit liniar** (rezistoare, surse, condensatoare și bobine în DC, întrerupătoare etc.): o singură construire și o singură rezolvare.
- **Circuit cu elemente neliniare** (diodă, LED, tranzistoare): se aplică o **iterație cu damping**.
  1. Se pornește de la soluția zero.
  2. La fiecare pas, elementele neliniare își recalculează stampila în funcție de tensiunile pasului anterior (**modele companion**, liniare pe porțiuni).
  3. Se rezolvă sistemul liniar rezultat.
  4. Soluția nouă se amestecă cu cea veche: `x = DAMPING · x_nou + (1 - DAMPING) · x_vechi`.
  5. Iterația se oprește când variația maximă a tensiunilor nodale scade sub `TOL_V`.

| Constantă | Valoare | Rol |
|---|---|---|
| `MAX_ITER` | 80 | număr maxim de iterații |
| `TOL_V` | 1e-5 V | prag de convergență |
| `DAMPING` | 0,5 | cât din pasul nou se aplică |
| `R_MIN` | 1e-6 Ω | rezistență parazită minimă |
| `R_OPEN` | 1e9 Ω | rezistență "circuit deschis" |

Dacă iterația nu converge în `MAX_ITER` pași, se emite un avertisment cu sugestia de a verifica polarizarea diodelor sau de a adăuga un rezistor în serie.

### 3.4. Postprocesare

Din tensiunile nodale și curenții necunoscuți, fiecare element calculează mărimile de afișat (`postprocess`): tensiune, curent, putere. Se generează avertismente pentru depășirea limitelor (de exemplu curent prea mare printr-un LED).

## 4. Modele de componente (`models.py`)

| Componentă | Model în regim DC |
|---|---|
| Rezistor | conductanță `1/R` |
| Sursă de tensiune | MNA, cu curent necunoscut |
| Sursă de curent | contribuție în vectorul `z` |
| Condensator | circuit deschis (`R_OPEN`) |
| Bobină | scurtcircuit în DC (rezistență `R_MIN`) |
| Întrerupător, buton | `R_MIN` când e închis, `R_OPEN` când e deschis |
| Voltmetru | rezistență foarte mare |
| Ampermetru | sursă de 0 V, cu curent necunoscut |
| Fotorezistor | rezistență în funcție de nivelul de lumină setat (între `R_dark` și `R_light`) |
| Termistor | rezistență NTC calculată din temperatură cu modelul Beta |
| Diodă | **liniar pe porțiuni**: blocată sub `Vf` (1 GΩ), în conducție sursă `Vf` în serie cu `R_on ≈ 5 Ω`, cu mic histerezis |
| LED | model asemănător diodei, cu `Vf` în funcție de culoare și avertisment la depășirea `If_max` |
| BJT NPN / PNP | joncțiunea B-E ca diodă liniară pe porțiuni, plus sursă de curent controlată `Ic = β · Ib` și conductanță de ieșire pentru stabilitate |
| Senzor ultrasonic | sursă de tensiune proporțională cu distanța setată |
| Buzzer, motor DC | rezistență echivalentă (înfășurare) |
| Potențiometru, releu, servomotor, LM35, Arduino UNO | modele compuse din elementele de mai sus |

Modelele sunt **didactice și simplificate**. Diodele și tranzistoarele nu folosesc ecuația exponențială Shockley, ci modele liniare pe porțiuni, care converg robust în câțiva pași și nu produc depășiri numerice. Rezultatele sunt potrivite pentru înțelegerea circuitelor, nu pentru proiectare cu toleranțe fine.

## 5. Condiții limită

| Situație | Comportament |
|---|---|
| Rezistență de 0 Ω | se folosește `R_MIN` |
| Nod fără conexiuni suficiente | conductanță `1/R_OPEN` pe diagonală |
| Circuit fără masă | se alege automat un nod de referință, cu avertisment |
| Circuit cu un singur nod | eroare: se cere conectarea componentelor prin fire |
| Matrice singulară (`LinAlgError`) | eroare cu locația și motivul, fără blocarea aplicației |
| Eroare în stampila unui element | eroare asociată elementului respectiv (`uid`) |
| Nu converge | avertisment cu sugestie |

## 6. Extinderea cu o componentă nouă

1. Se adaugă intrarea în `components_catalog.py` (nume, descriere, pini, parametri, simbol).
2. Se adaugă simbolul grafic al componentei.
3. Se adaugă o clasă `Element` în `models.py` cu metodele `stamp` și `postprocess`, iar dacă este neliniară, `is_linear = False`.
4. Se leagă tipul componentei de modelul ei în `build_element`.

Motorul și interfața nu necesită alte modificări.

## 7. Limitări și direcții viitoare

- analiză tranzitorie (condensatoare și bobine cu pas de timp);
- modele semiconductoare mai fidele (ecuația Shockley, Ebers-Moll);
- praguri de resurse pentru circuite foarte mari.
