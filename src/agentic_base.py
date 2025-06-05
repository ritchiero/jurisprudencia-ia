"""
Sistema Agéntico Base para Jurisprudencias SCJN
Implementación de la arquitectura multi-agente
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import threading
import queue
import time

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Tipos de mensajes entre agentes"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    COORDINATION = "coordination"

class AgentStatus(Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class Message:
    """Estructura de mensaje entre agentes"""
    id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type.value,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id
        }

@dataclass
class TaskResult:
    """Resultado de una tarea ejecutada por un agente"""
    task_id: str
    agent_id: str
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

class MessageBus:
    """Bus de mensajes para comunicación entre agentes"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
    
    def start(self):
        """Inicia el bus de mensajes"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_messages)
        self.worker_thread.start()
        logger.info("MessageBus iniciado")
    
    def stop(self):
        """Detiene el bus de mensajes"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("MessageBus detenido")
    
    def subscribe(self, agent_id: str, callback: Callable):
        """Suscribe un agente al bus de mensajes"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
        logger.info(f"Agente {agent_id} suscrito al MessageBus")
    
    def publish(self, message: Message):
        """Publica un mensaje en el bus"""
        self.message_queue.put(message)
    
    def _process_messages(self):
        """Procesa mensajes en el hilo de trabajo"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=1)
                self._deliver_message(message)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando mensaje: {e}")
    
    def _deliver_message(self, message: Message):
        """Entrega un mensaje al agente destinatario"""
        if message.receiver_id in self.subscribers:
            for callback in self.subscribers[message.receiver_id]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error entregando mensaje a {message.receiver_id}: {e}")

class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.status = AgentStatus.IDLE
        self.capabilities: List[str] = []
        self.task_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        
        # Suscribirse al bus de mensajes
        self.message_bus.subscribe(self.agent_id, self.handle_message)
        
        logger.info(f"Agente {self.agent_id} inicializado")
    
    def start(self):
        """Inicia el agente"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_tasks)
        self.worker_thread.start()
        self.status = AgentStatus.IDLE
        logger.info(f"Agente {self.agent_id} iniciado")
    
    def stop(self):
        """Detiene el agente"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        self.status = AgentStatus.OFFLINE
        logger.info(f"Agente {self.agent_id} detenido")
    
    def handle_message(self, message: Message):
        """Maneja mensajes recibidos"""
        logger.info(f"Agente {self.agent_id} recibió mensaje de {message.sender_id}")
        
        if message.message_type == MessageType.TASK_REQUEST:
            self.task_queue.put(message)
        elif message.message_type == MessageType.COORDINATION:
            self.handle_coordination(message)
        elif message.message_type == MessageType.STATUS_UPDATE:
            self.handle_status_update(message)
    
    def send_message(self, receiver_id: str, message_type: MessageType, 
                    payload: Dict[str, Any], correlation_id: Optional[str] = None):
        """Envía un mensaje a otro agente"""
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(),
            correlation_id=correlation_id
        )
        self.message_bus.publish(message)
    
    def _process_tasks(self):
        """Procesa tareas en el hilo de trabajo"""
        while self.running:
            try:
                message = self.task_queue.get(timeout=1)
                self._execute_task(message)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando tarea en {self.agent_id}: {e}")
    
    def _execute_task(self, message: Message):
        """Ejecuta una tarea específica"""
        self.status = AgentStatus.BUSY
        start_time = time.time()
        
        try:
            result = self.process_task(message.payload)
            execution_time = time.time() - start_time
            
            # Enviar respuesta exitosa
            response_payload = {
                'task_id': message.payload.get('task_id'),
                'result': result,
                'execution_time': execution_time,
                'success': True
            }
            
            self.send_message(
                message.sender_id,
                MessageType.TASK_RESPONSE,
                response_payload,
                message.correlation_id
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error ejecutando tarea en {self.agent_id}: {e}")
            
            # Enviar respuesta de error
            error_payload = {
                'task_id': message.payload.get('task_id'),
                'error': str(e),
                'execution_time': execution_time,
                'success': False
            }
            
            self.send_message(
                message.sender_id,
                MessageType.TASK_RESPONSE,
                error_payload,
                message.correlation_id
            )
        
        finally:
            self.status = AgentStatus.IDLE
    
    @abstractmethod
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa una tarea específica - debe ser implementado por cada agente"""
        pass
    
    def handle_coordination(self, message: Message):
        """Maneja mensajes de coordinación - puede ser sobrescrito"""
        pass
    
    def handle_status_update(self, message: Message):
        """Maneja actualizaciones de estado - puede ser sobrescrito"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente"""
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'capabilities': self.capabilities,
            'queue_size': self.task_queue.qsize()
        }

class AgentRegistry:
    """Registro de agentes del sistema"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.capabilities_map: Dict[str, List[str]] = {}
    
    def register_agent(self, agent: BaseAgent):
        """Registra un agente en el sistema"""
        self.agents[agent.agent_id] = agent
        
        # Mapear capacidades
        for capability in agent.capabilities:
            if capability not in self.capabilities_map:
                self.capabilities_map[capability] = []
            self.capabilities_map[capability].append(agent.agent_id)
        
        logger.info(f"Agente {agent.agent_id} registrado con capacidades: {agent.capabilities}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Obtiene un agente por ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Obtiene agentes que tienen una capacidad específica"""
        agent_ids = self.capabilities_map.get(capability, [])
        return [self.agents[agent_id] for agent_id in agent_ids if agent_id in self.agents]
    
    def get_available_agents(self) -> List[BaseAgent]:
        """Obtiene agentes disponibles (no ocupados)"""
        return [agent for agent in self.agents.values() if agent.status == AgentStatus.IDLE]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado del sistema completo"""
        return {
            'total_agents': len(self.agents),
            'agents_status': {agent_id: agent.get_status() for agent_id, agent in self.agents.items()},
            'capabilities': self.capabilities_map
        }

class AgenticSystem:
    """Sistema agéntico principal"""
    
    def __init__(self):
        self.message_bus = MessageBus()
        self.agent_registry = AgentRegistry()
        self.running = False
    
    def start(self):
        """Inicia el sistema agéntico"""
        self.message_bus.start()
        
        # Iniciar todos los agentes registrados
        for agent in self.agent_registry.agents.values():
            agent.start()
        
        self.running = True
        logger.info("Sistema agéntico iniciado")
    
    def stop(self):
        """Detiene el sistema agéntico"""
        # Detener todos los agentes
        for agent in self.agent_registry.agents.values():
            agent.stop()
        
        self.message_bus.stop()
        self.running = False
        logger.info("Sistema agéntico detenido")
    
    def register_agent(self, agent: BaseAgent):
        """Registra un agente en el sistema"""
        self.agent_registry.register_agent(agent)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema"""
        return {
            'system_running': self.running,
            'message_bus_active': self.message_bus.running,
            **self.agent_registry.get_system_status()
        }

# Función de utilidad para crear el sistema base
def create_agentic_system() -> AgenticSystem:
    """Crea e inicializa el sistema agéntico base"""
    system = AgenticSystem()
    logger.info("Sistema agéntico base creado")
    return system

