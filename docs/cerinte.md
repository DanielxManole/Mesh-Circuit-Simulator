# Specificația cerințelor

Specificația cerințelor pentru **Mesh - Simulator de circuite electrice**.
Realizat de Andrei Patrick-Cristian, Manole Daniel și Pralea Bogdan-Ștefan (631AB, Sg.2, FIIR - SIA).

## 1. Introducere

### 1.1. Scopul documentului

Documentul descrie funcționalitățile și cerințele sistemului, precum și interacțiunea utilizatorului cu acesta. Este punct de referință pentru echipa de dezvoltare și pentru beneficiari.

### 1.2. Contextul de utilizare

Sistemul este o unealtă **didactică**, pentru înțelegerea mai ușoară a circuitelor electrice de către studenți și pasionați, dar și o unealtă de **simulare și analiză** la nivel ingineresc, pentru verificări rapide.

### 1.3. Definiții și abrevieri

| Termen | Definiție |
|---|---|
| Simulator | Aplicație care permite crearea, configurarea și testarea circuitelor electrice într-un mediu virtual controlat |
| Drag-and-drop | Plasarea componentelor din bibliotecă în spațiul de lucru prin tragere cu cursorul |
| Schemă electrică | Reprezentarea grafică a unui circuit, cu simboluri standardizate |
| Componentă electrică | Element de bază (rezistență, LED, tranzistor etc.) folosit la construirea unui circuit |
| Parametrizare | Definirea și modificarea valorilor specifice ale componentelor (de exemplu rezistența în ohmi) |
| Analiză în timp real | Afișarea valorilor electrice (tensiune, curent) în timpul simulării sau într-un singur punct |
| Log / Cache | Fișiere de jurnalizare și de salvare a stării curente a proiectului |
| MNA | Analiza Nodală Modificată, metoda de rezolvare folosită de motorul de calcul |
| OS | Sistemul de operare (momentan exclusiv Windows) |

## 2. Descriere generală

### 2.1. Descrierea sistemului

Aplicația permite crearea, configurarea și simularea circuitelor electrice. Circuitele se construiesc prin drag-and-drop dintr-o bibliotecă de componente standard (surse de tensiune, rezistențe, LED-uri, tranzistoare, diode, fotorezistoare, senzori ultrasonici etc.). Aplicația analizează circuitul și oferă informații despre traseul curentului, tensiune, curent și funcționarea componentelor, ajutând la înțelegerea principiilor electrice.

### 2.2. Motivație

Produsul oferă o soluție simplă și accesibilă pentru înțelegerea circuitelor, transformând simularea dintr-o unealtă de testare într-una de predare: explică și logica din spatele fenomenelor fizice.

### 2.3. Produse similare

| Produs | Asemănări | Dezavantaje |
|---|---|---|
| TinkerCAD, Withdiode | Bibliotecă de resurse, modul de creare a circuitului | Parte analitică redusă, parametrizare simplă, lipsa erorilor și a explicațiilor, disponibile doar online |
| LTspice, Multisim | Schemă electrică, parte analitică | Interfață neintuitivă, neorientate pe vizualizare educațională |

### 2.4. Riscurile proiectului

- **Competiția**: aplicațiile consacrate au resurse mai mari și o bază mare de utilizatori în industrie, care tind să nu migreze.
- **Experiența echipei** în circuite electrice era la început doar teoretică.
- **Planificarea**: timpul este limitat, iar echipa trebuie să găsească un compromis comun pentru dezvoltare.

## 3. Sistemul propus

### 3.1. Categorii de utilizatori

| Utilizator | Utilizare | Competențe necesare | Pondere estimată | Frecvență |
|---|---|---|---|---|
| Student / novice | Creează circuite prin drag-and-drop, își validează cunoștințele citind descrierile componentelor | Cunoștințe elementare de fizică, acțiuni digitale simple | 80% | Ridicată (curs, laborator, timp liber) |
| Cadru didactic | Instrument demonstrativ la cursuri | Expertiză în inginerie electrică, abilități pedagogice | 3% | Moderată |
| Specialist | Prototipare rapidă, verificarea logicii unei scheme sau a unor parametri | Studii de profil, experiență în proiectarea circuitelor | 17% | Moderată |

### 3.2. Cerințe de sistem

| | Minim | Recomandat |
|---|---|---|
| Procesor | Dual-core 2 GHz | Quad-core 3 GHz |
| Memorie RAM | 8 GB | 16 GB |
| Stocare | 200 MB | 200 MB |
| Placă video | - | Integrată |
| Intrare | Mouse sau touchpad, tastatură | |
| Ieșire | Monitor | |
| Rețea | Local, fără conexiune la internet | |
| Sistem de operare | Windows | |

### 3.3. Cerințe funcționale

| # | Cerință | Stadiu |
|---|---|---|
| F1 | Adăugarea elementelor electrice | Implementat |
| F2 | Configurarea parametrilor fiecărei componente | Implementat |
| F3 | Definirea conexiunilor între componente | Implementat |
| F4 | Calculul tensiunii și curentului în circuit, pe baza datelor introduse | Implementat (regim DC) |
| F5 | Scurt manual de utilizare pentru fiecare componentă | Implementat (descrieri în catalog) |
| F6 | Semnalarea erorilor, a locului și a motivului lor | Implementat |
| F7 | Afișarea rezultatelor numeric sau grafic | Implementat (tabele, grafic, export CSV și PNG) |
| F8 | Simulări vizuale | Implementat (animația curentului) |
| F9 | Transformarea circuitului într-o schemă | Implementat (export imagine) |

### 3.4. Cerințe nefuncționale

| # | Cerință | Stadiu |
|---|---|---|
| N1 | Simularea se rezolvă într-un timp cât mai scurt | Implementat |
| N2 | Rulează pe Windows | Implementat |
| N3 | Permisiuni de citire/scriere în folderul aplicației | Necesar |
| N4 | Generează fișier de log și cache cu proiectul curent | Implementat (log și autosave) |
| N5 | Interfață intuitivă și plăcută | Implementat |
| N6 | Ușor scalabilă (noi tipuri de componente) | Implementat, vezi `motor-simulare.md` |
| N7 | Nu se blochează la date valide sau invalide | Implementat (erori returnate ca date) |
| N8 | Răspuns rapid la inputul utilizatorului | Implementat |

### 3.5. Modele ale sistemului

#### 3.5.1. Actori și cazuri de utilizare

Actorul principal este **Utilizatorul** (student/novice, cadru didactic sau specialist). Cazurile de utilizare:

- crearea sistemului electric;
- vizualizarea bibliotecii de elemente;
- citirea informațiilor despre elementele electrice;
- rularea simulării;
- vizualizarea datelor analitice obținute în urma rulării;
- realizarea unei scheme de proiectare pe baza circuitului.

Relații: *rularea simulării* este inclusă în *crearea sistemului electric* și include *vizualizarea datelor analitice*; *vizualizarea bibliotecii* extinde *citirea informațiilor* și *crearea sistemului*; *realizarea schemei* extinde *crearea sistemului*.

#### 3.5.2. Priorități

| Prioritate | Cerințe |
|---|---|
| Critică | Adăugarea elementelor, conectarea lor și setarea parametrilor; motorul de calcul `calculate_sys` |
| Ridicată | Afișarea rezultatelor numeric sau grafic, semnalarea clară a erorilor, interfață simplă și intuitivă |
| Medie | Animații vizuale ale curentului, transformarea circuitului într-o schemă tehnică, viteza de calcul |
| Scăzută | Manualul fiecărei piese, fișierele de log și cache, scalabilitatea |

#### 3.5.3. Scenarii de utilizare

**Crearea unui sistem electric**
- *Precondiții*: utilizatorul înțelege componentele electrice.
- *Flux de bază*: introduce componente din bibliotecă, le conectează, creează conexiunile.
- *Alternativă*: deschide un fișier de proiect existent.
- *Postcondiție*: sistemul poate fi salvat.

**Rularea simulării**
- *Precondiție*: circuitul este creat cu elemente din bibliotecă.
- *Flux de bază*: utilizatorul introduce parametrii doriți, apoi rulează simularea; motorul `calculate_sys` calculează rezultatele.
- *Alternativă*: rularea simulării fără modificarea parametrilor.
- *Postcondiții*: animația curentului și calculele analitice bazate pe parametrii elementelor.

**Citirea informațiilor despre componente**
- *Precondiție*: catalogul de componente este deschis.
- *Flux de bază*: căutarea componentei, alegerea ei și citirea informațiilor.
- *Alternativă*: alegerea componentei din meniu.

**Vizualizarea datelor analitice**
- *Precondiții*: circuit creat, parametri introduși, simulare rulată.
- *Flux de bază*: citirea rezultatelor într-un mod intuitiv și cu explicații; opțiune de salvare.
- *Alternativă*: reprezentarea grafică a informațiilor.

**Realizarea schemei**
- *Precondiții*: circuit creat, parametri introduși.
- *Flux de bază*: informațiile despre sistem sunt redate într-un format grafic pentru proiectare.
- *Alternativă*: schemă fără parametri, doar cu elemente.
- *Postcondiție*: schema este exportată.
