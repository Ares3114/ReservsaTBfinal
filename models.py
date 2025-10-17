"""
Módulo: models.py
-----------------
Define las clases de datos (modelos) principales del sistema de fidelización.

Responsabilidad:
- Representar de manera estructurada los elementos clave del dominio:
  * Clientes (`Customer`)
  * Reservas (`Reservation`)
  * Reglas de fidelización (`LoyaltyRule`)
  * Categorías de fidelización (`LoyaltyTier`)

Estas clases son simples contenedores de información (`dataclasses`) que
modelan el comportamiento esencial del sistema sin lógica compleja.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional



#                 CLASE: Categoria de fidelización

@dataclass(frozen=True)
class LoyaltyTier:
    """
    Representa un nivel o categoría de fidelización.

    Atributos:
        name (str): Nombre del nivel (ej. 'Regular', 'VIP', 'Super VIP').
        priority (int): Nivel de prioridad. Un número mayor indica una
                        categoría más alta (por ejemplo, 2 > 1).

    Ejemplo:
        >>> tier = LoyaltyTier("Super VIP", priority=2)
        >>> print(tier.name)
        Super VIP
    """
    name: str
    priority: int = 0  # mayor número = nivel más alto



#                 CLASE: Regla Fidelización 

@dataclass
class LoyaltyRule:
    """
    Define una regla de fidelización.

    Cada regla asocia un número mínimo de visitas dentro de una ventana de tiempo
    con un nivel de fidelización (`LoyaltyTier`).

    Atributos:
        min_visits (int): Número mínimo de visitas requeridas.
        window_months (int): Ventana temporal de análisis en meses.
        resulting_tier (LoyaltyTier): Nivel otorgado si se cumple la condición.

    Métodos:
        applies(visits_in_window): Devuelve True si el número de visitas
                                   alcanza el umbral mínimo.

    Ejemplo:
        >>> rule = LoyaltyRule(3, 2, LoyaltyTier("VIP", 1))
        >>> rule.applies(4)
        True
    """
    min_visits: int
    window_months: int
    resulting_tier: LoyaltyTier

    def applies(self, visits_in_window: int) -> bool:
        """
        Evalúa si una cantidad de visitas cumple con el mínimo exigido por la regla.

        Args:
            visits_in_window (int): Total de visitas registradas en la ventana.

        Returns:
            bool: True si se cumple o supera el mínimo requerido.
        """
        return visits_in_window >= self.min_visits


#                 CLASE: Clientes

@dataclass
class Customer:
    """
    Representa a un cliente del sistema.

    Atributos:
        id (str): Identificador único del cliente.
        name (str): Nombre completo del cliente.
        email (str): Correo electrónico.
        phone (str): Número telefónico de contacto.

    Ejemplo:
        >>> c = Customer("C001", "Ana López", "ana@example.com", "999123456")
        >>> print(c.name)
        Ana López
    """
    id: str
    name: str
    email: str
    phone: str



#                 CLASE: Reservacion

@dataclass
class Reservation:
    """
    Representa una reserva registrada en el sistema.

    Atributos:
        id (str): Identificador único de la reserva.
        customer_id (str): ID del cliente asociado.
        dt (datetime): Fecha y hora de la reserva.
        party_size (int): Tamaño del grupo o cantidad de personas.

    Métodos:
        parse_iso(dt_str): Convierte una cadena de texto en objeto datetime,
                           admitiendo múltiples formatos comunes.

    Ejemplo:
        >>> r = Reservation("R01", "C001", datetime(2025, 3, 15, 20, 0), 4)
        >>> print(r.party_size)
        4
    """
    id: str
    customer_id: str
    dt: datetime
    party_size: int

    @staticmethod
    def parse_iso(dt_str: str) -> datetime:
        """
        Convierte una cadena en un objeto datetime.

        Acepta los formatos:
          - 'YYYY-MM-DDTHH:MM' (ISO estándar)
          - 'YYYY-MM-DD HH:MM' (formato común con espacio)
          - 'YYYY-MM-DD' (solo fecha, sin hora)

        Args:
            dt_str (str): Fecha/hora en formato texto.

        Returns:
            datetime: Objeto datetime correspondiente.

        Raises:
            ValueError: Si el formato no es válido.

        Ejemplo:
            >>> Reservation.parse_iso("2025-04-10T18:30")
            datetime.datetime(2025, 4, 10, 18, 30)
        """
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                pass
        raise ValueError(f"Fecha/hora inválida: {dt_str}")
