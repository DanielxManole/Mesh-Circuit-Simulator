"""
Subsistem: Gestionare Date (Validare + Parsing).

Construieste reprezentarea de calcul a circuitului din scena vizuala:
  - identifica nodurile electrice (Union-Find peste pini conectati prin fire);
  - convertit fiecare ComponentItem intr-un Element pentru motor;
  - aplica validari de baza (cel putin un GND, fara pini neconectati etc.).

Iesirea = obiect `ParsedCircuit` consumat de `calculate_sys`.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

from .models import build_element, Element


@dataclass
class ParseError:
    where: str
    why: str
    level: str = "error"   # "error" | "warning"


@dataclass
class ParsedCircuit:
    elements: List[Element] = field(default_factory=list)
    node_count: int = 0
    # ground_node fixat la 0 in solver. Daca nu exista GND, motorul il alege singur.
    ground_node: int = 0
    # pin_node[(uid, pin_name)] -> id nod
    pin_node: Dict[Tuple[str, str], int] = field(default_factory=dict)
    # comp_by_uid[uid] -> ComponentItem (pentru raportare/erori)
    comp_by_uid: Dict[str, Any] = field(default_factory=dict)
    # pin ids care nu au nicio conexiune (avertismente)
    floating_pins: List[Tuple[str, str]] = field(default_factory=list)
    errors: List[ParseError] = field(default_factory=list)


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x

    def find(self, x):
        self.add(x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def parse_circuit(scene) -> ParsedCircuit:
    """Construieste ParsedCircuit din `CircuitScene`."""
    from src.components.component_item import ComponentItem
    from src.components.wire import Wire

    parsed = ParsedCircuit()

    components = [it for it in scene.items() if isinstance(it, ComponentItem)]
    wires = [it for it in scene.items() if isinstance(it, Wire)]

    if not components:
        parsed.errors.append(ParseError("circuit", "Nu exista nicio componenta in circuit.", "error"))
        return parsed

    # ----- Union-Find peste toti pinii pentru a determina nodurile electrice
    uf = _UnionFind()
    pin_keys: Dict[int, Tuple[str, str]] = {}   # id(pin_widget) -> (uid, pin_name)
    for comp in components:
        parsed.comp_by_uid[comp.uid] = comp
        for pin in comp.pins:
            key = (comp.uid, pin.node_name)
            pin_keys[id(pin)] = key
            uf.add(key)

    for wire in wires:
        k1 = pin_keys.get(id(wire.pin1))
        k2 = pin_keys.get(id(wire.pin2))
        if k1 is None or k2 is None:
            continue
        uf.union(k1, k2)

    # ----- Detectare pini neconectati (in afara de GND care e singur prin natura)
    pin_neighbours = {key: 0 for key in pin_keys.values()}
    for wire in wires:
        k1 = pin_keys.get(id(wire.pin1))
        k2 = pin_keys.get(id(wire.pin2))
        if k1: pin_neighbours[k1] = pin_neighbours.get(k1, 0) + 1
        if k2: pin_neighbours[k2] = pin_neighbours.get(k2, 0) + 1

    # ----- Asigneaza id-uri numerice nodurilor (root → int)
    root_to_id: Dict[Any, int] = {}

    def node_id_for(key):
        r = uf.find(key)
        if r not in root_to_id:
            root_to_id[r] = len(root_to_id)
        return root_to_id[r]

    for key in pin_keys.values():
        nid = node_id_for(key)
        parsed.pin_node[key] = nid

    # ----- Determina GND (primul GND component sau cel mai conectat nod)
    gnd_nodes = set()
    for comp in components:
        if comp.kind == "GND":
            key = (comp.uid, comp.pins[0].node_name)
            gnd_nodes.add(parsed.pin_node[key])

    if gnd_nodes:
        ground = sorted(gnd_nodes)[0]
        # Uneste toti GND intr-un singur nod 0 prin remap
        remap = {ground: 0}
        next_free = 1
        for nid in sorted(set(parsed.pin_node.values())):
            if nid in gnd_nodes:
                remap[nid] = 0
            elif nid not in remap:
                remap[nid] = next_free
                next_free += 1
        parsed.pin_node = {k: remap[v] for k, v in parsed.pin_node.items()}
        parsed.ground_node = 0
        parsed.node_count = max(parsed.pin_node.values()) + 1 if parsed.pin_node else 1
    else:
        # Fara GND explicit — auto-pick: nodul cu cele mai multe conexiuni devine 0
        if parsed.pin_node:
            counts = {}
            for k, n in parsed.pin_node.items():
                counts[n] = counts.get(n, 0) + 1
            auto = max(counts, key=counts.get)
            remap = {auto: 0}
            next_free = 1
            for nid in sorted(set(parsed.pin_node.values())):
                if nid == auto:
                    continue
                remap[nid] = next_free
                next_free += 1
            parsed.pin_node = {k: remap[v] for k, v in parsed.pin_node.items()}
            parsed.ground_node = 0
            parsed.node_count = max(parsed.pin_node.values()) + 1
            parsed.errors.append(ParseError(
                "circuit",
                "Niciun GND plasat: am ales automat un nod de referinta. "
                "Recomandat: adauga explicit o componenta 'Masa (GND)'.",
                "warning",
            ))
        else:
            parsed.node_count = 0

    # ----- Construieste elementele de calcul, ignorand GND ca element pasiv
    for comp in components:
        if comp.kind == "GND":
            continue
        nodes = [parsed.pin_node[(comp.uid, p.node_name)] for p in comp.pins]
        try:
            elem = build_element(comp, nodes)
            if elem is None:
                continue
            if isinstance(elem, list):
                parsed.elements.extend(elem)
            else:
                parsed.elements.append(elem)
        except NotImplementedError as ex:
            parsed.errors.append(ParseError(comp.uid, str(ex), "error"))

    # ----- Validari simple
    # componente la care nu raportam pini neconectati (e normal sa fie multi pini liberi)
    skip_floating = {"GND", "ARDUINO"}
    for (uid, pname), n in pin_neighbours.items():
        comp = parsed.comp_by_uid.get(uid)
        if comp and comp.kind in skip_floating:
            continue
        if n == 0:
            parsed.floating_pins.append((uid, pname))

    if parsed.floating_pins:
        for uid, pname in parsed.floating_pins:
            parsed.errors.append(ParseError(
                uid, f"Pin '{pname}' neconectat (nod flotant).", "warning"
            ))

    return parsed
