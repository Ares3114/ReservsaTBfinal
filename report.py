"""
Módulo: report.py
-----------------
Proporciona servicios para generar reportes de fidelización y análisis de visitas
de los clientes del restaurante.

Responsabilidad principal:
- Calcular visitas mensuales por cliente.
- Generar rankings de clientes más frecuentes.
- Exportar los resultados a un archivo CSV.

Este módulo funciona como una capa de servicio (service layer)
que aprovecha los datos almacenados en `VisitRepository` y
`InMemoryCustomerRepository`, delegando los cálculos al motor
de fidelización y estrategias.
"""

from __future__ import annotations
from datetime import date
from typing import List, Tuple, Dict

from models import Customer, LoyaltyTier
from repositories import VisitRepository, InMemoryCustomerRepository
from strategies import months_ago



#                 CLASE: ReportService

class ReportService:
    """
    Clase encargada de generar reportes analíticos a partir de los datos de reservas.

    Combina la información de visitas (proveniente del `VisitRepository`)
    y de los clientes (`InMemoryCustomerRepository`) para producir:
      - Resúmenes de visitas por mes.
      - Rankings de los clientes más activos.
      - Exportaciones de resultados a formato CSV.

    Atributos:
        repo (VisitRepository): Fuente de datos de reservas.
        customers (InMemoryCustomerRepository): Repositorio de clientes cargados.
    """

    def __init__(self, repo: VisitRepository, customers: InMemoryCustomerRepository):
        """
        Inicializa el servicio de reportes con los repositorios necesarios.

        Args:
            repo (VisitRepository): Repositorio que contiene las reservas.
            customers (InMemoryCustomerRepository): Repositorio con los clientes.
        """
        self.repo = repo
        self.customers = customers

   
    #                 MÉTODOS DE ANÁLISIS Y REPORTE
   

    def visits_by_month(self, customer: Customer, months: int, as_of: date) -> Dict[Tuple[int, int], int]:
        """
        Devuelve el número de visitas mensuales de un cliente durante
        un periodo determinado.

        Args:
            customer (Customer): Cliente a analizar.
            months (int): Cantidad de meses hacia atrás desde la fecha de referencia.
            as_of (date): Fecha de referencia (normalmente la fecha actual).

        Returns:
            Dict[Tuple[int, int], int]: Diccionario con claves (año, mes) y valores
            correspondientes a la cantidad de visitas.
        """
        return self.repo.visits_by_month(customer.id, months, as_of)

    def ranking_top_customers(self, months: int, as_of: date) -> List[Tuple[Customer, int]]:
        """
        Genera un ranking de los clientes con mayor número de visitas
        dentro de un rango temporal (últimos N meses).

        Args:
            months (int): Cantidad de meses a considerar.
            as_of (date): Fecha de referencia para el cálculo.

        Returns:
            List[Tuple[Customer, int]]: Lista de tuplas (cliente, visitas),
            ordenada de mayor a menor cantidad de visitas.
        """
        # Calcular el inicio del periodo según la cantidad de meses
        start_date = months_ago(as_of, months)
        from datetime import datetime
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(as_of, datetime.max.time())

        # Contar visitas únicas por día y generar ranking
        rows: List[Tuple[Customer, int]] = []
        for c in self.customers.find_all():
            count = self.repo.count_visits(c.id, start_dt, end_dt, unique_per_day=True)
            rows.append((c, count))

        # Ordenar primero por número de visitas (descendente)
        # y luego alfabéticamente por nombre
        rows.sort(key=lambda x: (-x[1], x[0].name.lower()))
        return rows

    def export_ranking_csv(self, rows: List[Tuple[Customer, int]], path: str) -> None:
        """
        Exporta un ranking de clientes a un archivo CSV.

        Args:
            rows (List[Tuple[Customer, int]]): Datos a exportar en formato (cliente, visitas).
            path (str): Ruta de salida del archivo CSV (incluye extensión .csv).

        Genera un archivo con columnas:
            - customer_id
            - name
            - email
            - phone
            - visits_last_window

        Ejemplo de uso:
            >>> svc.export_ranking_csv(rows, "ranking.csv")
        """
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["customer_id", "name", "email", "phone", "visits_last_window"])
            for c, v in rows:
                w.writerow([c.id, c.name, c.email, c.phone, v])

