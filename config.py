"""
Módulo: config.py
-----------------
Define la clase `Config`, que actúa como un Singleton (única instancia global)
para centralizar la configuración del sistema de fidelización.

Responsabilidades:
- Mantiene la lista de reglas de fidelización (`LoyaltyRule`).
- Proporciona valores por defecto para las reglas iniciales.
- Permite actualizar o consultar las reglas vigentes.
- Garantiza una única instancia compartida a través de `Config.get_instance()`.

Las reglas definen:
- El número de meses de análisis (window_months).
- La cantidad mínima de visitas requeridas (min_visits).
- El nivel de categoría asociado (resulting_tier).
"""

from __future__ import annotations
from typing import List
from models import LoyaltyTier, LoyaltyRule


class Config:
    """
    Clase Singleton que almacena la configuración global del sistema.

    En este contexto, `Config` mantiene las reglas de fidelización que el motor
    de lealtad (`LoyaltyEngine`) usará para clasificar a los clientes.

    Ejemplo de uso:
    ---------------
    >>> cfg = Config.get_instance()
    >>> reglas = cfg.get_rules()
    >>> cfg.set_rules(nuevas_reglas)
    """

    _instance = None  # Almacena la única instancia de la clase

    def __init__(self):
        """
        Inicializa la configuración con reglas por defecto.
        Por defecto se consideran tres meses de análisis (3m),
        clasificando a los clientes como:
          - "Super VIP" si tiene 4 o más visitas.
          - "VIP" si tiene 2 o más visitas.
        """
        self.rules: List[LoyaltyRule] = [
            LoyaltyRule(min_visits=4, window_months=3, resulting_tier=LoyaltyTier("Super VIP", 2)),
            LoyaltyRule(min_visits=2, window_months=3, resulting_tier=LoyaltyTier("VIP", 1)),
        ]

    #                MÉTODOS PRINCIPALES DE CONFIG
    

    @classmethod
    def get_instance(cls) -> "Config":
        """
        Devuelve la instancia única (Singleton) de Config.
        Si aún no existe, la crea.

        Returns:
            Config: Instancia global de configuración.
        """
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    def set_rules(self, rules: List[LoyaltyRule]) -> None:
        """
        Reemplaza las reglas actuales por una nueva lista,
        ordenándolas de mayor a menor número mínimo de visitas.

        Args:
            rules: Lista de reglas de tipo LoyaltyRule.
        """
        self.rules = sorted(rules, key=lambda r: r.min_visits, reverse=True)

    def get_rules(self) -> List[LoyaltyRule]:
        """
        Devuelve una copia de las reglas de fidelización actuales.

        Returns:
            List[LoyaltyRule]: Lista de reglas vigentes.
        """
        return list(self.rules)

