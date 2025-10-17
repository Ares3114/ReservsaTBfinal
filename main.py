"""
Sistema de Fidelización de Clientes (Consola / Python - POO)

Este módulo implementa el menú principal de la aplicación y coordina:
- [1] Carga de reservas desde CSV (selector de archivo con volver/cancelar).
- [2] Configuración de reglas (wizard con volver/cancelar por paso).
- [3] Consulta de categoría actual de un cliente (ID case-insensitive).
- [4] Listado por categoría actual.
- [5] Reporte de todas las fechas y detalle de reservas de un cliente (ID case-insensitive).
- [6] Ranking (últimos N meses).
- [7] Exportación de ranking a CSV con extensión .csv automática.

Incluye helpers de navegación (volver/cancelar) y validaciones de entrada.
"""

from __future__ import annotations
from datetime import date
from typing import List
import os

from models import LoyaltyRule, LoyaltyTier
from repositories import CsvVisitRepository, InMemoryCustomerRepository
from strategies import VisitsInWindowStrategy
from engine import LoyaltyEngine
from report import ReportService
from config import Config


def pause():
    """Pausa la consola hasta que el usuario presione ENTER."""
    input("\nPresiona ENTER para continuar...")


# ====== VOLVER / CANCELAR Helpers ======
BACK_TOKENS = {"b", "B", "<"}
CANCEL_TOKENS = {"x", "X", "q", "Q"}

def ask_text_with_back(prompt: str, prefill: str | None = None) -> tuple[str, str | None]:
    """
    Solicita texto con soporte para volver/cancelar.

    Returns:
        (action, value) con action ∈ {'ok','back','cancel'}.
    """
    suffix = "  [B=volver, X=cancelar]"
    full = f"{prompt} (ENTER para mantener: '{prefill}'){suffix}: " if prefill is not None else f"{prompt}{suffix}: "
    s = input(full).strip()
    if s in BACK_TOKENS:
        return "back", None
    if s in CANCEL_TOKENS:
        return "cancel", None
    if s == "" and prefill is not None:
        return "ok", prefill
    return "ok", s

def ask_int_with_back(prompt: str, prefill: int | None = None, min_value: int | None = None, max_value: int | None = None) -> tuple[str, int | None]:
    """
    Solicita un número entero con soporte para volver/cancelar y validación de rango.

    Returns:
        (action, value) con action ∈ {'ok','back','cancel'}.
    """
    suffix = "  [B=volver, X=cancelar]"
    full = f"{prompt} (ENTER para mantener: {prefill}){suffix}: " if prefill is not None else f"{prompt}{suffix}: "
    s = input(full).strip()
    if s in BACK_TOKENS:
        return "back", None
    if s in CANCEL_TOKENS:
        return "cancel", None
    if s == "" and prefill is not None:
        return "ok", prefill
    try:
        v = int(s)
        if min_value is not None and v < min_value:
            print(f"Valor mínimo permitido: {min_value}")
            return ask_int_with_back(prompt, prefill, min_value, max_value)
        if max_value is not None and v > max_value:
            print(f"Valor máximo permitido: {max_value}")
            return ask_int_with_back(prompt, prefill, min_value, max_value)
        return "ok", v
    except ValueError:
        print("Entrada inválida (debe ser entero).")
        return ask_int_with_back(prompt, prefill, min_value, max_value)

def ask_index_with_back(options_count: int, prompt: str = "Selecciona el número") -> tuple[str, int | None]:
    """
    Solicita un índice 1..N con soporte para volver/cancelar.

    Returns:
        (action, idx) con action ∈ {'ok','back','cancel'}.
    """
    s = input(f"{prompt}  [B=volver, X=cancelar]: ").strip()
    if s in BACK_TOKENS:
        return "back", None
    if s in CANCEL_TOKENS:
        return "cancel", None
    if not s.isdigit():
        print("Entrada inválida.")
        return ask_index_with_back(options_count, prompt)
    idx = int(s)
    if not (1 <= idx <= options_count):
        print("Índice fuera de rango.")
        return ask_index_with_back(options_count, prompt)
    return "ok", idx


# ====== Carga CSV y selección con volver/cancelar ======
def elegir_csv_en_directorio(directorio: str = "sample_data") -> str | None:
    """
    Lista archivos CSV del directorio y permite elegir uno por número.
    """
    try:
        archivos = [f for f in os.listdir(directorio) if f.lower().endswith(".csv")]
    except FileNotFoundError:
        print(f"No existe el directorio: {directorio}")
        return None

    if not archivos:
        print("No se encontraron archivos CSV en el directorio.")
        return None

    print("\nArchivos disponibles:")
    for i, f in enumerate(archivos, 1):
        print(f"[{i}] {f}")

    action, idx = ask_index_with_back(len(archivos), "Selecciona el número del archivo")
    if action in {"back", "cancel"}:
        return None
    return os.path.join(directorio, archivos[idx - 1])

def load_csv(repo: CsvVisitRepository, customers_repo: InMemoryCustomerRepository | None):
    """
    Carga reservas desde el repositorio CSV y refresca/crea el repositorio en memoria.
    """
    try:
        repo.load()
        customers = repo.get_customers()
        if customers_repo is None:
            customers_repo = InMemoryCustomerRepository(customers)
        else:
            customers_repo._customers = customers  # refrescar
        print(f"Cargadas {len(repo.get_reservations())} reservas y {len(customers)} clientes.")
        return customers_repo
    except FileNotFoundError as e:
        print(f"Archivo no encontrado: {e}")
        return customers_repo
    except UnicodeDecodeError:
        print("Problema de codificación. Guarda el CSV como UTF-8 (idealmente UTF-8-SIG).")
        return customers_repo
    except ValueError as e:
        print(f"Error de formato/encabezados: {e}")
        return customers_repo
    except Exception as e:
        print(f"Error inesperado al cargar CSV: {e}")
        return customers_repo


# ====== Impresión de reglas (texto amigable) ======
def print_rules(rules: List[LoyaltyRule] | None = None):
    """
    Muestra las reglas en formato claro para el usuario.
    Ejemplo:
      1. Meses de análisis: 3 | Mínimo de visitas: 4 | Categoría: Super VIP | Prioridad: 2
    """
    cfg = Config.get_instance()
    rules_to_show = rules if rules is not None else cfg.get_rules()
    print("\nReglas actuales (ordenadas por prioridad):")
    if not rules_to_show:
        print("(Sin reglas definidas por el momento)")
        return
    for i, r in enumerate(rules_to_show, start=1):
        print(
            f"{i}. Meses de análisis: {r.window_months} | "
            f"Mínimo de visitas: {r.min_visits} | "
            f"Categoría: {r.resulting_tier.name} | "
            f"Prioridad: {r.resulting_tier.priority}"
        )

# ====== Wizard de reglas con volver/cancelar por paso ======
def rule_wizard(existing: LoyaltyRule | None = None) -> LoyaltyRule | None:
    """
    Asistente paso a paso para crear/editar una regla de fidelización.
    Permite volver [B] o cancelar [X] en cada paso y editar el resumen final.
    """
    w = existing.window_months if existing else None
    mv = existing.min_visits if existing else None
    tier_name = existing.resulting_tier.name if existing else None
    priority = existing.resulting_tier.priority if existing else None

    step = 0  # 0: meses, 1: min_visits, 2: tier_name, 3: priority
    while True:
        if step == 0:
            act, val = ask_int_with_back("Cantidad de meses a analizar (ej. 3)", prefill=w, min_value=1, max_value=60)
            if act == "back":
                print("Estás en el primer campo. Usa X para cancelar si deseas salir.")
                continue
            if act == "cancel":
                return None
            w = val
            step = 1
            continue

        if step == 1:
            act, val = ask_int_with_back("Mínimo de visitas", prefill=mv, min_value=1, max_value=1000)
            if act == "back":
                step = 0
                continue
            if act == "cancel":
                return None
            mv = val
            step = 2
            continue

        if step == 2:
            act, val = ask_text_with_back("Nombrar categoría (ej. VIP, Super VIP)", prefill=tier_name or "VIP")
            if act == "back":
                step = 1
                continue
            if act == "cancel":
                return None
            tier_name = val or "VIP"
            step = 3
            continue

        if step == 3:
            act, val = ask_int_with_back("Nivel de categoría (prioridad; mayor = más alto) [sugerido 1..3]", prefill=priority or 1, min_value=1, max_value=99)
            if act == "back":
                step = 2
                continue
            if act == "cancel":
                return None
            priority = val

            # Resumen final y confirmación/edición puntual
            print("\nResumen de la regla:")
            print(f"- Ventana: {w} mes(es)")
            print(f"- Mínimo visitas: {mv}")
            print(f"- Categoría: {tier_name}")
            print(f"- Prioridad: {priority}")
            choice = input("¿Guardar [G], Editar campo [1-4], Volver [B], Cancelar [X]? ").strip()
            if choice in {"x", "X"}:
                return None
            if choice in {"b", "B", "<"}:
                step = 2
                continue
            if choice in {"1", "2", "3", "4"}:
                step = int(choice) - 1
                continue
            # Guardar por defecto si presiona ENTER o G
            return LoyaltyRule(min_visits=mv, window_months=w, resulting_tier=LoyaltyTier(tier_name, priority))


def configure_rules():
    """
    Editor de reglas con soporte para:
      - N: Nueva (wizard con volver por paso)
      - E: Editar existente (wizard precargado)
      - B: Borrar por índice
      - G: Guardar cambios en Config
      - C: Cancelar (descarta cambios locales)
    Trabaja sobre una copia local y solo persiste al confirmar.
    """
    cfg = Config.get_instance()
    work: List[LoyaltyRule] = list(cfg.get_rules())  # copia local editable

    while True:
        print_rules(work)
        print("\nOpciones: [N]ueva  [E]ditar  [B]orrar  [G]uardar  [C]ancelar")
        op = input("Elige una opción: ").strip().lower()

        if op == "n":
            new_rule = rule_wizard(None)
            if new_rule:
                work.append(new_rule)
                # Orden sugerido: prioridad DESC, luego mínimo de visitas DESC
                work.sort(key=lambda r: (r.resulting_tier.priority, r.min_visits), reverse=True)
                print("→ Regla añadida.")
            else:
                print("→ Creación cancelada.")

        elif op == "e":
            if not work:
                print("No hay reglas para editar.")
                continue
            try:
                idx = int(input("Número de regla a editar: ").strip())
                if not (1 <= idx <= len(work)):
                    print("Índice fuera de rango.")
                    continue
            except ValueError:
                print("Entrada inválida.")
                continue
            edited = rule_wizard(work[idx - 1])
            if edited:
                work[idx - 1] = edited
                work.sort(key=lambda r: (r.resulting_tier.priority, r.min_visits), reverse=True)
                print("→ Regla actualizada.")
            else:
                print("→ Edición cancelada.")

        elif op == "b":
            if not work:
                print("No hay reglas para borrar.")
                continue
            try:
                idx = int(input("Número de regla a borrar: ").strip())
                if not (1 <= idx <= len(work)):
                    print("Índice fuera de rango.")
                    continue
            except ValueError:
                print("Entrada inválida.")
                continue
            removed = work.pop(idx - 1)
            print(f"→ Regla eliminada: window={removed.window_months}m min_visits={removed.min_visits} -> {removed.resulting_tier.name}")

        elif op == "g":
            if not work:
                print("No puedes dejar las reglas vacías. Añade al menos una regla.")
                continue
            cfg.set_rules(work)
            print("Reglas actualizadas.")
            break

        elif op == "c":
            print("Cambios descartados. Reglas vigentes sin modificaciones.")
            break

        else:
            print("Opción inválida. Usa N / E / B / G / C.")


def ensure_engine(repo: CsvVisitRepository | None, customers_repo: InMemoryCustomerRepository | None) -> LoyaltyEngine | None:
    """
    Verifica que exista data cargada y construye el motor de fidelización.
    """
    if repo is None or customers_repo is None:
        print("Primero carga el CSV (opción 1).")
        return None
    cfg = Config.get_instance()
    strategy = VisitsInWindowStrategy(rules_desc=cfg.get_rules(), window_months=3, unique_per_day=True)
    return LoyaltyEngine(strategy=strategy, repo=repo, customers=customers_repo)


def ensure_csv_filename(name: str, default: str = "ranking") -> str:
    """
    Normaliza un nombre para asegurar extensión .csv y remover caracteres inválidos.
    """
    n = (name or default).strip().strip('"').strip("'")
    if not n:
        n = default
    n = "".join(ch for ch in n.replace(" ", "_") if ch not in '\\/:*?"<>|')
    if not n.lower().endswith(".csv"):
        n += ".csv"
    return n


# ====== Helper de formato para detalle de reservas ======
def format_reservation_line(r) -> str:
    """
    Devuelve una línea legible para mostrar el detalle de una reserva.

    Formato:
      - Fecha: YYYY-MM-DD HH:MM | Tamaño de reserva: <party_size> | ID de reserva: <id>
    """
    return (
        f"- Fecha: {r.dt.strftime('%Y-%m-%d %H:%M')} | "
        f"Tamaño de reserva: {r.party_size} | "
        f"ID de reserva: {r.id}"
    )


def main():
    """
    Bucle principal del menú de consola.
    """
    repo: CsvVisitRepository | None = None
    customers_repo: InMemoryCustomerRepository | None = None

    while True:
        # Menú principal
        print("\n=== Sistema de Fidelización de Clientes (Python/POO) ===")
        print("[1] Importar reservas (CSV)")
        print("[2] Configurar reglas de fidelización")
        print("[3] Buscar cliente por ID y ver categoría actual")
        print("[4] Listar clientes por categoría actual")
        print("[5] Reporte: TODOS los días que fue un cliente (detalle completo)")
        print("[6] Ranking top clientes (últimos N meses)")
        print("[7] Exportar ranking a CSV")
        print("[0] Salir")

        choice = input("Elige una opción: ").strip()

        if choice == "1":
            # Seleccionar y cargar CSV (con posibilidad de cancelar)
            path = elegir_csv_en_directorio("sample_data")
            if not path:
                print("No se seleccionó archivo.")
                pause()
                continue
            repo = CsvVisitRepository(path)
            print(f"\nArchivo seleccionado: {os.path.abspath(path)}")
            customers_repo = load_csv(repo, customers_repo)
            pause()

        elif choice == "2":
            # Editor de reglas con wizard (volver/cancelar por paso)
            configure_rules()
            pause()

        elif choice == "3":
            # Clasificar cliente por ID (búsqueda case-insensitive) y mostrar categoría actual
            eng = ensure_engine(repo, customers_repo)
            if eng:
                act, val = ask_text_with_back("ID del cliente")
                if act in {"back", "cancel"}:
                    pause(); continue
                # --- Normalizar ID a minúsculas y hacer búsqueda case-insensitive
                cid_norm = (val or "").strip().lower()
                c = next((cust for cust in customers_repo.find_all() if cust.id.lower() == cid_norm), None)
                if not c:
                    print("Cliente no encontrado.")
                else:
                    tier = eng.classify(c, date.today())
                    print(f"Cliente {c.name} -> Categoría actual: {tier.name}")
            pause()

        elif choice == "4":
            # Listar clientes agrupados por su categoría actual
            eng = ensure_engine(repo, customers_repo)
            if eng:
                as_of = date.today()
                tiers = {}
                for c in customers_repo.find_all():
                    t = eng.classify(c, as_of).name
                    tiers.setdefault(t, []).append(c)
                for tname, lst in sorted(tiers.items(), key=lambda kv: kv[0]):
                    print(f"\n[{tname}]")
                    for c in lst:
                        print(f"- {c.id} {c.name}")
            pause()

        elif choice == "5":
            # Reporte de todas las fechas y reservas del cliente (ID case-insensitive)
            if repo is None or customers_repo is None:
                print("Primero carga el CSV (opción 1)."); pause(); continue

            act, val = ask_text_with_back("ID del cliente")
            if act in {"back", "cancel"}:
                pause(); continue
            # --- Normalizar ID a minúsculas y hacer búsqueda case-insensitive
            cid_norm = (val or "").strip().lower()
            c = next((cust for cust in customers_repo.find_all() if cust.id.lower() == cid_norm), None)
            if not c:
                print("Cliente no encontrado."); pause(); continue

            all_res = [r for r in repo.get_reservations() if r.customer_id.lower() == cid_norm]
            if not all_res:
                print("Este cliente no tiene reservas registradas."); pause(); continue

            all_res.sort(key=lambda r: r.dt)

            print(f"\nDÍAS QUE ASISTIÓ {c.name}:")
            visits_per_day = {}
            for r in all_res:
                day = r.dt.date()
                visits_per_day[day] = visits_per_day.get(day, 0) + 1
            for d in sorted(visits_per_day.keys()):
                print(f"- {d.isoformat()}  ({visits_per_day[d]} reserva(s))")

            # Detalle con formato amigable solicitado
            print(f"\nDETALLE DE RESERVAS DE {c.name}:")
            for r in all_res:
                print(format_reservation_line(r))

            pause()

        elif choice == "6":
            # Ranking de clientes por visitas en los últimos N meses
            if repo is None or customers_repo is None:
                print("Primero carga el CSV (opción 1)."); pause(); continue

            act, months = ask_int_with_back("¿Últimos N meses? (ej. 3)", prefill=3, min_value=1, max_value=60)
            if act in {"back", "cancel"}:
                pause(); continue

            svc = ReportService(repo, customers_repo)
            rows = svc.ranking_top_customers(months, date.today())
            print("\nRanking:")
            for i, (c, v) in enumerate(rows, start=1):
                print(f"{i}. {c.name} ({c.id}) - {v} visitas")
            pause()

        elif choice == "7":
            # Exportar ranking a CSV (agrega .csv automáticamente al nombre)
            if repo is None or customers_repo is None:
                print("Primero carga el CSV (opción 1)."); pause(); continue

            act, months = ask_int_with_back("¿Últimos N meses? (ej. 3)", prefill=3, min_value=1, max_value=60)
            if act in {"back", "cancel"}:
                pause(); continue

            act2, nombre = ask_text_with_back("Nombre del archivo de salida (sin extensión si deseas)", prefill="ranking")
            if act2 in {"back", "cancel"}:
                pause(); continue
            out_path = ensure_csv_filename(nombre or "ranking")

            svc = ReportService(repo, customers_repo)
            rows = svc.ranking_top_customers(months, date.today())
            svc.export_ranking_csv(rows, out_path)
            print(f"Exportado correctamente como: {out_path}")
            pause()

        elif choice == "0":
            # Salir del programa
            print("¡Hasta luego!")
            break

        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()
