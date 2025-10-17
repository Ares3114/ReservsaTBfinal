"""
Módulo: strategies.py
---------------------
Define las estrategias utilizadas por el motor de fidelización
para clasificar a los clientes en categorías según sus visitas.

Responsabilidad principal:
- Establecer cómo aplicar las reglas de fidelización (`LoyaltyRule`)
  dentro de una ventana de tiempo definida.
- Permitir distintas estrategias de clasificación (por ejemplo,
  visitas por ventana, visitas acumuladas, etc.).
- Incluir utilidades para manejar el cálculo de fechas relativas
  sin depender de librerías externas.

Estructura:
    • months_ago()                → Calcula una fecha N meses atrás.
    • RuleStrategy                → Clase base abstracta para estrategias.
    • VisitsInWindowStrategy      → Estrategia concreta basada en visitas por ventana temporal.
"""

from __future__ import annotations
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from typing import List

from models import LoyaltyRule, LoyaltyTier, Customer
from repositories import VisitRepository


#                    FUNCIÓN: Calculo de meses atras


def months_ago(as_of: date, months: int) -> date:
    """
    Calcula la fecha exacta que ocurrió hace N meses desde una fecha dada.

    Esta función reemplaza dependencias externas (como `dateutil.relativedelta`)
    y ajusta correctamente los días para evitar errores con meses de distinta
    cantidad de días (por ejemplo, pasar de marzo 31 a febrero 28).

    Args:
        as_of (date): Fecha de referencia.
        months (int): Cantidad de meses hacia atrás.

    Returns:
        date: Nueva fecha correspondiente a N meses antes.

    Ejemplo:
        >>> from datetime import date
        >>> months_ago(date(2025, 3, 31), 1)
        datetime.date(2025, 2, 28)
    """
    y = as_of.year
    m = as_of.month - months
    while m <= 0:
        m += 12
        y -= 1
    d = min(as_of.day, [
        31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    ][m - 1])
    return date(y, m, d)



#                    CLASE BASE: Reglas para clasificacion de clientes


class RuleStrategy:
    """
    Clase base abstracta que define la interfaz para las estrategias
    de clasificación de clientes.

    Las subclases deben implementar el método `classify()`, que determina
    el nivel de fidelización (`LoyaltyTier`) de un cliente según las reglas.

    Este patrón permite cambiar la forma en que se evalúan los clientes
    sin modificar el motor (`LoyaltyEngine`).
    """

    def classify(self, customer: Customer, as_of: date, visits: VisitRepository) -> LoyaltyTier:
        """
        Clasifica un cliente según la estrategia definida.

        Args:
            customer (Customer): Cliente a evaluar.
            as_of (date): Fecha de referencia para el cálculo.
            visits (VisitRepository): Repositorio de visitas/reservas.

        Returns:
            LoyaltyTier: Categoría asignada al cliente.

        Nota:
            Este método debe ser implementado por las subclases.
        """
        raise NotImplementedError



#               CLASE: Clasificacion de Clientes


@dataclass
class VisitsInWindowStrategy(RuleStrategy):
    """
    Estrategia que clasifica a los clientes según el número de visitas
    realizadas dentro de una ventana temporal de N meses.

    Usa las reglas configuradas (`LoyaltyRule`) para determinar la categoría
    de fidelización más alta que el cliente cumple.

    Atributos:
        rules_desc (List[LoyaltyRule]): Lista de reglas de fidelización.
        window_months (int): Ventana de análisis en meses.
        unique_per_day (bool): Si True, cuenta solo una visita por día.

    Ejemplo:
        >>> strategy = VisitsInWindowStrategy(rules_desc=reglas, window_months=3)
        >>> tier = strategy.classify(cliente, date.today(), repo)
        >>> print(tier.name)
        'VIP'
    """

    rules_desc: List[LoyaltyRule]
    window_months: int = 3
    unique_per_day: bool = True

    def classify(self, customer: Customer, as_of: date, visits: VisitRepository) -> LoyaltyTier:
        """
        Clasifica un cliente según la cantidad de visitas que realizó
        en la ventana de tiempo especificada.

        Args:
            customer (Customer): Cliente a clasificar.
            as_of (date): Fecha de referencia (por ejemplo, la fecha actual).
            visits (VisitRepository): Fuente de datos de reservas.

        Returns:
            LoyaltyTier: Categoría asignada (por ejemplo, VIP, Super VIP, Regular).
        """
        # Calcular fechas de inicio y fin de la ventana
        start_date = months_ago(as_of, self.window_months)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(as_of, datetime.max.time())

        # Contar visitas únicas en el periodo
        count = visits.count_visits(customer.id, start_dt, end_dt, unique_per_day=self.unique_per_day)

        # Aplicar reglas ordenadas por prioridad o número mínimo de visitas
        for r in self.rules_desc:
            if r.window_months != self.window_months:
                # Permite coexistir reglas con distintas ventanas
                continue
            if r.applies(count):
                return r.resulting_tier

        # Si no cumple ninguna regla, se clasifica como "Regular"
        return LoyaltyTier("Regular", 0)
