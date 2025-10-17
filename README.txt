README – Sistema de Fidelización de Clientes (Python/POO)

Descripción general
-------------------
Este proyecto implementa un sistema de fidelización de clientes para un restaurante, diseñado en Python siguiendo principios de Programación Orientada a Objetos (POO) y modularidad.

El sistema permite:
- Importar reservas de clientes desde archivos CSV.
- Configurar reglas de fidelización según frecuencia de visitas.
- Clasificar automáticamente clientes como Regular, VIP o Super VIP.
- Consultar historial de visitas, listar clientes por categoría y generar reportes exportables.

Arquitectura del sistema
------------------------
main.py             → Control principal del sistema y menú en consola.
config.py           → Configuración global con patrón Singleton.
models.py           → Clases base del dominio (Cliente, Reserva, Regla, Nivel).
repositories.py     → Acceso y carga de datos desde CSV.
strategies.py       → Estrategias de clasificación por ventana temporal.
engine.py           → Motor de reglas (coordina repositorios y estrategias).
report.py           → Genera reportes, rankings y exportaciones CSV.

Estructura del proyecto
------------------------
sistema_fidelizacion/
│
├── main.py
├── config.py
├── models.py
├── repositories.py
├── strategies.py
├── engine.py
├── report.py
│
└── sample_data/
    └── reservas.csv

Ejemplo de archivo CSV
-----------------------
reservation_id,customer_id,name,email,phone,datetime,party_size
R001,C001,Ana López,ana@example.com,999123456,2025-01-05 20:00,2
R002,C002,Luis Gómez,luis@example.com,987654321,2025-01-12 21:00,4
R003,C001,Ana López,ana@example.com,999123456,2025-02-18 19:30,2

Modo de uso
-----------
1. Ejecuta el programa principal con:
   python main.py

2. Desde el menú principal selecciona opciones como:
   [1] Importar reservas (CSV)
   [2] Configurar reglas de fidelización
   [3] Buscar cliente por ID
   [4] Listar clientes por categoría
   [5] Reporte de visitas detallado
   [6] Ranking top clientes
   [7] Exportar ranking a CSV
   [0] Salir

Características clave
----------------------
- Reglas configurables con validación y opción de volver/cancelar.
- Clasificación automática según frecuencia de visitas.
- Reportes detallados por cliente y ranking general.
- Exportación de resultados a CSV sin escribir manualmente la extensión.
- Diseño modular, escalable y reutilizable.

Detalles técnicos
-----------------
- Lenguaje: Python 3.10+
- Paradigma: Programación Orientada a Objetos (POO)
- Patrones: Repository, Strategy, Singleton
- Entrada/salida: Archivos CSV (UTF-8)
- Interfaz: Consola (CLI)

Autor y créditos
----------------
Desarrollado por: Eduardo Jesús Pasquel Agüero - Rodrigo Francisco Corilloclla Saldarriaga - Arnol Esnayder Campos Medina - Angel Alonso Alvarez Yamunaque
Curso: Fundamentos de la Programación 2 – UPC (2025)
Asistentes técnicos: ChatGPT - Google Gemeni -  Pedro Ignacio Montenegro Montori 

Referencias
-----------
- PEP 8 – Style Guide for Python Code (van Rossum, 2001)
- PEP 257 – Docstring Conventions
- McConnell, S. (2004). Code Complete (2nd Edition). Microsoft Press
- Martin, R. C. (2009). Clean Code. Prentice Hall
