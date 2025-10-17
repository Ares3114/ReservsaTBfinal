
"""
Módulo: repositories.py
-----------------------
Define las clases que gestionan el acceso a los datos del sistema de fidelización:
reservas (visitas de clientes) y clientes registrados.

Responsabilidad principal:
- Leer, almacenar y consultar los datos provenientes del archivo CSV de reservas.
- Proveer métodos para contar visitas, agruparlas por mes y obtener clientes.
- Mantener repositorios en memoria y abstraer la fuente de datos (patrón Repository).

Estructura:
    • VisitRepository        → Clase base abstracta (definición de interfaz)
    • CsvVisitRepository     → Implementación que carga datos desde un CSV
    • InMemoryCustomerRepository → Repositorio de clientes en memoria
"""

from __future__ import annotations
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List, Tuple
from pathlib import Path

from models import Reservation, Customer



#                CLASE BASE: Datos de reservas

class VisitRepository:
    """
    Clase base abstracta que define la interfaz de acceso a datos de reservas.

    Su propósito es estandarizar los métodos que las implementaciones concretas
    (como `CsvVisitRepository`) deben proveer.

    Métodos principales:
        - get_reservations(): Devuelve todas las reservas.
        - count_visits(): Cuenta las visitas de un cliente en un rango de fechas.
        - visits_by_month(): Agrupa visitas por mes durante los últimos N meses.
    """

    def get_reservations(self) -> List[Reservation]:
        """Debe devolver la lista de reservas almacenadas."""
        raise NotImplementedError

    def count_visits(
        self,
        customer_id: str,
        start_dt: datetime,
        end_dt: datetime,
        unique_per_day: bool = True
    ) -> int:
        """
        Cuenta cuántas visitas tiene un cliente dentro de un rango temporal.

        Args:
            customer_id (str): ID del cliente.
            start_dt (datetime): Fecha y hora inicial del rango.
            end_dt (datetime): Fecha y hora final del rango.
            unique_per_day (bool): Si True, cuenta solo una visita por día.

        Returns:
            int: Número de visitas registradas dentro del rango.
        """
        res = [
            r for r in self.get_reservations()
            if r.customer_id == customer_id and start_dt <= r.dt <= end_dt
        ]
        if unique_per_day:
            days = {r.dt.date() for r in res}
            return len(days)
        return len(res)

    def visits_by_month(self, customer_id: str, months: int, as_of: date) -> Dict[Tuple[int, int], int]:
        """
        Devuelve la cantidad de visitas por mes durante los últimos N meses.

        Args:
            customer_id (str): ID del cliente.
            months (int): Cantidad de meses hacia atrás desde la fecha actual.
            as_of (date): Fecha de referencia.

        Returns:
            Dict[Tuple[int, int], int]: Diccionario con claves (año, mes)
            y valores que representan la cantidad de visitas en ese mes.
        """
        # Implementación manual de suma de meses sin dependencias externas
        def add_months(d: date, m: int) -> date:
            y = d.year + (d.month - 1 + m) // 12
            m2 = (d.month - 1 + m) % 12 + 1
            day = min(
                d.day,
                [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
                 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m2 - 1]
            )
            return date(y, m2, day)

        # Calcular rango de fechas de análisis
        start_month = add_months(as_of.replace(day=1), -(months - 1))
        end_dt = datetime.combine(as_of, datetime.min.time()).replace(hour=23, minute=59, second=59)
        start_dt = datetime.combine(start_month, datetime.min.time())
        counts: Dict[Tuple[int, int], int] = defaultdict(int)

        # Contar reservas por mes
        for r in self.get_reservations():
            if r.customer_id != customer_id:
                continue
            if start_dt <= r.dt <= end_dt:
                key = (r.dt.year, r.dt.month)
                counts[key] += 1

        # Asegurar que todos los meses del rango aparezcan (aunque tengan 0)
        out = {}
        cur = start_month
        for _ in range(months):
            out[(cur.year, cur.month)] = counts.get((cur.year, cur.month), 0)
            cur = add_months(cur, 1)
        return out



#                CLASE: Carga de reservas desde el CSV


class CsvVisitRepository(VisitRepository):
    """
    Implementación concreta de `VisitRepository` que carga las reservas
    desde un archivo CSV.

    El archivo CSV debe contener las columnas:
        reservation_id, customer_id, name, email, phone, datetime, party_size

    Ejemplo de uso:
        >>> repo = CsvVisitRepository("reservas.csv")
        >>> repo.load()
        >>> reservas = repo.get_reservations()
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self._reservations: List[Reservation] = []
        self._customers: Dict[str, Customer] = {}

    def load(self) -> None:
        """
        Carga los datos desde el archivo CSV y los almacena en memoria.

        Verifica:
            - Existencia del archivo.
            - Presencia de las columnas esperadas.
            - Evita duplicados de reservas (por reservation_id).
            - Valida formato de fecha y tamaño del grupo.

        Ignora filas con errores de formato, pero continúa procesando las demás.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"No existe el archivo: {self.path}")

        with self.path.open(newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            expected = {"reservation_id", "customer_id", "name", "email", "phone", "datetime", "party_size"}
            missing = expected - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"Faltan columnas en CSV: {missing}")

            seen_res_ids = set()
            for i, row in enumerate(reader, start=2):  # Línea 1 = encabezado
                rid = row["reservation_id"].strip()
                if not rid or rid in seen_res_ids:
                    continue  # saltar duplicados o vacíos
                seen_res_ids.add(rid)

                cid = row["customer_id"].strip()
                name = row["name"].strip()
                email = row["email"].strip()
                phone = row["phone"].strip()
                dt_str = row["datetime"].strip()
                size_str = row["party_size"].strip()

                try:
                    dt = Reservation.parse_iso(dt_str)
                    size = int(size_str)
                    if size <= 0:
                        raise ValueError("party_size debe ser > 0")
                except Exception:
                    # En entorno productivo, esto debería registrarse en logs
                    continue

                # Registrar cliente si aún no existe
                if cid not in self._customers:
                    self._customers[cid] = Customer(id=cid, name=name, email=email, phone=phone)

                # Agregar reserva
                self._reservations.append(Reservation(id=rid, customer_id=cid, dt=dt, party_size=size))

    def get_reservations(self) -> List[Reservation]:
        """Devuelve una copia de la lista de reservas cargadas."""
        return list(self._reservations)

    def get_customers(self) -> Dict[str, Customer]:
        """Devuelve un diccionario de clientes registrados (id → objeto Customer)."""
        return dict(self._customers)


#                CLASE: Almacenamiento de clientes en memoria


class InMemoryCustomerRepository:
    """
    Repositorio simple que almacena clientes en memoria.

    Se utiliza para búsquedas rápidas una vez que los datos han sido
    cargados desde un CSV.

    Ejemplo de uso:
        >>> customers = repo.get_customers()
        >>> mem_repo = InMemoryCustomerRepository(customers)
        >>> cliente = mem_repo.find_by_id("C001")
    """

    def __init__(self, customers: Dict[str, Customer]):
        """
        Inicializa el repositorio en memoria con un diccionario de clientes.

        Args:
            customers (Dict[str, Customer]): Diccionario con los clientes cargados.
        """
        self._customers = customers

    def find_by_id(self, cid: str) -> Customer | None:
        """
        Busca un cliente por su ID.

        Args:
            cid (str): ID del cliente.

        Returns:
            Customer | None: El cliente si existe, o None si no se encuentra.
        """
        return self._customers.get(cid)

    def find_all(self) -> List[Customer]:
        """
        Devuelve una lista con todos los clientes registrados en memoria.

        Returns:
            List[Customer]: Lista de clientes.
        """
        return list(self._customers.values())
