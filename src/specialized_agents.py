"""
Agentes Especializados para el Sistema de Jurisprudencias SCJN
Implementación de cada agente según el diagrama de arquitectura
"""

import re
import json
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from src.agentic_base import BaseAgent, MessageBus, MessageType

logger = logging.getLogger(__name__)

class AgenteOrquestador(BaseAgent):
    """
    Agente Orquestador - Coordinador principal del sistema
    Recibe consultas del usuario y coordina la ejecución entre agentes
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("orquestador", message_bus)
        self.capabilities = ["coordination", "task_distribution", "result_aggregation"]
        self.active_sessions: Dict[str, Dict] = {}
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa consultas del usuario y coordina la ejecución"""
        user_query = task_data.get("user_query", "")
        session_id = task_data.get("session_id", f"session_{int(time.time())}")
        
        logger.info(f"Orquestador procesando consulta: {user_query}")
        
        # Crear sesión de trabajo
        self.active_sessions[session_id] = {
            "query": user_query,
            "start_time": datetime.now(),
            "status": "processing",
            "results": {}
        }
        
        # Paso 1: Enviar a Agente de Interpretación
        interpretation_task = {
            "task_id": f"interpret_{session_id}",
            "session_id": session_id,
            "user_query": user_query
        }
        
        self.send_message(
            "interpretacion",
            MessageType.TASK_REQUEST,
            interpretation_task,
            session_id
        )
        
        # Retornar confirmación de inicio
        return {
            "session_id": session_id,
            "status": "initiated",
            "message": "Procesando consulta, por favor espere..."
        }
    
    def handle_coordination(self, message):
        """Maneja respuestas de otros agentes y coordina el flujo"""
        session_id = message.correlation_id
        payload = message.payload
        
        if session_id not in self.active_sessions:
            logger.warning(f"Sesión {session_id} no encontrada")
            return
        
        session = self.active_sessions[session_id]
        
        # Procesar respuesta según el agente emisor
        if message.sender_id == "interpretacion":
            self._handle_interpretation_response(session_id, payload)
        elif message.sender_id == "busqueda_exploratoria":
            self._handle_exploratory_search_response(session_id, payload)
        elif message.sender_id == "terminos_busqueda":
            self._handle_search_terms_response(session_id, payload)
        elif message.sender_id == "busqueda_definitiva":
            self._handle_definitive_search_response(session_id, payload)
        elif message.sender_id == "procesamiento_resultados":
            self._handle_results_processing_response(session_id, payload)
    
    def _handle_interpretation_response(self, session_id: str, payload: Dict):
        """Maneja respuesta del agente de interpretación"""
        if payload.get("success"):
            interpretation_data = payload.get("result", {})
            
            # Enviar a búsqueda exploratoria
            search_task = {
                "task_id": f"explore_{session_id}",
                "session_id": session_id,
                "search_terms": interpretation_data.get("search_terms", []),
                "query_type": interpretation_data.get("query_type", "general"),
                "legal_concepts": interpretation_data.get("legal_concepts", [])
            }
            
            self.send_message(
                "busqueda_exploratoria",
                MessageType.TASK_REQUEST,
                search_task,
                session_id
            )
    
    def _handle_exploratory_search_response(self, session_id: str, payload: Dict):
        """Maneja respuesta de búsqueda exploratoria"""
        if payload.get("success"):
            search_results = payload.get("result", {})
            
            # Enviar a agente de términos para refinamiento
            terms_task = {
                "task_id": f"refine_{session_id}",
                "session_id": session_id,
                "initial_results": search_results,
                "original_query": self.active_sessions[session_id]["query"]
            }
            
            self.send_message(
                "terminos_busqueda",
                MessageType.TASK_REQUEST,
                terms_task,
                session_id
            )
    
    def _handle_search_terms_response(self, session_id: str, payload: Dict):
        """Maneja respuesta del agente de términos"""
        if payload.get("success"):
            refined_terms = payload.get("result", {})
            
            # Enviar a búsqueda definitiva
            definitive_task = {
                "task_id": f"definitive_{session_id}",
                "session_id": session_id,
                "refined_terms": refined_terms.get("optimized_terms", []),
                "search_strategy": refined_terms.get("strategy", "standard")
            }
            
            self.send_message(
                "busqueda_definitiva",
                MessageType.TASK_REQUEST,
                definitive_task,
                session_id
            )
    
    def _handle_definitive_search_response(self, session_id: str, payload: Dict):
        """Maneja respuesta de búsqueda definitiva"""
        if payload.get("success"):
            final_results = payload.get("result", {})
            
            # Enviar a procesamiento de resultados
            processing_task = {
                "task_id": f"process_{session_id}",
                "session_id": session_id,
                "raw_results": final_results,
                "original_query": self.active_sessions[session_id]["query"]
            }
            
            self.send_message(
                "procesamiento_resultados",
                MessageType.TASK_REQUEST,
                processing_task,
                session_id
            )
    
    def _handle_results_processing_response(self, session_id: str, payload: Dict):
        """Maneja respuesta final del procesamiento"""
        session = self.active_sessions[session_id]
        session["status"] = "completed"
        session["results"] = payload.get("result", {})
        session["end_time"] = datetime.now()
        
        logger.info(f"Sesión {session_id} completada exitosamente")

class AgenteInterpretacion(BaseAgent):
    """
    Agente de Interpretación - Procesa lenguaje natural y extrae conceptos jurídicos
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("interpretacion", message_bus)
        self.capabilities = ["nlp", "legal_analysis", "query_classification"]
        self.legal_terms = self._load_legal_dictionary()
    
    def _load_legal_dictionary(self) -> Dict[str, List[str]]:
        """Carga diccionario de términos legales"""
        return {
            "marcas": ["marca", "marcas", "signo distintivo", "registro marcario"],
            "administrativo": ["administrativo", "administrativa", "procedimiento administrativo"],
            "caducidad": ["caducidad", "caducidad relativa", "declaración de caducidad"],
            "reconvencional": ["reconvención", "reconvencional", "vía reconvencional"],
            "amparo": ["amparo", "juicio de amparo", "recurso de amparo"],
            "constitucional": ["constitucional", "constitución", "constitucionalidad"],
            "civil": ["civil", "derecho civil", "código civil"],
            "penal": ["penal", "derecho penal", "código penal"],
            "laboral": ["laboral", "trabajo", "derecho laboral"],
            "fiscal": ["fiscal", "tributario", "derecho fiscal"]
        }
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa consulta del usuario y extrae conceptos jurídicos"""
        user_query = task_data.get("user_query", "")
        
        logger.info(f"Interpretando consulta: {user_query}")
        
        # Análisis de la consulta
        search_terms = self._extract_search_terms(user_query)
        legal_concepts = self._identify_legal_concepts(user_query)
        query_type = self._classify_query_type(user_query)
        
        return {
            "search_terms": search_terms,
            "legal_concepts": legal_concepts,
            "query_type": query_type,
            "original_query": user_query,
            "confidence": self._calculate_confidence(search_terms, legal_concepts)
        }
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extrae términos de búsqueda relevantes"""
        # Limpiar y normalizar
        query_clean = re.sub(r'[^\w\s]', ' ', query.lower())
        words = query_clean.split()
        
        # Filtrar palabras vacías
        stop_words = {"el", "la", "los", "las", "de", "del", "en", "con", "por", "para", "que", "es", "un", "una"}
        terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return terms[:10]  # Limitar a 10 términos principales
    
    def _identify_legal_concepts(self, query: str) -> List[str]:
        """Identifica conceptos jurídicos en la consulta"""
        query_lower = query.lower()
        identified_concepts = []
        
        for concept, terms in self.legal_terms.items():
            for term in terms:
                if term in query_lower:
                    identified_concepts.append(concept)
                    break
        
        return list(set(identified_concepts))
    
    def _classify_query_type(self, query: str) -> str:
        """Clasifica el tipo de consulta"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["qué es", "definición", "concepto", "significa"]):
            return "definition"
        elif any(word in query_lower for word in ["procedimiento", "proceso", "cómo", "pasos"]):
            return "procedure"
        elif any(word in query_lower for word in ["busco", "necesito", "quiero encontrar"]):
            return "search"
        else:
            return "general"
    
    def _calculate_confidence(self, search_terms: List[str], legal_concepts: List[str]) -> float:
        """Calcula confianza en la interpretación"""
        base_confidence = 0.5
        
        # Aumentar confianza por términos legales identificados
        if legal_concepts:
            base_confidence += 0.3 * min(len(legal_concepts) / 3, 1)
        
        # Aumentar confianza por número de términos relevantes
        if search_terms:
            base_confidence += 0.2 * min(len(search_terms) / 5, 1)
        
        return min(base_confidence, 1.0)

class AgenteBusquedaExploratoria(BaseAgent):
    """
    Agente de Búsqueda Exploratoria - Realiza búsquedas amplias en SCJN
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("busqueda_exploratoria", message_bus)
        self.capabilities = ["web_scraping", "exploratory_search", "data_extraction"]
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza búsqueda exploratoria en SCJN"""
        search_terms = task_data.get("search_terms", [])
        query_type = task_data.get("query_type", "general")
        
        logger.info(f"Búsqueda exploratoria con términos: {search_terms}")
        
        # Simular búsqueda exploratoria (en implementación real usaría scraper)
        results = self._simulate_exploratory_search(search_terms)
        
        return {
            "found_results": len(results),
            "results": results,
            "search_terms_used": search_terms,
            "coverage_score": self._calculate_coverage(results)
        }
    
    def _simulate_exploratory_search(self, terms: List[str]) -> List[Dict]:
        """Simula búsqueda exploratoria"""
        # En implementación real, aquí iría la lógica de scraping
        simulated_results = []
        
        for i, term in enumerate(terms[:3]):  # Simular hasta 3 resultados por término
            simulated_results.append({
                "id": f"result_{i}",
                "title": f"Jurisprudencia relacionada con {term}",
                "summary": f"Resultado exploratorio para el término {term}",
                "relevance": 0.7 + (i * 0.1),
                "source": "SCJN",
                "term_matched": term
            })
        
        return simulated_results
    
    def _calculate_coverage(self, results: List[Dict]) -> float:
        """Calcula cobertura de la búsqueda exploratoria"""
        if not results:
            return 0.0
        
        # Simular cálculo de cobertura basado en diversidad de resultados
        unique_sources = len(set(r.get("source", "") for r in results))
        avg_relevance = sum(r.get("relevance", 0) for r in results) / len(results)
        
        return min((unique_sources * 0.3 + avg_relevance * 0.7), 1.0)

class AgenteTerminosBusqueda(BaseAgent):
    """
    Agente de Términos de Búsqueda - Optimiza y refina términos de búsqueda
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("terminos_busqueda", message_bus)
        self.capabilities = ["term_optimization", "synonym_generation", "search_refinement"]
        self.synonyms_db = self._load_synonyms()
    
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """Carga base de datos de sinónimos jurídicos"""
        return {
            "caducidad": ["vencimiento", "expiración", "pérdida de vigencia"],
            "administrativo": ["gubernamental", "oficial", "burocrático"],
            "reconvencional": ["contrademanda", "demanda reconvencional"],
            "marca": ["signo distintivo", "denominación comercial"],
            "procedimiento": ["proceso", "trámite", "gestión"]
        }
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimiza términos de búsqueda basado en resultados exploratorios"""
        initial_results = task_data.get("initial_results", {})
        original_query = task_data.get("original_query", "")
        
        logger.info("Optimizando términos de búsqueda")
        
        # Analizar efectividad de términos actuales
        current_terms = self._extract_effective_terms(initial_results)
        
        # Generar términos optimizados
        optimized_terms = self._generate_optimized_terms(current_terms, original_query)
        
        # Determinar estrategia de búsqueda
        search_strategy = self._determine_search_strategy(initial_results)
        
        return {
            "optimized_terms": optimized_terms,
            "strategy": search_strategy,
            "confidence": self._calculate_optimization_confidence(optimized_terms),
            "original_terms": current_terms
        }
    
    def _extract_effective_terms(self, results: Dict) -> List[str]:
        """Extrae términos efectivos de resultados exploratorios"""
        effective_terms = []
        
        for result in results.get("results", []):
            if result.get("relevance", 0) > 0.7:
                term = result.get("term_matched")
                if term and term not in effective_terms:
                    effective_terms.append(term)
        
        return effective_terms
    
    def _generate_optimized_terms(self, current_terms: List[str], original_query: str) -> List[str]:
        """Genera términos optimizados"""
        optimized = current_terms.copy()
        
        # Agregar sinónimos para términos efectivos
        for term in current_terms:
            if term in self.synonyms_db:
                optimized.extend(self.synonyms_db[term][:2])  # Máximo 2 sinónimos por término
        
        # Agregar términos específicos basados en la consulta original
        if "marca" in original_query.lower():
            optimized.extend(["registro marcario", "propiedad industrial"])
        
        return list(set(optimized))[:8]  # Limitar a 8 términos optimizados
    
    def _determine_search_strategy(self, results: Dict) -> str:
        """Determina estrategia de búsqueda basada en resultados exploratorios"""
        found_results = results.get("found_results", 0)
        coverage = results.get("coverage_score", 0)
        
        if found_results == 0:
            return "broad"
        elif found_results > 10 and coverage > 0.8:
            return "narrow"
        else:
            return "standard"
    
    def _calculate_optimization_confidence(self, optimized_terms: List[str]) -> float:
        """Calcula confianza en la optimización"""
        base_confidence = 0.6
        
        # Aumentar confianza por diversidad de términos
        if len(optimized_terms) >= 5:
            base_confidence += 0.2
        
        # Aumentar confianza por presencia de sinónimos
        synonym_count = sum(1 for term in optimized_terms if any(term in syns for syns in self.synonyms_db.values()))
        if synonym_count > 0:
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)

class AgenteBusquedaDefinitiva(BaseAgent):
    """
    Agente de Búsqueda Definitiva - Ejecuta búsquedas precisas y específicas
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("busqueda_definitiva", message_bus)
        self.capabilities = ["precise_search", "targeted_extraction", "result_validation"]
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta búsqueda definitiva con términos optimizados"""
        refined_terms = task_data.get("refined_terms", [])
        search_strategy = task_data.get("search_strategy", "standard")
        
        logger.info(f"Búsqueda definitiva con estrategia {search_strategy}")
        
        # Ejecutar búsqueda definitiva
        results = self._execute_definitive_search(refined_terms, search_strategy)
        
        return {
            "final_results": results,
            "total_found": len(results),
            "search_strategy_used": search_strategy,
            "precision_score": self._calculate_precision(results)
        }
    
    def _execute_definitive_search(self, terms: List[str], strategy: str) -> List[Dict]:
        """Ejecuta búsqueda definitiva"""
        # En implementación real, aquí iría la lógica de scraping específica
        results = []
        
        # Simular resultados basados en estrategia
        if strategy == "narrow":
            # Búsqueda específica - pocos resultados pero muy relevantes
            results = [
                {
                    "id": "def_001",
                    "title": "MARCAS. LA SOLICITUD DE DECLARACIÓN ADMINISTRATIVA DE CADUCIDAD RELATIVA",
                    "content": "Jurisprudencia específica sobre caducidad de marcas en vía reconvencional",
                    "relevance": 0.95,
                    "source": "SCJN",
                    "registro": "2023366",
                    "epoca": "11a. Época"
                }
            ]
        elif strategy == "broad":
            # Búsqueda amplia - más resultados con variada relevancia
            for i in range(5):
                results.append({
                    "id": f"def_{i:03d}",
                    "title": f"Jurisprudencia relacionada {i+1}",
                    "content": f"Contenido de jurisprudencia {i+1}",
                    "relevance": 0.6 + (i * 0.05),
                    "source": "SCJN"
                })
        else:  # standard
            # Búsqueda estándar - balance entre cantidad y relevancia
            for i in range(3):
                results.append({
                    "id": f"def_{i:03d}",
                    "title": f"Jurisprudencia estándar {i+1}",
                    "content": f"Contenido estándar {i+1}",
                    "relevance": 0.75 + (i * 0.05),
                    "source": "SCJN"
                })
        
        return results
    
    def _calculate_precision(self, results: List[Dict]) -> float:
        """Calcula precisión de los resultados"""
        if not results:
            return 0.0
        
        high_relevance_count = sum(1 for r in results if r.get("relevance", 0) > 0.8)
        return high_relevance_count / len(results)

class AgenteProcesamientoResultados(BaseAgent):
    """
    Agente de Procesamiento de Resultados - Analiza, filtra y estructura resultados finales
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("procesamiento_resultados", message_bus)
        self.capabilities = ["result_analysis", "ranking", "formatting", "summarization"]
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa y estructura resultados finales"""
        raw_results = task_data.get("raw_results", {})
        original_query = task_data.get("original_query", "")
        
        logger.info("Procesando resultados finales")
        
        final_results = raw_results.get("final_results", [])
        
        # Procesar y estructurar resultados
        processed_results = self._process_and_rank_results(final_results, original_query)
        summary = self._generate_summary(processed_results, original_query)
        
        return {
            "processed_results": processed_results,
            "summary": summary,
            "total_results": len(processed_results),
            "quality_score": self._calculate_quality_score(processed_results),
            "recommendations": self._generate_recommendations(processed_results)
        }
    
    def _process_and_rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Procesa y rankea resultados por relevancia"""
        processed = []
        
        for result in results:
            processed_result = {
                "id": result.get("id"),
                "title": result.get("title"),
                "summary": result.get("content", "")[:200] + "...",
                "relevance_score": result.get("relevance", 0),
                "source": result.get("source"),
                "metadata": {
                    "registro": result.get("registro"),
                    "epoca": result.get("epoca"),
                    "processed_at": datetime.now().isoformat()
                }
            }
            processed.append(processed_result)
        
        # Ordenar por relevancia
        processed.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return processed
    
    def _generate_summary(self, results: List[Dict], query: str) -> str:
        """Genera resumen de resultados"""
        if not results:
            return "No se encontraron jurisprudencias relevantes para la consulta."
        
        best_result = results[0]
        total_results = len(results)
        avg_relevance = sum(r["relevance_score"] for r in results) / total_results
        
        summary = f"Se encontraron {total_results} jurisprudencias relevantes. "
        summary += f"El resultado más relevante es '{best_result['title']}' "
        summary += f"con una puntuación de relevancia de {best_result['relevance_score']:.2f}. "
        summary += f"La relevancia promedio de todos los resultados es {avg_relevance:.2f}."
        
        return summary
    
    def _calculate_quality_score(self, results: List[Dict]) -> float:
        """Calcula puntuación de calidad general"""
        if not results:
            return 0.0
        
        # Factores de calidad
        avg_relevance = sum(r["relevance_score"] for r in results) / len(results)
        result_count_factor = min(len(results) / 5, 1.0)  # Óptimo: 5 resultados
        
        quality_score = (avg_relevance * 0.7) + (result_count_factor * 0.3)
        return min(quality_score, 1.0)
    
    def _generate_recommendations(self, results: List[Dict]) -> List[str]:
        """Genera recomendaciones basadas en resultados"""
        recommendations = []
        
        if not results:
            recommendations.append("Intente con términos de búsqueda más generales")
            recommendations.append("Verifique la ortografía de los términos jurídicos")
        elif len(results) == 1:
            recommendations.append("Resultado muy específico encontrado")
            recommendations.append("Considere buscar jurisprudencias relacionadas")
        elif len(results) > 10:
            recommendations.append("Muchos resultados encontrados")
            recommendations.append("Considere refinar la búsqueda con términos más específicos")
        else:
            recommendations.append("Resultados balanceados encontrados")
            recommendations.append("Revise los resultados por orden de relevancia")
        
        return recommendations

class AgenteProcesamiento(BaseAgent):
    """
    Agente de Procesamiento - Maneja procesamiento general de búsquedas
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("procesamiento_busqueda", message_bus)
        self.capabilities = ["data_processing", "search_coordination", "result_integration"]
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa tareas de coordinación de búsqueda"""
        task_type = task_data.get("task_type", "general")
        
        logger.info(f"Procesando tarea de tipo: {task_type}")
        
        if task_type == "integration":
            return self._integrate_search_results(task_data)
        elif task_type == "validation":
            return self._validate_search_results(task_data)
        else:
            return self._general_processing(task_data)
    
    def _integrate_search_results(self, task_data: Dict) -> Dict:
        """Integra resultados de múltiples fuentes"""
        return {
            "integrated_results": [],
            "integration_status": "completed",
            "sources_integrated": 0
        }
    
    def _validate_search_results(self, task_data: Dict) -> Dict:
        """Valida calidad de resultados de búsqueda"""
        return {
            "validation_status": "passed",
            "quality_metrics": {},
            "recommendations": []
        }
    
    def _general_processing(self, task_data: Dict) -> Dict:
        """Procesamiento general"""
        return {
            "processing_status": "completed",
            "processed_data": task_data
        }

