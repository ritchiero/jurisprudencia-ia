"""
Sistema de Comunicación y Coordinación entre Agentes
Implementa el orquestador principal y la lógica de coordinación
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from src.agentic_base import AgenticSystem, MessageType, Message
from src.specialized_agents import (
    AgenteOrquestador, AgenteInterpretacion, AgenteBusquedaExploratoria,
    AgenteTerminosBusqueda, AgenteBusquedaDefinitiva, AgenteProcesamientoResultados,
    AgenteProcesamiento
)

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Estados del flujo de trabajo"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class WorkflowStep:
    """Paso individual en el flujo de trabajo"""
    step_id: str
    agent_id: str
    task_data: Dict[str, Any]
    dependencies: List[str]
    status: WorkflowStatus
    result: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

class WorkflowOrchestrator:
    """
    Orquestador de flujos de trabajo entre agentes
    Maneja la coordinación compleja y el estado del sistema
    """
    
    def __init__(self, agentic_system: AgenticSystem):
        self.system = agentic_system
        self.active_workflows: Dict[str, Dict] = {}
        self.workflow_templates = self._initialize_workflow_templates()
        self.performance_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0
        }
    
    def _initialize_workflow_templates(self) -> Dict[str, List[WorkflowStep]]:
        """Inicializa plantillas de flujos de trabajo"""
        return {
            "jurisprudencia_search": [
                WorkflowStep(
                    step_id="interpretation",
                    agent_id="interpretacion",
                    task_data={},
                    dependencies=[],
                    status=WorkflowStatus.PENDING
                ),
                WorkflowStep(
                    step_id="exploratory_search",
                    agent_id="busqueda_exploratoria",
                    task_data={},
                    dependencies=["interpretation"],
                    status=WorkflowStatus.PENDING
                ),
                WorkflowStep(
                    step_id="term_optimization",
                    agent_id="terminos_busqueda",
                    task_data={},
                    dependencies=["exploratory_search"],
                    status=WorkflowStatus.PENDING
                ),
                WorkflowStep(
                    step_id="definitive_search",
                    agent_id="busqueda_definitiva",
                    task_data={},
                    dependencies=["term_optimization"],
                    status=WorkflowStatus.PENDING
                ),
                WorkflowStep(
                    step_id="result_processing",
                    agent_id="procesamiento_resultados",
                    task_data={},
                    dependencies=["definitive_search"],
                    status=WorkflowStatus.PENDING
                )
            ]
        }
    
    def start_workflow(self, workflow_type: str, initial_data: Dict[str, Any]) -> str:
        """Inicia un nuevo flujo de trabajo"""
        workflow_id = f"workflow_{int(time.time())}_{workflow_type}"
        
        if workflow_type not in self.workflow_templates:
            raise ValueError(f"Tipo de flujo de trabajo desconocido: {workflow_type}")
        
        # Crear copia de la plantilla
        steps = []
        for template_step in self.workflow_templates[workflow_type]:
            step = WorkflowStep(
                step_id=template_step.step_id,
                agent_id=template_step.agent_id,
                task_data=template_step.task_data.copy(),
                dependencies=template_step.dependencies.copy(),
                status=WorkflowStatus.PENDING
            )
            steps.append(step)
        
        # Configurar datos iniciales
        if steps:
            steps[0].task_data.update(initial_data)
        
        workflow = {
            "id": workflow_id,
            "type": workflow_type,
            "steps": {step.step_id: step for step in steps},
            "status": WorkflowStatus.IN_PROGRESS,
            "start_time": datetime.now(),
            "initial_data": initial_data,
            "results": {}
        }
        
        self.active_workflows[workflow_id] = workflow
        self.performance_metrics["total_workflows"] += 1
        
        logger.info(f"Iniciado flujo de trabajo {workflow_id} de tipo {workflow_type}")
        
        # Ejecutar primer paso
        self._execute_next_steps(workflow_id)
        
        return workflow_id
    
    def _execute_next_steps(self, workflow_id: str):
        """Ejecuta los siguientes pasos disponibles en el flujo de trabajo"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return
        
        steps = workflow["steps"]
        
        # Encontrar pasos listos para ejecutar
        ready_steps = []
        for step in steps.values():
            if step.status == WorkflowStatus.PENDING:
                # Verificar si todas las dependencias están completadas
                dependencies_met = all(
                    steps[dep_id].status == WorkflowStatus.COMPLETED
                    for dep_id in step.dependencies
                )
                if dependencies_met:
                    ready_steps.append(step)
        
        # Ejecutar pasos listos
        for step in ready_steps:
            self._execute_step(workflow_id, step)
    
    def _execute_step(self, workflow_id: str, step: WorkflowStep):
        """Ejecuta un paso individual del flujo de trabajo"""
        workflow = self.active_workflows[workflow_id]
        
        # Preparar datos de la tarea
        task_data = step.task_data.copy()
        task_data["workflow_id"] = workflow_id
        task_data["step_id"] = step.step_id
        
        # Agregar resultados de pasos anteriores
        for dep_id in step.dependencies:
            dep_step = workflow["steps"][dep_id]
            if dep_step.result:
                task_data[f"{dep_id}_result"] = dep_step.result
        
        # Marcar paso como en progreso
        step.status = WorkflowStatus.IN_PROGRESS
        step.start_time = datetime.now()
        
        # Obtener agente y enviar tarea
        agent = self.system.agent_registry.get_agent(step.agent_id)
        if agent:
            # Crear mensaje de tarea
            message = Message(
                id=f"task_{workflow_id}_{step.step_id}",
                sender_id="orchestrator",
                receiver_id=step.agent_id,
                message_type=MessageType.TASK_REQUEST,
                payload={
                    "task_id": f"{workflow_id}_{step.step_id}",
                    "workflow_id": workflow_id,
                    "step_id": step.step_id,
                    **task_data
                },
                timestamp=datetime.now(),
                correlation_id=workflow_id
            )
            
            self.system.message_bus.publish(message)
            logger.info(f"Ejecutando paso {step.step_id} en agente {step.agent_id}")
        else:
            logger.error(f"Agente {step.agent_id} no encontrado")
            step.status = WorkflowStatus.FAILED
            step.error_message = f"Agente {step.agent_id} no disponible"
    
    def handle_step_completion(self, workflow_id: str, step_id: str, result: Dict[str, Any], success: bool):
        """Maneja la finalización de un paso del flujo de trabajo"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            logger.warning(f"Flujo de trabajo {workflow_id} no encontrado")
            return
        
        step = workflow["steps"].get(step_id)
        if not step:
            logger.warning(f"Paso {step_id} no encontrado en flujo {workflow_id}")
            return
        
        # Actualizar estado del paso
        step.end_time = datetime.now()
        step.result = result
        
        if success:
            step.status = WorkflowStatus.COMPLETED
            logger.info(f"Paso {step_id} completado exitosamente en flujo {workflow_id}")
        else:
            step.status = WorkflowStatus.FAILED
            step.error_message = result.get("error", "Error desconocido")
            logger.error(f"Paso {step_id} falló en flujo {workflow_id}: {step.error_message}")
        
        # Verificar si el flujo de trabajo está completo
        self._check_workflow_completion(workflow_id)
        
        # Ejecutar siguientes pasos si es posible
        if success:
            self._execute_next_steps(workflow_id)
    
    def _check_workflow_completion(self, workflow_id: str):
        """Verifica si el flujo de trabajo está completo"""
        workflow = self.active_workflows[workflow_id]
        steps = workflow["steps"]
        
        # Verificar si todos los pasos están completos o fallaron
        all_finished = all(
            step.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
            for step in steps.values()
        )
        
        if all_finished:
            # Determinar estado final
            any_failed = any(step.status == WorkflowStatus.FAILED for step in steps.values())
            
            if any_failed:
                workflow["status"] = WorkflowStatus.FAILED
                self.performance_metrics["failed_workflows"] += 1
            else:
                workflow["status"] = WorkflowStatus.COMPLETED
                self.performance_metrics["successful_workflows"] += 1
            
            workflow["end_time"] = datetime.now()
            
            # Calcular tiempo de ejecución
            execution_time = (workflow["end_time"] - workflow["start_time"]).total_seconds()
            
            # Actualizar métricas
            total_successful = self.performance_metrics["successful_workflows"]
            if total_successful > 0:
                current_avg = self.performance_metrics["average_execution_time"]
                new_avg = ((current_avg * (total_successful - 1)) + execution_time) / total_successful
                self.performance_metrics["average_execution_time"] = new_avg
            
            logger.info(f"Flujo de trabajo {workflow_id} finalizado con estado {workflow['status'].value}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado actual de un flujo de trabajo"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            "id": workflow["id"],
            "type": workflow["type"],
            "status": workflow["status"].value,
            "start_time": workflow["start_time"].isoformat(),
            "end_time": workflow.get("end_time").isoformat() if workflow.get("end_time") else None,
            "steps": {
                step_id: {
                    "status": step.status.value,
                    "agent_id": step.agent_id,
                    "start_time": step.start_time.isoformat() if step.start_time else None,
                    "end_time": step.end_time.isoformat() if step.end_time else None,
                    "error_message": step.error_message
                }
                for step_id, step in workflow["steps"].items()
            }
        }
    
    def get_workflow_results(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los resultados de un flujo de trabajo completado"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow or workflow["status"] != WorkflowStatus.COMPLETED:
            return None
        
        # Recopilar resultados de todos los pasos
        results = {}
        for step_id, step in workflow["steps"].items():
            if step.result:
                results[step_id] = step.result
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "results": results,
            "execution_time": (workflow["end_time"] - workflow["start_time"]).total_seconds()
        }
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Limpia flujos de trabajo completados antiguos"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        workflows_to_remove = []
        for workflow_id, workflow in self.active_workflows.items():
            if (workflow["status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED] and
                workflow.get("end_time") and workflow["end_time"] < cutoff_time):
                workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]
        
        if workflows_to_remove:
            logger.info(f"Limpiados {len(workflows_to_remove)} flujos de trabajo antiguos")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento del sistema"""
        return {
            **self.performance_metrics,
            "active_workflows": len(self.active_workflows),
            "success_rate": (
                self.performance_metrics["successful_workflows"] / 
                max(self.performance_metrics["total_workflows"], 1)
            ) * 100
        }

class EnhancedOrchestrator(AgenteOrquestador):
    """
    Orquestador mejorado que utiliza el WorkflowOrchestrator
    """
    
    def __init__(self, message_bus, workflow_orchestrator: WorkflowOrchestrator):
        super().__init__(message_bus)
        self.workflow_orchestrator = workflow_orchestrator
        self.active_sessions = {}
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa consultas utilizando el sistema de flujos de trabajo"""
        user_query = task_data.get("user_query", "")
        session_id = task_data.get("session_id", f"session_{int(time.time())}")
        
        logger.info(f"Orquestador mejorado procesando consulta: {user_query}")
        
        # Iniciar flujo de trabajo
        workflow_id = self.workflow_orchestrator.start_workflow(
            "jurisprudencia_search",
            {
                "user_query": user_query,
                "session_id": session_id
            }
        )
        
        # Registrar sesión
        self.active_sessions[session_id] = {
            "workflow_id": workflow_id,
            "user_query": user_query,
            "start_time": datetime.now()
        }
        
        return {
            "session_id": session_id,
            "workflow_id": workflow_id,
            "status": "initiated",
            "message": "Procesando consulta con sistema agéntico..."
        }
    
    def handle_coordination(self, message):
        """Maneja respuestas de agentes en el contexto de flujos de trabajo"""
        workflow_id = message.correlation_id
        payload = message.payload
        
        # Extraer información del paso
        step_id = payload.get("step_id")
        success = payload.get("success", False)
        result = payload.get("result", {})
        
        if workflow_id and step_id:
            self.workflow_orchestrator.handle_step_completion(
                workflow_id, step_id, result, success
            )
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de una sesión"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        workflow_status = self.workflow_orchestrator.get_workflow_status(session["workflow_id"])
        
        return {
            "session_id": session_id,
            "user_query": session["user_query"],
            "workflow_status": workflow_status,
            "start_time": session["start_time"].isoformat()
        }
    
    def get_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los resultados de una sesión completada"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        workflow_results = self.workflow_orchestrator.get_workflow_results(session["workflow_id"])
        
        if workflow_results:
            return {
                "session_id": session_id,
                "user_query": session["user_query"],
                "results": workflow_results
            }
        
        return None

def create_coordinated_agentic_system() -> tuple[AgenticSystem, WorkflowOrchestrator]:
    """
    Crea el sistema agéntico completo con coordinación avanzada
    """
    # Crear sistema base
    system = AgenticSystem()
    
    # Crear orquestador de flujos de trabajo
    workflow_orchestrator = WorkflowOrchestrator(system)
    
    # Crear y registrar agentes especializados
    agents = [
        AgenteInterpretacion(system.message_bus),
        AgenteBusquedaExploratoria(system.message_bus),
        AgenteTerminosBusqueda(system.message_bus),
        AgenteBusquedaDefinitiva(system.message_bus),
        AgenteProcesamientoResultados(system.message_bus),
        AgenteProcesamiento(system.message_bus)
    ]
    
    # Registrar agentes
    for agent in agents:
        system.register_agent(agent)
    
    # Crear orquestador mejorado
    enhanced_orchestrator = EnhancedOrchestrator(system.message_bus, workflow_orchestrator)
    system.register_agent(enhanced_orchestrator)
    
    logger.info("Sistema agéntico coordinado creado exitosamente")
    
    return system, workflow_orchestrator

