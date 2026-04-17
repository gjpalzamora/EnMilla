EnMilla/
├── app.py                # Punto de entrada Streamlit [cite: 33]
├── core/                 # Lógica de negocio y servicios
│   ├── config.py         # Gestión de variables de entorno (.env) [cite: 188]
│   ├── database.py       # Configuración de SQLAlchemy y SessionLocal [cite: 41]
│   └── pdf_service.py    # Generación de POD con fpdf2 [cite: 47, 254]
├── models/               # Definición de tablas (SQLAlchemy) [cite: 38, 51]
│   ├── package.py
│   ├── movement.py
│   └── courier.py
├── modules/              # Lógica de cada módulo funcional [cite: 94]
│   ├── reception.py
│   ├── tracking.py
│   └── dispatch.py
├── scripts/              # Scripts de inicialización y migración
└── requirements.txt      # Dependencias (Python 3.9+, Streamlit, SQLAlchemy, psycopg2) [cite: 30, 234]
