"""
Módulo: engine.py
-----------------
Define la clase `LoyaltyEngine`, responsable de ejecutar el proceso
de clasificación de clientes según las reglas de fidelización.

Este módulo actúa como el "motor" central del sistema:
coordina la estrategia de evaluación (`RuleStrategy`), los datos
de reservas (`VisitRepository`) y el padrón de clientes
(`InMemoryCustomerRepository`).

Responsabilidad principal:
- Aplicar la estrategia configurada para determinar el nivel de fidelización
  (por ejemplo, Regular, VIP, Super VIP) de cada cliente según sus visitas.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Dict

from models import LoyaltyTier, Customer
from repositories import VisitRepository, InMemoryCustomerRepository
from strategies import RuleStrategy


@dataclass
class LoyaltyEngine:
    """
    Clase principal que implementa el motor de clasificación de fidelización.

    Combina:
      - Una estrategia (`RuleStrategy`) que define cómo evaluar a los clientes.
      - Un repositorio de reservas (`VisitRepository`) con el historial de visitas.
      - Un repositorio de clientes (`InMemoryCustomerRepository`).

    Funciona como una capa de coordinación: no define la lógica de las reglas,
    sino que delega esa tarea a la estrategia activa.

    Atributos:
        strategy (RuleStrategy): Estrategia para evaluar reglas de fidelización.
        repo (VisitRepository): Fuente de datos de reservas.
        customers (InMemoryCustomerRepository): Catálogo de clientes.
    """

    strategy: RuleStrategy
    repo: VisitRepository
    customers: InMemoryCustomerRepository


    #                MÉTODOS PRINCIPALES DEL MOTOR


    def classify(self, customer: Customer, as_of: date) -> LoyaltyTier:
        """
        Clasifica a un cliente específico según las reglas activas.

        Args:
            customer (Customer): Cliente a evaluar.
            as_of (date): Fecha de referencia para el análisis (ej. hoy).

        Returns:
            LoyaltyTier: Categoría de fidelización obtenida (ej. VIP, Super VIP).
        """
        return self.strategy.classify(customer, as_of, self.repo)

    def classify_all(self, as_of: date) -> Dict[str, LoyaltyTier]:
        """
        Clasifica a todos los clientes registrados y devuelve sus categorías.

        Args:
            as_of (date): Fecha de referencia para la evaluación.

        Returns:
            Dict[str, LoyaltyTier]: Diccionario con los IDs de cliente como clave
            y su categoría de fidelización como valor.
        """
        out = {}
        for c in self.customers.find_all():
            out[c.id] = self.classify(c, as_of)
        return out
