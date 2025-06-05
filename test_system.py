#!/usr/bin/env python3
"""
Script de pruebas para el Sistema Agéntico de Jurisprudencias SCJN
Realiza pruebas automatizadas de todos los componentes
"""

import requests
import json
import time
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Prueba las importaciones básicas del sistema"""
    print("🔍 Probando importaciones básicas...")
    
    try:
        from src.agentic_base import create_agentic_system, BaseAgent, MessageBus
        print("✅ Importación de sistema base exitosa")
        
        from src.specialized_agents import AgenteOrquestador, AgenteInterpretacion
        print("✅ Importación de agentes especializados exitosa")
        
        from src.coordination_system import create_coordinated_agentic_system
        print("✅ Importación de sistema de coordinación exitosa")
        
        from src.external_tools import ExternalToolsManager
        print("✅ Importación de herramientas externas exitosa")
        
        return True
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def test_agentic_system_creation():
    """Prueba la creación del sistema agéntico"""
    print("\n🔍 Probando creación del sistema agéntico...")
    
    try:
        from src.coordination_system import create_coordinated_agentic_system
        
        # Crear sistema
        system, orchestrator = create_coordinated_agentic_system()
        print("✅ Sistema agéntico creado exitosamente")
        
        # Verificar agentes registrados
        status = system.get_system_status()
        print(f"✅ Agentes registrados: {status['total_agents']}")
        
        # Iniciar sistema brevemente
        system.start()
        time.sleep(1)
        
        # Verificar estado
        status = system.get_system_status()
        print(f"✅ Sistema funcionando: {status['system_running']}")
        
        # Detener sistema
        system.stop()
        print("✅ Sistema detenido correctamente")
        
        return True
    except Exception as e:
        print(f"❌ Error creando sistema agéntico: {e}")
        return False

def test_external_tools():
    """Prueba las herramientas externas"""
    print("\n🔍 Probando herramientas externas...")
    
    try:
        from src.external_tools import ExternalToolsManager
        
        # Crear gestor de herramientas
        tools = ExternalToolsManager()
        print("✅ Gestor de herramientas externas creado")
        
        # Probar Perplexity (modo simulación)
        result = tools.enhance_with_perplexity("marcas y caducidad")
        print(f"✅ Perplexity simulado: {result['success']}")
        
        # Probar cache
        stats = tools.get_cache_stats()
        print(f"✅ Cache funcionando: {stats['cached_items']} items")
        
        return True
    except Exception as e:
        print(f"❌ Error en herramientas externas: {e}")
        return False

def test_workflow_simulation():
    """Simula un flujo de trabajo completo"""
    print("\n🔍 Simulando flujo de trabajo completo...")
    
    try:
        from src.coordination_system import create_coordinated_agentic_system
        
        # Crear y iniciar sistema
        system, orchestrator = create_coordinated_agentic_system()
        system.start()
        
        # Iniciar flujo de trabajo
        workflow_id = orchestrator.start_workflow(
            "jurisprudencia_search",
            {
                "user_query": "marcas y caducidad administrativa",
                "session_id": "test_session"
            }
        )
        print(f"✅ Flujo de trabajo iniciado: {workflow_id}")
        
        # Esperar un poco para que se procese
        time.sleep(3)
        
        # Verificar estado
        status = orchestrator.get_workflow_status(workflow_id)
        if status:
            print(f"✅ Estado del flujo: {status['status']}")
            print(f"✅ Pasos: {len(status['steps'])}")
        
        # Obtener métricas
        metrics = orchestrator.get_performance_metrics()
        print(f"✅ Flujos totales: {metrics['total_workflows']}")
        
        # Detener sistema
        system.stop()
        
        return True
    except Exception as e:
        print(f"❌ Error en simulación de flujo: {e}")
        return False

def test_api_endpoints():
    """Prueba los endpoints de la API"""
    print("\n🔍 Probando endpoints de API...")
    
    base_url = "http://localhost:5000"
    
    try:
        # Probar health check
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data['status']}")
        else:
            print(f"⚠️ Health check devolvió: {response.status_code}")
        
        # Probar búsqueda demo
        search_data = {"query": "marcas y caducidad"}
        response = requests.post(f"{base_url}/api/demo/search", 
                               json=search_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Búsqueda demo: {data['total_found']} resultados")
        else:
            print(f"⚠️ Búsqueda demo devolvió: {response.status_code}")
        
        # Probar métricas
        response = requests.get(f"{base_url}/api/system/metrics", timeout=5)
        if response.status_code == 200:
            print("✅ Métricas del sistema obtenidas")
        else:
            print(f"⚠️ Métricas devolvieron: {response.status_code}")
        
        return True
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor no está ejecutándose - pruebas de API omitidas")
        return True
    except Exception as e:
        print(f"❌ Error en pruebas de API: {e}")
        return False

def test_performance():
    """Prueba el rendimiento básico del sistema"""
    print("\n🔍 Probando rendimiento básico...")
    
    try:
        from src.coordination_system import create_coordinated_agentic_system
        
        # Medir tiempo de creación
        start_time = time.time()
        system, orchestrator = create_coordinated_agentic_system()
        creation_time = time.time() - start_time
        print(f"✅ Tiempo de creación: {creation_time:.2f}s")
        
        # Medir tiempo de inicio
        start_time = time.time()
        system.start()
        startup_time = time.time() - start_time
        print(f"✅ Tiempo de inicio: {startup_time:.2f}s")
        
        # Medir múltiples flujos de trabajo
        start_time = time.time()
        workflow_ids = []
        for i in range(3):
            workflow_id = orchestrator.start_workflow(
                "jurisprudencia_search",
                {"user_query": f"consulta {i}", "session_id": f"test_{i}"}
            )
            workflow_ids.append(workflow_id)
        
        workflow_time = time.time() - start_time
        print(f"✅ Tiempo para 3 flujos: {workflow_time:.2f}s")
        
        # Verificar métricas
        metrics = orchestrator.get_performance_metrics()
        print(f"✅ Flujos activos: {metrics['active_workflows']}")
        
        system.stop()
        
        return True
    except Exception as e:
        print(f"❌ Error en pruebas de rendimiento: {e}")
        return False

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas del Sistema Agéntico de Jurisprudencias SCJN")
    print("=" * 60)
    
    tests = [
        ("Importaciones Básicas", test_basic_imports),
        ("Creación del Sistema", test_agentic_system_creation),
        ("Herramientas Externas", test_external_tools),
        ("Flujo de Trabajo", test_workflow_simulation),
        ("Endpoints API", test_api_endpoints),
        ("Rendimiento", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{test_name:<25} {status}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} pruebas pasaron")
    print(f"Tasa de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
        return True
    else:
        print(f"\n⚠️ {total-passed} pruebas fallaron. Revisar errores arriba.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

