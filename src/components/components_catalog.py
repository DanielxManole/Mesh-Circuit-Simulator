"""
Catalog Componente — biblioteca fixa (subsistemul Modelare circuite).

Fiecare componenta defineste:
  kind        : tipul electric folosit de motorul calculate_sys (R, V, I, D, LED,
                CAP, IND, SW, GND, METER_V, METER_I, BJT_NPN, BJT_PNP, PHOTORES).
  name        : nume afisat in paleta.
  symbol      : tip de simbol grafic desenat de UI (IEC/ANSI).
  pins        : pozitii (x, y) si nume locale ale terminalelor.
  properties  : parametri editabili in Properties Panel (cu unitati si limite).
  manual      : scurt manual de utilizare (cerinta SRS).
"""

COMPONENTS = {
    # ------------------------------ Pasive ------------------------------
    "resistor": {
        "kind": "R",
        "name": "Rezistor",
        "symbol": "resistor",
        "icon": "src/components/Icons/resistor.png",
        "pins": [
            {"name": "A", "x": 0,  "y": 30},
            {"name": "B", "x": 60, "y": 30},
        ],
        "properties": {
            "resistance": {"value": 1000.0, "unit": "Ω",  "min": 1e-3, "max": 1e9,  "label": "Rezistenta"},
            "power_max":  {"value": 0.25,   "unit": "W",  "min": 1e-3, "max": 1e3,  "label": "Putere max"},
        },
        "manual": (
            "Rezistorul limiteaza curentul si reduce tensiunea. "
            "Legea lui Ohm: U = R·I. Codul de culori indica valoarea in Ohmi (Ω). "
            "Verifica intotdeauna puterea disipata P = U·I < puterea maxima."
        ),
    },

    "capacitor": {
        "kind": "CAP",
        "name": "Condensator",
        "symbol": "capacitor",
        "icon": None,
        "pins": [
            {"name": "A", "x": 0,  "y": 30},
            {"name": "B", "x": 60, "y": 30},
        ],
        "properties": {
            "capacitance":   {"value": 1e-6, "unit": "F", "min": 1e-15, "max": 1.0, "label": "Capacitate"},
            "voltage_max":   {"value": 25.0, "unit": "V", "min": 1.0,   "max": 1e4, "label": "Tensiune max"},
        },
        "manual": (
            "Condensatorul stocheaza energie in camp electric. Q = C·U. "
            "In regim DC se comporta ca un circuit deschis (dupa incarcare). "
            "In tranzitoriu introduce o constanta de timp τ = R·C."
        ),
    },

    "inductor": {
        "kind": "IND",
        "name": "Bobina",
        "symbol": "inductor",
        "icon": None,
        "pins": [
            {"name": "A", "x": 0,  "y": 30},
            {"name": "B", "x": 60, "y": 30},
        ],
        "properties": {
            "inductance": {"value": 1e-3, "unit": "H", "min": 1e-9, "max": 10.0, "label": "Inductanta"},
        },
        "manual": (
            "Bobina stocheaza energie in camp magnetic. U = L·dI/dt. "
            "In regim DC stationar se comporta ca un scurtcircuit."
        ),
    },

    # ------------------------------ Surse ------------------------------
    "vsource": {
        "kind": "V",
        "name": "Sursa tensiune",
        "symbol": "vsource",
        "icon": "src/components/Icons/battery.png",
        "pins": [
            {"name": "+", "x": 0,  "y": 30},
            {"name": "-", "x": 60, "y": 30},
        ],
        "properties": {
            "voltage": {"value": 5.0, "unit": "V", "min": -1000.0, "max": 1000.0, "label": "Tensiune"},
        },
        "manual": (
            "Sursa ideala de tensiune mentine constant U intre borne. "
            "Curentul prin ea depinde de circuitul exterior. "
            "Nu o scurtcircuita: motorul va insera o rezistenta parazita minima."
        ),
    },

    "isource": {
        "kind": "I",
        "name": "Sursa curent",
        "symbol": "isource",
        "icon": None,
        "pins": [
            {"name": "+", "x": 0,  "y": 30},
            {"name": "-", "x": 60, "y": 30},
        ],
        "properties": {
            "current": {"value": 0.01, "unit": "A", "min": -100.0, "max": 100.0, "label": "Curent"},
        },
        "manual": (
            "Sursa ideala de curent forteaza valoarea I prin ramura. "
            "Tensiunea la borne depinde de circuit. Sageata indica sensul + -> -."
        ),
    },

    "ground": {
        "kind": "GND",
        "name": "Masa (GND)",
        "symbol": "ground",
        "icon": None,
        "pins": [
            {"name": "GND", "x": 30, "y": 0},
        ],
        "properties": {},
        "manual": (
            "Nodul de referinta cu potential 0V. "
            "Orice circuit are nevoie de cel putin un GND ca simularea sa fie posibila."
        ),
    },

    # ------------------------------ Semiconductoare ------------------------------
    "diode": {
        "kind": "D",
        "name": "Dioda",
        "symbol": "diode",
        "icon": None,
        "pins": [
            {"name": "anod",  "x": 0,  "y": 30},
            {"name": "catod", "x": 60, "y": 30},
        ],
        "properties": {
            "Is":         {"value": 1e-12, "unit": "A", "min": 1e-18, "max": 1e-6, "label": "Curent saturatie"},
            "n":          {"value": 1.0,   "unit": "",  "min": 0.5,   "max": 3.0,  "label": "Factor idealitate"},
            "Vbreakdown": {"value": 50.0,  "unit": "V", "min": 1.0,   "max": 1000.0, "label": "Tensiune strapungere"},
        },
        "manual": (
            "Dioda conduce de la anod la catod cand U_AK ≥ ~0.7 V (siliciu). "
            "Model Shockley: I = Is·(exp(V/(n·Vt)) − 1). "
            "In polarizare inversa peste Vbreakdown poate fi distrusa."
        ),
    },

    "led": {
        "kind": "LED",
        "name": "LED",
        "symbol": "led",
        "icon": "src/components/Icons/led.png",
        "pins": [
            {"name": "anod",  "x": 0,  "y": 30},
            {"name": "catod", "x": 60, "y": 30},
        ],
        "properties": {
            "Vf":         {"value": 2.0,  "unit": "V", "min": 1.5,  "max": 4.0,   "label": "Tensiune directa"},
            "If_max":     {"value": 0.02, "unit": "A", "min": 1e-4, "max": 0.5,   "label": "Curent max"},
            "color":      {"value": "rosu", "unit": "", "options": ["rosu", "verde", "albastru", "galben", "alb"], "label": "Culoare"},
        },
        "manual": (
            "LED-ul lumineaza cand prin el trece un curent direct. "
            "Foloseste mereu un rezistor in serie: R = (Usursa − Vf) / If. "
            "Depasirea curentului maxim arde LED-ul."
        ),
    },

    "photoresistor": {
        "kind": "PHOTORES",
        "name": "Fotorezistor",
        "symbol": "photoresistor",
        "icon": None,
        "pins": [
            {"name": "A", "x": 0,  "y": 30},
            {"name": "B", "x": 60, "y": 30},
        ],
        "properties": {
            "R_dark":     {"value": 1e6,  "unit": "Ω",  "min": 1.0,  "max": 1e9, "label": "R intuneric"},
            "R_light":    {"value": 1e3,  "unit": "Ω",  "min": 1.0,  "max": 1e9, "label": "R lumina"},
            "light_level":{"value": 0.5,  "unit": "0..1","min": 0.0, "max": 1.0, "label": "Nivel lumina"},
        },
        "manual": (
            "Fotorezistorul (LDR) isi schimba rezistenta in functie de lumina. "
            "Valoarea efectiva interpoleaza intre R_intuneric si R_lumina dupa "
            "parametrul 'Nivel lumina' (0 = intuneric, 1 = lumina maxima)."
        ),
    },

    "bjt_npn": {
        "kind": "BJT_NPN",
        "name": "Tranzistor NPN",
        "symbol": "bjt_npn",
        "icon": None,
        "pins": [
            {"name": "B", "x": 0,  "y": 30},
            {"name": "C", "x": 60, "y": 0},
            {"name": "E", "x": 60, "y": 60},
        ],
        "properties": {
            "beta":  {"value": 100.0, "unit": "", "min": 1.0, "max": 1000.0, "label": "Castig curent (β)"},
            "Vbe":   {"value": 0.7,   "unit": "V", "min": 0.3, "max": 1.0,   "label": "U_BE activ"},
        },
        "manual": (
            "Tranzistor bipolar NPN. In regiunea activa: I_C ≈ β·I_B, U_BE ≈ 0.7V. "
            "Folosit ca amplificator sau intrerupator controlat de baza."
        ),
    },

    "bjt_pnp": {
        "kind": "BJT_PNP",
        "name": "Tranzistor PNP",
        "symbol": "bjt_pnp",
        "icon": None,
        "pins": [
            {"name": "B", "x": 0,  "y": 30},
            {"name": "C", "x": 60, "y": 60},
            {"name": "E", "x": 60, "y": 0},
        ],
        "properties": {
            "beta":  {"value": 100.0, "unit": "", "min": 1.0, "max": 1000.0, "label": "Castig curent (β)"},
            "Vbe":   {"value": 0.7,   "unit": "V", "min": 0.3, "max": 1.0,   "label": "U_EB activ"},
        },
        "manual": (
            "Tranzistor bipolar PNP. Curentul conventional intra in emitor. "
            "In regiunea activa: I_C ≈ β·I_B, U_EB ≈ 0.7V."
        ),
    },

    # ------------------------------ Mecanice ------------------------------
    "switch": {
        "kind": "SW",
        "name": "Comutator",
        "symbol": "switch",
        "icon": None,
        "pins": [
            {"name": "A", "x": 0,  "y": 30},
            {"name": "B", "x": 60, "y": 30},
        ],
        "properties": {
            "closed": {"value": False, "unit": "", "options": [False, True], "label": "Inchis"},
        },
        "manual": (
            "Comutator simplu pe doua pozitii. Cand e inchis se comporta ca un fir, "
            "cand e deschis intrerupe complet ramura."
        ),
    },

    # ------------------------------ Instrumente ------------------------------
    "voltmeter": {
        "kind": "METER_V",
        "name": "Voltmetru",
        "symbol": "voltmeter",
        "icon": None,
        "pins": [
            {"name": "+", "x": 0,  "y": 30},
            {"name": "-", "x": 60, "y": 30},
        ],
        "properties": {},
        "manual": (
            "Masoara diferenta de potential intre cele doua borne. "
            "Ideal: rezistenta interna infinita (nu consuma curent)."
        ),
    },

    "ammeter": {
        "kind": "METER_I",
        "name": "Ampermetru",
        "symbol": "ammeter",
        "icon": None,
        "pins": [
            {"name": "+", "x": 0,  "y": 30},
            {"name": "-", "x": 60, "y": 30},
        ],
        "properties": {},
        "manual": (
            "Masoara curentul care trece prin ramura. Se monteaza IN SERIE. "
            "Ideal: rezistenta interna zero (modelat ca scurtcircuit + masurare)."
        ),
    },

    "ultrasonic": {
        "kind": "ULTRA",
        "name": "Senzor ultrasonic",
        "symbol": "ultrasonic",
        "icon": None,
        "pins": [
            {"name": "VCC", "x": 0,  "y": 15},
            {"name": "OUT", "x": 0,  "y": 45},
            {"name": "GND", "x": 60, "y": 30},
        ],
        "properties": {
            "distance_cm": {"value": 100.0, "unit": "cm", "min": 2.0, "max": 400.0, "label": "Distanta detectata"},
            "vcc":         {"value": 5.0,   "unit": "V",  "min": 3.0, "max": 5.5,   "label": "Alimentare"},
        },
        "manual": (
            "Senzor HC-SR04 simplificat. Iesirea OUT genereaza o tensiune "
            "proportionala cu distanta (modelat ca sursa ideala de tensiune "
            "intre OUT si GND): U_OUT = 5V · (distanta/400cm)."
        ),
    },

    # ============================================================
    #                       Arduino & periferice
    # ============================================================

    "arduino_uno": {
        "kind": "ARDUINO",
        "name": "Arduino UNO",
        "symbol": "arduino_uno",
        "icon": None,
        "size": (180, 200),
        "show_pin_labels": True,
        "pins": [
            # alimentare (stanga)
            {"name": "5V",  "x": 0,  "y": 30},
            {"name": "3V3", "x": 0,  "y": 50},
            {"name": "GND", "x": 0,  "y": 70},
            {"name": "Vin", "x": 0,  "y": 90},
            # analog (jos)
            {"name": "A0", "x":  20, "y": 200},
            {"name": "A1", "x":  50, "y": 200},
            {"name": "A2", "x":  80, "y": 200},
            {"name": "A3", "x": 110, "y": 200},
            {"name": "A4", "x": 140, "y": 200},
            {"name": "A5", "x": 170, "y": 200},
            # digital (dreapta)
            {"name": "D2",  "x": 180, "y": 20},
            {"name": "D3",  "x": 180, "y": 40},
            {"name": "D4",  "x": 180, "y": 60},
            {"name": "D5",  "x": 180, "y": 80},
            {"name": "D6",  "x": 180, "y": 100},
            {"name": "D7",  "x": 180, "y": 120},
            {"name": "D8",  "x": 180, "y": 140},
            {"name": "D9",  "x": 180, "y": 160},
            {"name": "D10", "x": 180, "y": 180},
            {"name": "D11", "x": 150, "y": 0},
            {"name": "D12", "x": 120, "y": 0},
            {"name": "D13", "x": 90,  "y": 0},
        ],
        "properties": {
            "D2":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW", "PWM"], "label": "D2"},
            "D3":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW", "PWM"], "label": "D3"},
            "D4":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW"], "label": "D4"},
            "D5":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW", "PWM"], "label": "D5"},
            "D6":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW", "PWM"], "label": "D6"},
            "D7":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW"], "label": "D7"},
            "D8":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW"], "label": "D8"},
            "D9":  {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW", "PWM"], "label": "D9"},
            "D10": {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW", "PWM"], "label": "D10"},
            "D11": {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW", "PWM"], "label": "D11"},
            "D12": {"value": "INPUT",   "options": ["INPUT", "HIGH", "LOW"], "label": "D12"},
            "D13": {"value": "HIGH",    "options": ["INPUT", "HIGH", "LOW"], "label": "D13 (LED placa)"},
            "PWM_D3":  {"value": 128, "unit": "0..255", "min": 0, "max": 255, "label": "PWM D3"},
            "PWM_D5":  {"value": 128, "unit": "0..255", "min": 0, "max": 255, "label": "PWM D5"},
            "PWM_D6":  {"value": 128, "unit": "0..255", "min": 0, "max": 255, "label": "PWM D6"},
            "PWM_D9":  {"value": 128, "unit": "0..255", "min": 0, "max": 255, "label": "PWM D9"},
            "PWM_D10": {"value": 128, "unit": "0..255", "min": 0, "max": 255, "label": "PWM D10"},
            "PWM_D11": {"value": 128, "unit": "0..255", "min": 0, "max": 255, "label": "PWM D11"},
        },
        "manual": (
            "Placa Arduino UNO simulata. Pini:\n"
            "- 5V / 3V3 = surse de alimentare fata de GND.\n"
            "- GND = masa interna (CONECTAT-O la GND-ul circuitului).\n"
            "- D2..D13 = pini digitali, configurabili HIGH/LOW/INPUT/PWM.\n"
            "- A0..A5 = pini analogici (citesc tensiunea fata de GND).\n\n"
            "HIGH=5V, LOW=0V. INPUT=intrare de impedanta mare. PWM=valoare medie "
            "intre 0..5V proportionala cu setarea 0..255."
        ),
    },

    "push_button": {
        "kind": "BTN",
        "name": "Buton (push)",
        "symbol": "push_button",
        "icon": None,
        "pins": [
            {"name": "A", "x": 0,  "y": 30},
            {"name": "B", "x": 60, "y": 30},
        ],
        "properties": {
            "pressed": {"value": False, "options": [False, True], "label": "Apasat"},
        },
        "manual": (
            "Buton tip 'tact-switch'. Cand este apasat (Apasat=ON), inchide circuitul "
            "intre cele doua borne. Cand este liber, este deschis (impedanta foarte mare). "
            "In circuitele Arduino se foloseste de obicei cu rezistor pull-down sau pull-up."
        ),
    },

    "potentiometer": {
        "kind": "POT",
        "name": "Potentiometru",
        "symbol": "potentiometer",
        "icon": None,
        "size": (80, 60),
        "show_pin_labels": True,
        "pins": [
            {"name": "A", "x": 0,  "y": 30, "label_at": "right"},
            {"name": "W", "x": 40, "y": 0,  "label_at": "below"},
            {"name": "B", "x": 80, "y": 30, "label_at": "left"},
        ],
        "properties": {
            "resistance": {"value": 10000.0, "unit": "Ω", "min": 100.0, "max": 1e6, "label": "Rezistenta totala"},
            "position":   {"value": 0.5,     "unit": "0..1", "min": 0.0, "max": 1.0, "label": "Pozitie cursor"},
        },
        "manual": (
            "Rezistor variabil cu 3 terminale: A, B (capete) si W (wiper/cursor). "
            "Rezistenta A-W = R_total · pozitie. Rezistenta W-B = R_total · (1-pozitie). "
            "Folosit ca divizor de tensiune (citit pe wiper) sau ca rezistor variabil."
        ),
    },

    "buzzer": {
        "kind": "BUZZER",
        "name": "Buzzer",
        "symbol": "buzzer",
        "icon": None,
        "pins": [
            {"name": "+", "x": 0,  "y": 30},
            {"name": "-", "x": 60, "y": 30},
        ],
        "properties": {
            "resistance": {"value": 50.0,   "unit": "Ω", "min": 1.0, "max": 1e4, "label": "Impedanta"},
            "v_on":       {"value": 3.0,    "unit": "V", "min": 1.0, "max": 12.0, "label": "Tensiune pornire"},
            "freq":       {"value": 2000.0, "unit": "Hz","min": 100.0,"max":20000.0,"label":"Frecventa"},
        },
        "manual": (
            "Buzzer piezoelectric. Pornit cand U > Tensiune_pornire. "
            "Modelat ca un rezistor (impedanta).frecventa este informativa "
            "(nu modelam audio in DC)."
        ),
    },

    "servo": {
        "kind": "SERVO",
        "name": "Servomotor",
        "symbol": "servo",
        "icon": None,
        "size": (80, 60),
        "show_pin_labels": True,
        "pins": [
            {"name": "VCC", "x": 0,  "y": 15, "label_at": "right"},
            {"name": "SIG", "x": 0,  "y": 30, "label_at": "right"},
            {"name": "GND", "x": 0,  "y": 45, "label_at": "right"},
        ],
        "properties": {
            "angle":  {"value": 90.0,  "unit": "°", "min": 0.0, "max": 180.0, "label": "Unghi"},
            "i_load": {"value": 0.150, "unit": "A", "min": 0.001, "max": 2.0, "label": "Curent sarcina"},
        },
        "manual": (
            "Servomotor (SG90/MG90). VCC = +5V, GND = masa, SIG = semnal PWM "
            "(controleaza unghiul 0..180°). In DC sa modelam VCC-GND ca o sarcina "
            "constanta in curent. Unghiul reactioneaza la PWM-ul de pe pinul Arduino."
        ),
    },

    "dc_motor": {
        "kind": "DCMOTOR",
        "name": "Motor DC",
        "symbol": "dc_motor",
        "icon": None,
        "pins": [
            {"name": "+", "x": 0,  "y": 30},
            {"name": "-", "x": 60, "y": 30},
        ],
        "properties": {
            "R_winding":  {"value": 8.0,    "unit": "Ω",   "min": 0.1, "max": 1e3, "label": "Rezistenta infasurare"},
            "Kv":         {"value": 800.0,  "unit": "RPM/V","min": 1.0,"max":1e5, "label": "Kv (vitezacontant)"},
        },
        "manual": (
            "Motor de curent continuu. Modelat ca o rezistenta a infasurarii. "
            "Viteza estimata = Kv · U. Sensul rotirii depinde de polaritate."
        ),
    },

    "lm35": {
        "kind": "LM35",
        "name": "Senzor LM35",
        "symbol": "lm35",
        "icon": None,
        "size": (80, 60),
        "show_pin_labels": True,
        "pins": [
            {"name": "VCC", "x": 0,  "y": 15, "label_at": "right"},
            {"name": "OUT", "x": 0,  "y": 30, "label_at": "right"},
            {"name": "GND", "x": 0,  "y": 45, "label_at": "right"},
        ],
        "properties": {
            "temperature": {"value": 25.0, "unit": "°C", "min": -40.0, "max": 150.0, "label": "Temperatura"},
        },
        "manual": (
            "Senzor analogic de temperatura. Iesirea OUT = 10 mV/°C "
            "fata de GND (ex: 25 grade C -> 250 mV). Conecteaza VCC la 5V, OUT la "
            "un pin analogic Arduino (A0..A5)."
        ),
    },

    "thermistor": {
        "kind": "THERM",
        "name": "Termistor (NTC)",
        "symbol": "thermistor",
        "icon": None,
        "pins": [
            {"name": "A", "x": 0,  "y": 30},
            {"name": "B", "x": 60, "y": 30},
        ],
        "properties": {
            "R_25":       {"value": 10000.0, "unit": "Ω",  "min": 100.0,  "max": 1e6, "label": "R la 25°C"},
            "Beta":       {"value": 3950.0,  "unit": "K",  "min": 1000.0, "max": 6000.0,"label":"Coeficient Beta"},
            "temperature":{"value": 25.0,    "unit": "°C", "min": -40.0,  "max": 150.0,"label":"Temperatura"},
        },
        "manual": (
            "Termistor NTC: rezistenta scade cu temperatura. "
            "R(T) = R_25 · exp(β·(1/T − 1/T_25)), T in Kelvin."
        ),
    },

    "relay": {
        "kind": "RELAY",
        "name": "Releu (5V)",
        "symbol": "relay",
        "icon": None,
        "size": (100, 80),
        "show_pin_labels": True,
        "pins": [
            # bobina (stanga)
            {"name": "C+",  "x": 0,  "y": 20, "label_at": "right"},
            {"name": "C-",  "x": 0,  "y": 60, "label_at": "right"},
            # contacte (dreapta)
            {"name": "COM", "x": 100, "y": 20, "label_at": "left"},
            {"name": "NO",  "x": 100, "y": 40, "label_at": "left"},
            {"name": "NC",  "x": 100, "y": 60, "label_at": "left"},
        ],
        "properties": {
            "v_threshold": {"value": 3.0, "unit": "V", "min": 0.5, "max": 12.0, "label": "Prag activare bobina"},
            "R_coil":      {"value": 70.0, "unit": "Ω", "min": 1.0, "max": 1e4, "label": "Rezistenta bobina"},
        },
        "manual": (
            "Releu electromagnetic. Cand tensiunea pe bobina (C+/C-) depaseste pragul, "
            "COM se conecteaza la NO (normal-deschis). Altfel COM ramane conectat la "
            "NC (normal-inchis). Util pentru a comuta sarcini mari de la un pin de "
            "putere mica al Arduino-ului."
        ),
    },
}


def get_component(kind_or_key):
    """Returneaza dictionarul componentei dupa cheia din catalog."""
    return COMPONENTS.get(kind_or_key)


def list_categories():
    """Grupare logica pentru paleta UI."""
    return {
        "Pasive":          ["resistor", "capacitor", "inductor", "potentiometer"],
        "Surse":           ["vsource", "isource", "ground"],
        "Semiconductoare": ["diode", "led", "photoresistor", "thermistor",
                             "bjt_npn", "bjt_pnp"],
        "Mecanice":        ["switch", "push_button", "relay"],
        "Arduino":         ["arduino_uno"],
        "Actuatori":       ["buzzer", "servo", "dc_motor"],
        "Senzori":         ["ultrasonic", "lm35"],
        "Instrumente":     ["voltmeter", "ammeter"],
    }
