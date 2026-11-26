# Arhitectura sistemului

Document de proiectare arhitecturală pentru **Mesh - Simulator de circuite electrice**.
Realizat de Andrei Patrick-Cristian, Manole Daniel și Pralea Bogdan-Ștefan (631AB, Sg.2, FIIR - SIA).

## 1. Scopul sistemului

Mesh este o aplicație desktop care permite studenților, cadrelor didactice și specialiștilor să construiască vizual circuite electrice, să le simuleze și să înțeleagă rezultatele. Accentul cade pe latura didactică: aplicația nu doar calculează, ci explică (descrieri pentru fiecare componentă, erori cu locație și motiv, sugestii de rezolvare).

Sistemul rulează local pe Windows, fără conexiune la internet și fără servicii externe.

### Surse de referință

- standardele de simbolistică electrică **IEC 60617** și **ANSI Y32.2**, pentru simbolurile din biblioteca de componente;
- documentația și comportamentul unor simulatoare existente (LTspice, Multisim, Tinkercad Circuits), consultate pentru a identifica limitările lor în ceea ce privește asistența oferită utilizatorului;
- metodele de rezolvare a ecuațiilor nodale folosite în simulatoarele de tip SPICE.

## 2. Obiective de proiectare

- **Simplitate** ("less is more"): conexiunile și parametrii se stabilesc cu cât mai puține click-uri, fără meniuri ramificate sau ferestre pop-up obstructive.
- **Cerințe hardware reduse**: grafică 2D schematică, fără modele 3D; aplicația rulează pe laptopuri și PC-uri obișnuite cu Windows.
- **Modularitate**: separarea clară între interfață, parsare, calcul și persistență, astfel încât adăugarea unui nou tip de componentă să se facă într-un număr mic de locuri.
- **Robustețe**: motorul de calcul nu trebuie să blocheze aplicația la date invalide; orice problemă este raportată utilizatorului cu locația și motivul ei.

## 3. Subsisteme

| Subsistem | Responsabilități | Cod |
|---|---|---|
| **Modelare circuite** | Catalog de componente, adăugare prin drag-and-drop, conexiuni, parametrizare | `src/components/`, `src/components_logic/`, `src/ui/` |
| **Gestionare date** | Preluarea și validarea circuitului, transformarea lui într-un model utilizabil de simulare | `src/calculation/data_parsing.py` |
| **Simulare** | Procesarea modelului, aplicarea legilor lui Kirchhoff, generarea rezultatelor | `src/calculation/models.py`, `src/calculation/calculate_sys.py` |
| **Afișare rezultate** | Prezentarea numerică și grafică a rezultatelor, animația curentului | `src/ui/results_view.py` |
| **Export schemă** | Generarea schemei tehnice a circuitului | `src/export/schematic_from_sys.py` |
| **Persistență** | Salvare/încărcare proiecte, autosave, log | `src/persistence/` |

### Pachete

```
Interfață (UI)
 ├─ Model circuit (canvas)
 ├─ Catalog (paletă de componente)
 ├─ Parametrizare (panou de proprietăți)
 └─ Rezultate
        │
        ▼
Calculation
 ├─ DataParsing (data_parsing.py)
 └─ Simulation (models.py, calculate_sys.py)
```

Interfața depinde de pachetul `Calculation`, nu invers: motorul de calcul nu importă nimic din interfață și poate fi testat separat.

### Distribuție

Aplicația este un singur proces pe un singur calculator. Interfața grafică (modelul circuitului și rezultatele) comunică direct cu motorul de simulare, în același mediu de execuție Python, folosind PyQt6 și NumPy ca dependențe.

## 4. Managementul datelor persistente

Nu se folosește o bază de date. Aplicația este locală, iar un sistem SQL ar fi îngreunat instalarea și ar fi consumat resurse inutile. Datele sunt gestionate prin **sistemul de fișiere**, ceea ce permite utilizatorului să își mute proiectele dintr-un folder în altul ca fișiere individuale.

- **Proiectul** este un fișier **JSON** care conține lista componentelor folosite, poziția lor pe ecran, conexiunile și parametrii setați (de exemplu valoarea unei rezistențe în ohmi).
- **Autosave și log**: aplicația salvează periodic starea curentă (la 30 de secunde) și scrie fișiere de jurnal în `%APPDATA%\SimulatorCircuiteElectrice`, astfel încât munca să nu se piardă la o închidere neașteptată.
- **Catalogul de componente** (nume, descrieri, parametri, pini) este definit în cod, în `components_catalog.py`.

## 5. Controlul accesului

Aplicația este un instrument local și nu folosește conturi sau parole. Toți utilizatorii (student, cadru didactic, specialist) au acces la aceleași funcții. Interfața este gândită să fie intuitivă pentru începători și suficient de detaliată pentru utilizatorii avansați.

## 6. Fluxul global al controlului

1. La pornire, aplicația inițializează mediul de lucru și încarcă catalogul de componente.
2. Utilizatorul plasează componente, le conectează și le setează parametrii. Controlul aparține exclusiv utilizatorului.
3. La rularea simulării, controlul trece la motorul `calculate_sys`:
   - `parse_circuit` construiește nodurile electrice și modelul circuitului și validează topologia;
   - `calculate_sys` rezolvă sistemul de ecuații și întoarce un `SimulationResult`.
4. Dacă există erori, simularea se oprește și interfața afișează unde și de ce a apărut problema. Dacă totul este în regulă, se afișează rezultatele și animația curentului.
5. La final, utilizatorul poate salva proiectul sau exporta schema circuitului.

## 7. Condiții limită

- **Singularități matematice**: rezistență de 0 Ω și scurtcircuitarea unei surse ideale de tensiune. Motorul inserează o rezistență parazită minimă (`R_MIN = 1 µΩ`) sau emite o notificare contextuală, păstrând sistemul rezolvabil.
- **Convergență**: pentru circuitele cu elemente neliniare, iterația are un număr maxim de pași și un prag de convergență. La depășire, utilizatorul primește un mesaj, nu o blocare.
- **Limite ale componentelor**: la depășirea puterii disipate maxime sau a curentului maxim (de exemplu la un LED), aplicația afișează un avertisment cu o sugestie (de exemplu un rezistor de limitare).
- **Erori ca date**: motorul nu aruncă excepții către interfață; orice problemă este returnată ca `SimError` (locație, motiv, sugestie).

### Prevăzut, dar neimplementat în versiunea curentă

- praguri pentru numărul maxim de componente corelate cu memoria RAM;
- analiză tranzitorie cu gestionarea automată a frecvenței de eșantionare;
- tensiune de străpungere ca limită monitorizată pentru toate semiconductoarele.
