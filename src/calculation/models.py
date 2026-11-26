"""
Modele de element pentru motorul `calculate_sys`.

Fiecare model expune:
  uid           : identificator (R1, V2, ...) — folosit la raportare.
  nodes         : tuple cu id-urile nodurilor (in ordinea pinilor componentei).
  needs_current : True daca modelul introduce o necunoscuta de curent (V, IND in DC, METER_I).
  stamp(A, z, v_prev, ic_index, t, dt) : aplica stampila MNA.
  is_linear     : daca False, motorul activeaza iteratia Newton-Raphson.
  postprocess(node_v, branch_i) : extrage marimi de afisare (V, I) prin componenta.

Constante folosite la singularitati:
  R_MIN  = rezistenta parazita inserata implicit pentru a evita matrice singulara.
  R_OPEN = rezistenta "circuit deschis" pentru elemente in DC (CAP, voltmetru).
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
import math


R_MIN  = 1e-6
R_OPEN = 1e9
VT     = 0.02585   # tensiune termica @ 300 K


# ---------------------------------------------------------------------------
# Element de baza
# ---------------------------------------------------------------------------

class Element:
    is_linear = True
    needs_current = False

    def __init__(self, uid, nodes, kind):
        self.uid = uid
        self.nodes = tuple(nodes)
        self.kind = kind
        self.ic_index = None   # offset in vectorul x (>= n_noduri) pentru curentul propriu

    def stamp(self, A, z, v_prev, t, dt):
        raise NotImplementedError

    def postprocess(self, node_v, branch_i):
        """Returneaza dict cu V/I/extras pentru raport."""
        return {}


def stamp_conductance(A, a, b, g):
    """Stampila de conductanta intre nodurile a si b (0 = GND)."""
    if a != 0:
        A[a - 1][a - 1] += g
    if b != 0:
        A[b - 1][b - 1] += g
    if a != 0 and b != 0:
        A[a - 1][b - 1] -= g
        A[b - 1][a - 1] -= g


def stamp_current(z, a, b, I):
    """Sursa de curent I de la nodul a spre b (I > 0 ⇒ iese din a, intra in b)."""
    if a != 0:
        z[a - 1] -= I
    if b != 0:
        z[b - 1] += I


def stamp_voltage(A, z, a, b, V, k):
    """Sursa de tensiune V intre a (+) si b (−), cu necunoscuta de curent la indexul k."""
    if a != 0:
        A[a - 1][k] += 1.0
        A[k][a - 1] += 1.0
    if b != 0:
        A[b - 1][k] -= 1.0
        A[k][b - 1] -= 1.0
    z[k] += V


# ---------------------------------------------------------------------------
# Elemente concrete
# ---------------------------------------------------------------------------

class Resistor(Element):
    def __init__(self, uid, nodes, R):
        super().__init__(uid, nodes, "R")
        self.R = max(R, R_MIN)

    def stamp(self, A, z, v_prev, t, dt):
        g = 1.0 / self.R
        stamp_conductance(A, self.nodes[0], self.nodes[1], g)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        va = node_v[a]; vb = node_v[b]
        u = va - vb
        i = u / self.R
        return {"V": u, "I": i, "P": u * i}


class VoltageSource(Element):
    needs_current = True

    def __init__(self, uid, nodes, V):
        super().__init__(uid, nodes, "V")
        self.V = V

    def stamp(self, A, z, v_prev, t, dt):
        stamp_voltage(A, z, self.nodes[0], self.nodes[1], self.V, self.ic_index)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        return {"V": node_v[a] - node_v[b], "I": branch_i[self.ic_index]}


class CurrentSource(Element):
    def __init__(self, uid, nodes, I):
        super().__init__(uid, nodes, "I")
        self.I = I

    def stamp(self, A, z, v_prev, t, dt):
        # + -> -: curentul iese din +, intra in -
        stamp_current(z, self.nodes[0], self.nodes[1], self.I)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        return {"V": node_v[a] - node_v[b], "I": self.I}


class Capacitor(Element):
    """DC: circuit deschis (R foarte mare ca sa evite floating)."""
    def __init__(self, uid, nodes, C):
        super().__init__(uid, nodes, "CAP")
        self.C = C

    def stamp(self, A, z, v_prev, t, dt):
        g = 1.0 / R_OPEN
        stamp_conductance(A, self.nodes[0], self.nodes[1], g)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        return {"V": node_v[a] - node_v[b], "I": 0.0}


class Inductor(Element):
    """DC: scurtcircuit (R foarte mica)."""
    def __init__(self, uid, nodes, L):
        super().__init__(uid, nodes, "IND")
        self.L = L

    def stamp(self, A, z, v_prev, t, dt):
        stamp_conductance(A, self.nodes[0], self.nodes[1], 1.0 / R_MIN)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        u = node_v[a] - node_v[b]
        return {"V": u, "I": u / R_MIN if R_MIN > 0 else 0.0}


class Switch(Element):
    def __init__(self, uid, nodes, closed):
        super().__init__(uid, nodes, "SW")
        self.closed = bool(closed)

    def stamp(self, A, z, v_prev, t, dt):
        g = 1.0 / R_MIN if self.closed else 1.0 / R_OPEN
        stamp_conductance(A, self.nodes[0], self.nodes[1], g)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        u = node_v[a] - node_v[b]
        R = R_MIN if self.closed else R_OPEN
        return {"V": u, "I": u / R}


class Voltmeter(Element):
    """Comportament: rezistenta foarte mare. Citeste tensiunea finala."""
    def __init__(self, uid, nodes):
        super().__init__(uid, nodes, "METER_V")

    def stamp(self, A, z, v_prev, t, dt):
        stamp_conductance(A, self.nodes[0], self.nodes[1], 1.0 / R_OPEN)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        return {"V": node_v[a] - node_v[b], "I": 0.0, "reading": node_v[a] - node_v[b]}


class Ammeter(Element):
    """Comportament: sursa de tensiune 0V → permite citirea directa a curentului."""
    needs_current = True

    def __init__(self, uid, nodes):
        super().__init__(uid, nodes, "METER_I")

    def stamp(self, A, z, v_prev, t, dt):
        stamp_voltage(A, z, self.nodes[0], self.nodes[1], 0.0, self.ic_index)

    def postprocess(self, node_v, branch_i):
        I = branch_i[self.ic_index]
        return {"V": 0.0, "I": I, "reading": I}


class Photoresistor(Resistor):
    """Rezistenta variabila in functie de nivelul de lumina (0..1)."""
    def __init__(self, uid, nodes, R_dark, R_light, light_level):
        light_level = max(0.0, min(1.0, light_level))
        R = R_dark + (R_light - R_dark) * light_level
        super().__init__(uid, nodes, R)
        self.kind = "PHOTORES"


# ----------------------- Neliniare (Newton-Raphson) ----------------------- #

class Diode(Element):
    """
    Model piecewise-linear (PWL) — robust pentru iteratia Newton-Raphson:
      - blocata (Vd < Vf):     rezistenta foarte mare (~1 GΩ);
      - conducta (Vd >= Vf):   sursa de tensiune Vf in serie cu R_on ≈ 5 Ω.

    Converge tipic in 1-3 iteratii indiferent de complexitatea circuitului;
    nu produce overflow ca modelul exponential.
    """
    is_linear = False
    R_ON  = 5.0
    R_OFF = 1e9

    def __init__(self, uid, nodes, Vf=0.7, Is=1e-12, n=1.0, Vbreakdown=50.0):
        super().__init__(uid, nodes, "D")
        self.Vf  = Vf
        self.Is  = Is        # pastrat pentru calculul afisat (curent saturatie)
        self.n   = n
        self.Vbd = Vbreakdown
        self._conducting = False

    def _decide_state(self, Vd):
        # mic histerezis: o data conducand, mentine pana V scade clar sub Vf
        if self._conducting:
            self._conducting = Vd > (self.Vf - 0.1)
        else:
            self._conducting = Vd >= self.Vf

    def stamp(self, A, z, v_prev, t, dt):
        a, b = self.nodes
        va = v_prev[a]; vb = v_prev[b]
        Vd = va - vb
        self._decide_state(Vd)
        if self._conducting:
            G = 1.0 / self.R_ON
            stamp_conductance(A, a, b, G)
            # Companion pentru sursa de tensiune Vf in serie cu R_on:
            #   I_d = (Vd - Vf) / R_on  ⇒  z -= G*Vf  pentru nodul +
            stamp_current(z, a, b, -G * self.Vf)
        else:
            stamp_conductance(A, a, b, 1.0 / self.R_OFF)

    def postprocess(self, node_v, branch_i):
        a, b = self.nodes
        Vd = node_v[a] - node_v[b]
        if self._conducting and Vd > 0:
            Id = (Vd - self.Vf) / self.R_ON
        else:
            Id = Vd / self.R_OFF
        warn = None
        if Vd < -self.Vbd:
            warn = f"Polarizare inversa {Vd:.2f}V depaseste Vbreakdown ({self.Vbd}V)."
        return {"V": Vd, "I": Id, "P": Vd * Id, "warning": warn}


class LED(Diode):
    """Model didactic: dioda PWL cu Vf specific culorii + indicator luminos."""
    def __init__(self, uid, nodes, Vf=2.0, If_max=0.02, color="rosu"):
        # rezistenta interna mai mare ca sa "satureze" mai realist
        super().__init__(uid, nodes, Vf=Vf, Vbreakdown=5.0)
        self.R_ON = max(2.0, (Vf * 0.1) / max(If_max, 1e-3))
        self.kind = "LED"
        self.If_max = If_max
        self.color = color

    def postprocess(self, node_v, branch_i):
        out = super().postprocess(node_v, branch_i)
        Id = out["I"]
        if Id > self.If_max:
            out["warning"] = (
                f"Curent {Id*1000:.1f}mA depaseste I_max ({self.If_max*1000:.0f}mA). "
                f"Sugestie: adauga un rezistor in serie. "
                f"Pentru o sursa de 5V, R_min ≈ {max(1.0, (5.0 - self.Vf) / self.If_max):.0f} Ω."
            )
        out["lit"] = max(0.0, min(1.0, Id / max(self.If_max, 1e-9)))
        return out


# ---------------------------------------------------------------------------
# Tranzistoare — implementare simpla pentru caz didactic (regiune activa)
# ---------------------------------------------------------------------------

class BJT_NPN(Element):
    """
    Tranzistor NPN simplificat (PWL pe jonctiunea B-E + sursa de curent
    dependenta pentru colector). Suficient pentru ilustrare didactica.
    """
    is_linear = False
    R_BE_ON  = 50.0
    R_BE_OFF = 1e9
    R_CE_OUT = 1e5      # conductanta mica de iesire pentru stabilitate

    def __init__(self, uid, nodes, beta=100.0, Vbe=0.7):
        super().__init__(uid, nodes, "BJT_NPN")
        self.beta = beta
        self.Vbe_on = Vbe
        self._on = False
        self._Ib_prev = 0.0

    def stamp(self, A, z, v_prev, t, dt):
        B, C, E = self.nodes
        Vbe = v_prev[B] - v_prev[E]
        # decizie cu mic histerezis
        if self._on:
            self._on = Vbe > (self.Vbe_on - 0.1)
        else:
            self._on = Vbe >= self.Vbe_on
        # Jonctiunea B-E ca dioda PWL
        if self._on:
            G = 1.0 / self.R_BE_ON
            stamp_conductance(A, B, E, G)
            stamp_current(z, B, E, -G * self.Vbe_on)
            Ib = (Vbe - self.Vbe_on) / self.R_BE_ON
            if Ib < 0: Ib = 0.0
        else:
            stamp_conductance(A, B, E, 1.0 / self.R_BE_OFF)
            Ib = 0.0
        self._Ib_prev = Ib
        # Sursa de curent controlata: Ic = beta * Ib, de la C la E
        Ic = self.beta * Ib
        stamp_current(z, C, E, Ic)
        # conductanta de iesire pentru stabilitate
        stamp_conductance(A, C, E, 1.0 / self.R_CE_OUT)

    def postprocess(self, node_v, branch_i):
        B, C, E = self.nodes
        Vbe = node_v[B] - node_v[E]
        Vce = node_v[C] - node_v[E]
        Ic = self.beta * self._Ib_prev
        regiune = "cut-off"
        if self._on:
            regiune = "saturatie" if Vce < 0.2 else "activ"
        return {"V": Vce, "I": Ic, "Vbe": Vbe, "Ib": self._Ib_prev, "regiune": regiune}


class BJT_PNP(BJT_NPN):
    def __init__(self, uid, nodes, beta=100.0, Vbe=0.7):
        super().__init__(uid, nodes, beta=beta, Vbe=Vbe)
        self.kind = "BJT_PNP"

    def stamp(self, A, z, v_prev, t, dt):
        # Aceleasi formule cu polaritate inversata: U_EB joaca rol de U_BE.
        B, C, E = self.nodes
        Veb = v_prev[E] - v_prev[B]
        if self._on:
            self._on = Veb > (self.Vbe_on - 0.1)
        else:
            self._on = Veb >= self.Vbe_on
        if self._on:
            G = 1.0 / self.R_BE_ON
            stamp_conductance(A, E, B, G)
            stamp_current(z, E, B, -G * self.Vbe_on)
            Ib = (Veb - self.Vbe_on) / self.R_BE_ON
            if Ib < 0: Ib = 0.0
        else:
            stamp_conductance(A, E, B, 1.0 / self.R_BE_OFF)
            Ib = 0.0
        self._Ib_prev = Ib
        Ic = self.beta * Ib
        stamp_current(z, E, C, Ic)
        stamp_conductance(A, E, C, 1.0 / self.R_CE_OUT)


# ---------------------------------------------------------------------------
# Build dispatcher
# ---------------------------------------------------------------------------

def build_element(comp, nodes):
    """Construieste Element-ul (sau o lista de elemente) pentru `ComponentItem`.

    Pentru componente multi-pin (Arduino, potentiometer, releu), aceasta functie
    poate intoarce o lista — `data_parsing` o va aplatiza.
    """
    k = comp.kind
    p = comp.properties
    uid = comp.uid
    # acces facil dupa nume de pin
    pin_node = {pin.node_name: nodes[i] for i, pin in enumerate(comp.pins)}

    if k == "R":
        return Resistor(uid, nodes, float(p.get("resistance", 1000.0)))
    if k == "V":
        return VoltageSource(uid, nodes, float(p.get("voltage", 5.0)))
    if k == "I":
        return CurrentSource(uid, nodes, float(p.get("current", 0.01)))
    if k == "CAP":
        return Capacitor(uid, nodes, float(p.get("capacitance", 1e-6)))
    if k == "IND":
        return Inductor(uid, nodes, float(p.get("inductance", 1e-3)))
    if k == "SW":
        return Switch(uid, nodes, bool(p.get("closed", False)))
    if k == "METER_V":
        return Voltmeter(uid, nodes)
    if k == "METER_I":
        return Ammeter(uid, nodes)
    if k == "PHOTORES":
        return Photoresistor(
            uid, nodes,
            float(p.get("R_dark", 1e6)),
            float(p.get("R_light", 1e3)),
            float(p.get("light_level", 0.5)),
        )
    if k == "D":
        return Diode(uid, nodes,
                     Vf=0.7,
                     Is=float(p.get("Is", 1e-12)),
                     n=float(p.get("n", 1.0)),
                     Vbreakdown=float(p.get("Vbreakdown", 50.0)))
    if k == "LED":
        return LED(uid, nodes,
                   Vf=float(p.get("Vf", 2.0)),
                   If_max=float(p.get("If_max", 0.02)),
                   color=str(p.get("color", "rosu")))
    if k == "BJT_NPN":
        return BJT_NPN(uid, nodes,
                       beta=float(p.get("beta", 100.0)),
                       Vbe=float(p.get("Vbe", 0.7)))
    if k == "BJT_PNP":
        return BJT_PNP(uid, nodes,
                       beta=float(p.get("beta", 100.0)),
                       Vbe=float(p.get("Vbe", 0.7)))
    if k == "ULTRA":
        # nodes in ordinea pinilor: VCC(0), OUT(1), GND(2)
        vcc_v = float(p.get("vcc", 5.0))
        dist  = float(p.get("distance_cm", 100.0))
        out_v = vcc_v * max(0.0, min(1.0, dist / 400.0))
        return VoltageSource(uid, (nodes[1], nodes[2]), out_v)

    # ---------------------------- Arduino & periferice ----------------------
    if k == "ARDUINO":
        return _build_arduino(uid, pin_node, p)
    if k == "BTN":
        return Switch(uid, nodes, bool(p.get("pressed", False)))
    if k == "POT":
        return _build_potentiometer(uid, pin_node, p)
    if k == "BUZZER":
        return Resistor(uid, nodes, float(p.get("resistance", 50.0)))
    if k == "SERVO":
        return _build_servo(uid, pin_node, p)
    if k == "DCMOTOR":
        return Resistor(uid, nodes, float(p.get("R_winding", 8.0)))
    if k == "LM35":
        return _build_lm35(uid, pin_node, p)
    if k == "THERM":
        return _build_thermistor(uid, nodes, p)
    if k == "RELAY":
        return _build_relay(uid, pin_node, p)

    raise NotImplementedError(f"Element neimplementat: {k}")


# ---------------------------------------------------------------------------
# Builders pentru componente multi-element
# ---------------------------------------------------------------------------

def _build_arduino(uid, pin_node, p):
    """Arduino genereaza:
        - V source 5V intre pinul '5V' si 'GND'
        - V source 3.3V intre '3V3' si 'GND'
        - per fiecare digital pin: V source 5V (HIGH) / 0V (LOW) / nimic (INPUT)
        - pini PWM: V source = 5V * (PWM_Dn / 255)
        - GND intern e legat la nodul 'GND' al circuitului (utilizatorul il leaga)
    """
    elements = []
    gnd = pin_node.get("GND")
    if gnd is None:
        return elements

    def vs(name, node, V):
        elements.append(VoltageSource(f"{uid}.{name}", (node, gnd), V))

    if "5V"  in pin_node: vs("5V",  pin_node["5V"],  5.0)
    if "3V3" in pin_node: vs("3V3", pin_node["3V3"], 3.3)
    if "Vin" in pin_node: vs("Vin", pin_node["Vin"], 7.0)   # tipic baterie 9V

    for pin_name, node in pin_node.items():
        if pin_name in ("5V", "3V3", "GND", "Vin"):
            continue
        # analogii sunt intrari — high-impedance, ii lasam in pace (voltaj citit din MNA)
        if pin_name.startswith("A"):
            # adauga un voltmetru "fantoma" ca sa nu lase nodul floating
            elements.append(Voltmeter(f"{uid}.{pin_name}", (node, gnd)))
            continue
        mode = str(p.get(pin_name, "INPUT"))
        if mode == "HIGH":
            vs(pin_name, node, 5.0)
        elif mode == "LOW":
            vs(pin_name, node, 0.0)
        elif mode == "PWM":
            duty = float(p.get(f"PWM_{pin_name}", 128))
            duty = max(0.0, min(255.0, duty))
            vs(pin_name, node, 5.0 * duty / 255.0)
        # INPUT: nimic — daca pinul ramane neconectat, parser-ul semnaleaza floating
        else:
            # pune un voltmetru ca sa-l "ancoram" si sa nu fie floating
            elements.append(Voltmeter(f"{uid}.{pin_name}", (node, gnd)))
    return elements


def _build_potentiometer(uid, pin_node, p):
    R = max(1.0, float(p.get("resistance", 10000.0)))
    pos = max(0.0, min(1.0, float(p.get("position", 0.5))))
    R_aw = max(R_MIN, R * pos)
    R_wb = max(R_MIN, R * (1.0 - pos))
    return [
        Resistor(f"{uid}.AW", (pin_node["A"], pin_node["W"]), R_aw),
        Resistor(f"{uid}.WB", (pin_node["W"], pin_node["B"]), R_wb),
    ]


def _build_servo(uid, pin_node, p):
    # VCC-GND ca sarcina (curent consumat); SIG = intrare de impedanta mare
    vcc, gnd, sig = pin_node["VCC"], pin_node["GND"], pin_node["SIG"]
    i_load = max(0.0, float(p.get("i_load", 0.150)))
    return [
        CurrentSource(f"{uid}.load", (vcc, gnd), i_load),
        Voltmeter(f"{uid}.sig", (sig, gnd)),
    ]


def _build_lm35(uid, pin_node, p):
    vcc, out, gnd = pin_node["VCC"], pin_node["OUT"], pin_node["GND"]
    temp = float(p.get("temperature", 25.0))
    out_v = max(0.0, 0.01 * temp)         # 10 mV / °C
    # Modeleaza: VCC-GND ca rezistenta consum (R mare), OUT-GND ca sursa V
    return [
        Resistor(f"{uid}.icc", (vcc, gnd), 5_000.0),   # curent consum tipic 1 mA
        VoltageSource(f"{uid}.out", (out, gnd), out_v),
    ]


def _build_thermistor(uid, nodes, p):
    import math
    T_C   = float(p.get("temperature", 25.0))
    T_K   = T_C + 273.15
    T25_K = 298.15
    R25   = float(p.get("R_25", 10000.0))
    beta  = float(p.get("Beta", 3950.0))
    try:
        R = R25 * math.exp(beta * (1.0 / T_K - 1.0 / T25_K))
    except OverflowError:
        R = R25 * 1e6
    R = max(R_MIN, min(R, 1e12))
    return Resistor(uid, nodes, R)


def _build_relay(uid, pin_node, p):
    """Bobina = rezistenta. Comutator: COM-NO daca U_bobina > prag, altfel COM-NC.

    Folosim un PWL: comutarea depinde de tensiune. Marcam neliniar prin
    inserarea unei "conexiuni" simulate cu rezistenta mica/mare in functie
    de starea curenta a tensiunii.
    """
    cp, cn = pin_node["C+"], pin_node["C-"]
    com    = pin_node["COM"]
    no     = pin_node["NO"]
    nc     = pin_node["NC"]
    R_coil = float(p.get("R_coil", 70.0))
    threshold = float(p.get("v_threshold", 3.0))
    return [
        Resistor(f"{uid}.coil", (cp, cn), R_coil),
        _RelayContact(f"{uid}.k", (cp, cn, com, no, nc), threshold),
    ]


class _RelayContact(Element):
    """Comutator dependent de tensiunea pe bobina (PWL, neliniar)."""
    is_linear = False
    R_CLOSED = 0.01
    R_OPEN   = 1e9

    def __init__(self, uid, nodes, threshold):
        # nodes = (cp, cn, com, no, nc)
        super().__init__(uid, nodes, "RELAY")
        self.threshold = threshold
        self._energized = False

    def stamp(self, A, z, v_prev, t, dt):
        cp, cn, com, no, nc = self.nodes
        Vc = v_prev[cp] - v_prev[cn]
        # histerezis: o data energizat, ramane pana scade clar
        if self._energized:
            self._energized = abs(Vc) > (self.threshold * 0.6)
        else:
            self._energized = abs(Vc) >= self.threshold
        if self._energized:
            stamp_conductance(A, com, no, 1.0 / self.R_CLOSED)
            stamp_conductance(A, com, nc, 1.0 / self.R_OPEN)
        else:
            stamp_conductance(A, com, no, 1.0 / self.R_OPEN)
            stamp_conductance(A, com, nc, 1.0 / self.R_CLOSED)

    def postprocess(self, node_v, branch_i):
        return {
            "V": 0.0,
            "I": 0.0,
            "state": "ACTIVAT" if self._energized else "in repaus",
        }
