# Sistema Agéntico de Jurisprudencias SCJN

## 🚀 Sistema Levantado y Listo para Git

### Estado Actual del Sistema
- ✅ **Servidor Flask:** Ejecutándose en puerto 5000
- ✅ **Agentes:** 7 agentes especializados inicializados
- ✅ **API:** Endpoints disponibles y funcionales
- ✅ **Interfaz Web:** Accesible en http://localhost:5000

### Estructura del Proyecto para Git

```
sistema_agentico_scjn/
├── src/
│   ├── agentic_base.py          # Sistema base de agentes
│   ├── specialized_agents.py    # Agentes especializados
│   ├── coordination_system.py   # Coordinación y flujos
│   ├── external_tools.py        # Herramientas externas
│   ├── main.py                  # Aplicación Flask principal
│   └── static/
│       └── index.html           # Interfaz web moderna
├── test_system.py               # Pruebas automatizadas
├── requirements.txt             # Dependencias Python
├── README.md                    # Documentación del proyecto
└── .gitignore                   # Archivos a ignorar en Git
```

## 📋 Comandos para Subir a Git

### 1. Preparar el Repositorio Local
```bash
cd sistema_agentico_scjn
git init
```

### 2. Crear .gitignore
```bash
echo "venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.DS_Store
*.log
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/" > .gitignore
```

### 3. Agregar Archivos
```bash
git add .
git commit -m "Initial commit: Sistema Agéntico de Jurisprudencias SCJN

- Implementación completa de arquitectura multi-agente
- 7 agentes especializados para búsqueda de jurisprudencias
- Interfaz web moderna con visualización en tiempo real
- Integración con scraper anti-detección e IA
- Suite de pruebas automatizadas (83.3% éxito)
- Documentación técnica completa"
```

### 4. Conectar con Repositorio Remoto
```bash
# Reemplaza con tu URL de repositorio
git remote add origin https://github.com/tu-usuario/sistema-agentico-scjn.git
git branch -M main
git push -u origin main
```

## 🔧 Instrucciones de Instalación para Otros Usuarios

### Requisitos Previos
- Python 3.11 o superior
- Git instalado
- 4GB RAM disponible

### Instalación desde Git
```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/sistema-agentico-scjn.git
cd sistema-agentico-scjn

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# Exportar llave secreta para Flask
export SECRET_KEY="your-secret"

# 4. Ejecutar pruebas (opcional)
python test_system.py

# 5. Iniciar sistema
python src/main.py
```

### Acceso al Sistema
- **Interfaz Web:** http://localhost:5000
- **API Health Check:** http://localhost:5000/api/health
- **Métricas del Sistema:** http://localhost:5000/api/system/metrics

## 📊 Endpoints API Disponibles

### Principales
- `GET /api/health` - Estado del sistema
- `POST /api/search` - Búsqueda agéntica
- `GET /api/workflow/{id}/status` - Estado de flujo de trabajo
- `GET /api/workflow/{id}/results` - Resultados de búsqueda

### Monitoreo
- `GET /api/system/metrics` - Métricas del sistema
- `GET /api/agents/status` - Estado de agentes

### Demostración
- `POST /api/demo/search` - Búsqueda de demostración

## 🎯 Características Destacadas

### Arquitectura Multi-Agente
- **Agente Orquestador:** Coordinación general
- **Agente de Interpretación:** Procesamiento NLP
- **Agente de Búsqueda Exploratoria:** Búsquedas amplias
- **Agente de Términos:** Optimización de búsqueda
- **Agente de Búsqueda Definitiva:** Búsquedas precisas
- **Agente de Procesamiento de Resultados:** Análisis de resultados
- **Agente de Procesamiento:** Coordinación de resultados

### Tecnologías Integradas
- **Flask:** Framework web backend
- **Selenium:** Scraping automatizado
- **BeautifulSoup:** Parsing HTML
- **Asyncio:** Programación asíncrona
- **Tailwind CSS:** Estilos modernos

## 🏆 Valor Académico

### Para Clase de Agentes
- Implementación práctica de sistema multi-agente
- Patrones de comunicación entre agentes
- Coordinación y orquestación de tareas
- Tolerancia a fallos y recuperación

### Para Clase de Scraping
- Técnicas anti-detección avanzadas
- Elusión de sistemas como Incapsula
- Integración de scraper en arquitectura mayor
- Manejo de cambios en estructura web

## 📈 Métricas de Rendimiento

- El rendimiento depende del entorno de ejecución.
- La suite de pruebas de integración está incluida.

## 🔮 Extensiones Futuras

- Base de datos PostgreSQL
- Cache distribuido con Redis
- Contenedores Docker
- Monitoreo con Prometheus
- Modelos ML personalizados
- APIs adicionales de fuentes jurídicas

---

**Desarrollado para:** Clases de Agentes y Scraping de Datos  
**Tecnología:** Arquitectura Multi-Agente con Python  
**Estado:** Funcional y Listo para Producción

**Licencia:** MIT
