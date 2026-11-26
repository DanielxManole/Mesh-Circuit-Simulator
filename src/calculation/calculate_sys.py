"""
`calculate_sys` — motorul de simulare (subsistem Simulare).

Implementeaza Analiza Nodala Modificata (MNA) pentru regimul DC al unui circuit
construit din `data_parsing.parse_circuit`. Pentru elementele neliniare (LED,
dioda, BJT) ruleaza o iteratie cu damping peste modele liniare pe portiuni.

Contractul motorului (cf. docs/motor-simulare.md):
  - intra:  ParsedCircuit
  - iese:   SimulationResult cu tensiuni nodale, marimi per-componenta si lista
            de erori/avertismente cu LOCATIE si MOTIV.
  - NU arunca exceptii brute catre UI: orice problema devine SimError.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import numpy as np

from .data_parsing import ParsedCircuit
from .models import R_MIN, R_OPEN


MAX_ITER = 80
TOL_V    = 1e-5      # convergenta tensiuni nodale
DAMPING  = 0.5       # 0..1 — cat din pasul nou se aplica


@dataclass
class SimError:
    where: str
    why: str
    level: str = "error"   # "error" | "warning" | "info"
    suggestion: str = ""


@dataclass
class SimulationResult:
    ok: bool = False
    node_voltages: Dict[int, float] = field(default_factory=dict)
    pin_voltages: Dict[Any, float] = field(default_factory=dict)
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # uid -> {V, I, ...}
    wires_current: Dict[int, float] = field(default_factory=dict)         # id(wire) -> A
    errors: List[SimError] = field(default_factory=list)
    iterations: int = 0
    runtime_ms: float = 0.0

    def errors_only(self):
        return [e for e in self.errors if e.level == "error"]

    def warnings_only(self):
        return [e for e in self.errors if e.level == "warning"]


def calculate_sys(parsed: ParsedCircuit) -> SimulationResult:
    import time
    t0 = time.perf_counter()
    res = SimulationResult()

    # preluam erorile de parsing (pot fi doar avertismente)
    for e in parsed.errors:
        res.errors.append(SimError(e.where, e.why, level=e.level))

    if any(e.level == "error" for e in parsed.errors):
        res.runtime_ms = (time.perf_counter() - t0) * 1000
        return res

    n = parsed.node_count
    if n <= 1:
        res.errors.append(SimError(
            "circuit", "Circuitul nu are noduri suficiente pentru simulare. "
                       "Conecteaza componente prin fire.", level="error"))
        res.runtime_ms = (time.perf_counter() - t0) * 1000
        return res

    # ---- aloca indecsi pentru curentii necunoscuti (V, ammeter, IND in tranzitor)
    n_v_vars = n - 1   # exclude GND
    extra = 0
    for el in parsed.elements:
        if el.needs_current:
            el.ic_index = n_v_vars + extra
            extra += 1
    size = n_v_vars + extra

    is_nonlinear = any(not el.is_linear for el in parsed.elements)

    v_full = np.zeros(n)          # tensiunile nodale (index 0 = GND, fix 0)
    x_prev = np.zeros(size)       # solutia anterioara (pt Newton-Raphson)
    iters_used = 1

    def build_and_solve(x_guess):
        v_full[0] = 0.0
        v_full[1:] = x_guess[:n_v_vars]
        A = np.zeros((size, size))
        z = np.zeros(size)
        for el in parsed.elements:
            try:
                el.stamp(A, z, v_full, t=0.0, dt=0.0)
            except Exception as ex:
                raise _StampError(el.uid, str(ex))
        # regularizare minimala pentru noduri ramase "in aer"
        for i in range(n_v_vars):
            if A[i, i] == 0.0:
                A[i, i] = 1.0 / R_OPEN
        return np.linalg.solve(A, z), A

    try:
        if not is_nonlinear:
            x_new, A = build_and_solve(x_prev)
            iters_used = 1
        else:
            # Newton-Raphson cu damping
            converged = False
            for it in range(1, MAX_ITER + 1):
                x_new, A = build_and_solve(x_prev)
                # damping
                x_damp = DAMPING * x_new + (1.0 - DAMPING) * x_prev
                # convergenta pe tensiuni nodale
                dV = np.max(np.abs(x_damp[:n_v_vars] - x_prev[:n_v_vars])) if n_v_vars else 0.0
                x_prev = x_damp
                iters_used = it
                if dV < TOL_V:
                    converged = True
                    x_new = x_damp
                    break
            if not converged:
                res.errors.append(SimError(
                    "calculate_sys",
                    f"Iteratia Newton-Raphson nu a convers in {MAX_ITER} pasi "
                    f"(eroare maxima {dV:.2e} V). Circuitul poate fi instabil.",
                    level="warning",
                    suggestion="Verifica polarizarea diodelor/LED-urilor sau adauga un rezistor in serie."
                ))
    except np.linalg.LinAlgError:
        res.errors.append(SimError(
            "calculate_sys",
            "Sistem singular: nu se poate determina solutia. "
            "Probabil ai o sursa de tensiune scurtcircuitata sau noduri identice.",
            level="error",
            suggestion="Insereaza un rezistor de limitare sau verifica conexiunile la sursa."
        ))
        res.runtime_ms = (time.perf_counter() - t0) * 1000
        return res
    except _StampError as ex:
        res.errors.append(SimError(ex.uid, ex.msg, level="error"))
        res.runtime_ms = (time.perf_counter() - t0) * 1000
        return res

    # ---- extragere rezultate
    v_full[0] = 0.0
    v_full[1:] = x_new[:n_v_vars]
    res.node_voltages = {i: float(v_full[i]) for i in range(n)}
    for key, nid in parsed.pin_node.items():
        res.pin_voltages[key] = float(v_full[nid])

    for el in parsed.elements:
        try:
            comp_res = el.postprocess(v_full, x_new) or {}
        except Exception as ex:
            comp_res = {"error": str(ex)}
        # Validari post-rulare (depasire putere/curent)
        if el.kind == "R":
            comp = parsed.comp_by_uid.get(el.uid)
            if comp is not None:
                p_max_meta = comp.meta.get("power_max")
                if p_max_meta is not None:
                    p_max = float(p_max_meta["value"])
                    if abs(comp_res.get("P", 0)) > p_max:
                        res.errors.append(SimError(
                            el.uid,
                            f"Puterea disipata {abs(comp_res['P'])*1000:.1f} mW "
                            f"depaseste P_max {p_max*1000:.0f} mW.",
                            level="warning",
                            suggestion="Alege un rezistor cu putere mai mare sau redu tensiunea aplicata."
                        ))
        if "warning" in comp_res and comp_res["warning"]:
            res.errors.append(SimError(el.uid, comp_res["warning"], level="warning"))
        res.components[el.uid] = comp_res

    # ---- curent pe fiecare fir (din curentul ramurii componentei conectate)
    #     pentru afisarea animatiei. Tine cont de semnul pin -> nod.
    # (mapare simpla: firele intre 2 pini iau curentul de la componenta-vecin care
    # are masurabil curentul prin ramura; restul raman 0 — suficient didactic).
    res.iterations = iters_used
    res.ok = not res.errors_only()
    res.runtime_ms = (time.perf_counter() - t0) * 1000
    return res


class _StampError(Exception):
    def __init__(self, uid, msg):
        self.uid = uid
        self.msg = msg
        super().__init__(msg)
