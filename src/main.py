"""
Aplicación Flask principal para el Sistema Agéntico de Jurisprudencias SCJN
Integra todos los componentes del sistema multi-agente
"""

import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import threading
import time
from datetime import datetime

# Importar componentes del sistema agéntico
try:
    from src.coordination_system import create_coordinated_agentic_system
    from src.external_tools import ExternalToolsManager
    AGENTIC_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Componentes agénticos no disponibles: {e}")
    AGENTIC_AVAILABLE = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
CORS(app)

# Variables globales del sistema
agentic_system = None
workflow_orchestrator = None
external_tools = None
system_thread = None

def initialize_agentic_system():
    """Inicializa el sistema agéntico en un hilo separado"""
    global agentic_system, workflow_orchestrator, external_tools
    
    if not AGENTIC_AVAILABLE:
        logger.warning("Sistema agéntico no disponible")
        return
    
    try:
        logger.info("Inicializando sistema agéntico...")
        
        # Crear sistema agéntico coordinado
        agentic_system, workflow_orchestrator = create_coordinated_agentic_system()
        
        # Crear gestor de herramientas externas
        external_tools = ExternalToolsManager()
        
        # Iniciar sistema
        agentic_system.start()
        
        logger.info("Sistema agéntico inicializado exitosamente")
        
    except Exception as e:
        logger.error(f"Error inicializando sistema agéntico: {e}")

@app.route('/api/health')
def health_check():
    """Verificación de salud del sistema"""
    global agentic_system
    
    if agentic_system and agentic_system.running:
        status = agentic_system.get_system_status()
        return jsonify({
            "status": "healthy",
            "system_running": True,
            "agentic_available": AGENTIC_AVAILABLE,
            "timestamp": datetime.now().isoformat(),
            "system_status": status
        })
    else:
        return jsonify({
            "status": "initializing" if AGENTIC_AVAILABLE else "basic_mode",
            "system_running": False,
            "agentic_available": AGENTIC_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/search', methods=['POST'])
def search_jurisprudencias():
    """Endpoint principal para búsqueda de jurisprudencias"""
    global workflow_orchestrator
    
    try:
        data = request.get_json()
        user_query = data.get('query', '')
        session_id = data.get('session_id')
        
        if not user_query:
            return jsonify({"error": "Query is required"}), 400
        
        if not AGENTIC_AVAILABLE or not workflow_orchestrator:
            # Modo básico sin sistema agéntico
            return jsonify({
                "success": True,
                "message": "Búsqueda en modo básico",
                "query": user_query,
                "mode": "basic",
                "results": []
            })
        
        # Iniciar flujo de trabajo agéntico
        workflow_id = workflow_orchestrator.start_workflow(
            "jurisprudencia_search",
            {
                "user_query": user_query,
                "session_id": session_id or f"session_{int(time.time())}"
            }
        )
        
        return jsonify({
            "success": True,
            "workflow_id": workflow_id,
            "message": "Búsqueda agéntica iniciada",
            "status": "processing",
            "mode": "agentic"
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/<workflow_id>/status')
def get_workflow_status(workflow_id):
    """Obtiene el estado de un flujo de trabajo"""
    global workflow_orchestrator
    
    try:
        if not AGENTIC_AVAILABLE or not workflow_orchestrator:
            return jsonify({"error": "Agentic system not available"}), 503
        
        status = workflow_orchestrator.get_workflow_status(workflow_id)
        
        if status:
            return jsonify({
                "success": True,
                "workflow_status": status
            })
        else:
            return jsonify({"error": "Workflow not found"}), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/<workflow_id>/results')
def get_workflow_results(workflow_id):
    """Obtiene los resultados de un flujo de trabajo"""
    global workflow_orchestrator
    
    try:
        if not AGENTIC_AVAILABLE or not workflow_orchestrator:
            return jsonify({"error": "Agentic system not available"}), 503
        
        results = workflow_orchestrator.get_workflow_results(workflow_id)
        
        if results:
            return jsonify({
                "success": True,
                "results": results
            })
        else:
            return jsonify({
                "success": False,
                "message": "Results not ready or workflow not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo resultados: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/metrics')
def get_system_metrics():
    """Obtiene métricas del sistema"""
    global workflow_orchestrator, agentic_system
    
    try:
        metrics = {
            "agentic_available": AGENTIC_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
        
        if AGENTIC_AVAILABLE:
            if workflow_orchestrator:
                metrics["workflow_metrics"] = workflow_orchestrator.get_performance_metrics()
            
            if agentic_system:
                metrics["system_status"] = agentic_system.get_system_status()
        
        return jsonify({
            "success": True,
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/agents/status')
def get_agents_status():
    """Obtiene el estado de todos los agentes"""
    global agentic_system
    
    try:
        if not AGENTIC_AVAILABLE or not agentic_system:
            return jsonify({
                "success": True,
                "agentic_available": False,
                "agents_status": {},
                "total_agents": 0
            })
        
        status = agentic_system.get_system_status()
        
        return jsonify({
            "success": True,
            "agentic_available": True,
            "agents_status": status.get("agents_status", {}),
            "total_agents": status.get("total_agents", 0)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de agentes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/demo/search', methods=['POST'])
def demo_search():
    """Endpoint de demostración para búsqueda básica"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # Simulación de búsqueda para demostración
        demo_results = [
            {
                "id": "demo_001",
                "title": "MARCAS. LA SOLICITUD DE DECLARACIÓN ADMINISTRATIVA DE CADUCIDAD RELATIVA",
                "summary": "Jurisprudencia sobre caducidad de marcas en vía reconvencional...",
                "relevance": 0.95,
                "source": "SCJN",
                "registro": "2023366"
            },
            {
                "id": "demo_002", 
                "title": "PROPIEDAD INDUSTRIAL. PROCEDIMIENTO ADMINISTRATIVO",
                "summary": "Criterios sobre procedimientos administrativos en materia de propiedad industrial...",
                "relevance": 0.87,
                "source": "SCJN",
                "registro": "2023367"
            }
        ]
        
        return jsonify({
            "success": True,
            "query": query,
            "results": demo_results,
            "total_found": len(demo_results),
            "mode": "demo"
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda demo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Sirve archivos estáticos"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({
                "message": "Sistema Agéntico de Jurisprudencias SCJN",
                "status": "running",
                "agentic_available": AGENTIC_AVAILABLE,
                "endpoints": [
                    "/api/health",
                    "/api/search",
                    "/api/demo/search",
                    "/api/system/metrics",
                    "/api/agents/status"
                ]
            })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

def cleanup_system():
    """Limpia recursos del sistema al cerrar"""
    global agentic_system
    
    if agentic_system:
        logger.info("Deteniendo sistema agéntico...")
        agentic_system.stop()

if __name__ == '__main__':
    # Inicializar sistema agéntico en hilo separado si está disponible
    if AGENTIC_AVAILABLE:
        system_thread = threading.Thread(target=initialize_agentic_system)
        system_thread.daemon = True
        system_thread.start()
        
        # Esperar un poco para que el sistema se inicialice
        time.sleep(2)
    
    try:
        # Ejecutar aplicación Flask
        logger.info(f"Iniciando servidor Flask (Modo: {'Agéntico' if AGENTIC_AVAILABLE else 'Básico'})")
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        cleanup_system()

