"""
Core — Task Registry & Sub-Agent Lifecycle Management
GAACA v2.0 (Inspired by claw-code TaskRegistry)

Manages the lifecycle, packets, messages, and execution states
for autonomous sub-agent and background tasks.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

from agent_v2.capabilities.base import (
    ImplementationSpec, CostModel, Observation, ExecContext
)
from agent_v2.capabilities.registry import CapabilityRegistry


class TaskStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class TaskMessage:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class TaskPacket:
    task_id: str
    prompt: str
    description: str = ""
    status: TaskStatus = TaskStatus.CREATED
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    messages: List[TaskMessage] = field(default_factory=list)
    output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages_count": len(self.messages),
            "output_length": len(self.output),
            "metadata": self.metadata,
        }


class TaskRegistry:
    """
    Thread-safe in-memory task registry for sub-agent task lifecycle management.
    """
    def __init__(self):
        self._tasks: Dict[str, TaskPacket] = {}
        self._lock = Lock()

    def create_task(self, prompt: str, description: str = "", metadata: Optional[Dict[str, Any]] = None) -> TaskPacket:
        with self._lock:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            task = TaskPacket(
                task_id=task_id,
                prompt=prompt,
                description=description,
                status=TaskStatus.CREATED,
                metadata=metadata or {},
            )
            self._tasks[task_id] = task
            return task

    def get_task(self, task_id: str) -> Optional[TaskPacket]:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskPacket]:
        with self._lock:
            if status is None:
                return list(self._tasks.values())
            return [t for t in self._tasks.values() if t.status == status]

    def set_status(self, task_id: str, status: TaskStatus) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.status = status
            task.updated_at = time.time()
            return True

    def append_output(self, task_id: str, chunk: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.output += chunk
            task.updated_at = time.time()
            return True

    def add_message(self, task_id: str, role: str, content: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.messages.append(TaskMessage(role=role, content=content))
            task.updated_at = time.time()
            return True

    def stop_task(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.STOPPED):
                return False
            task.status = TaskStatus.STOPPED
            task.updated_at = time.time()
            return True

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            counts = {s.value: 0 for s in TaskStatus}
            for t in self._tasks.values():
                counts[t.status.value] += 1
            return {
                "total_tasks": len(self._tasks),
                "by_status": counts,
            }


# Global default registry instance
GLOBAL_TASK_REGISTRY = TaskRegistry()


# ---------------------------------------------------------------------------
# Capability Handlers
# ---------------------------------------------------------------------------

def handle_create_task(params: Dict[str, Any], context: ExecContext) -> Observation:
    prompt = params.get("prompt", "").strip()
    if not prompt:
        return Observation(ok=False, output=None, error="Missing required parameter 'prompt'.")

    description = params.get("description", "")
    task = GLOBAL_TASK_REGISTRY.create_task(prompt=prompt, description=description)
    return Observation(
        ok=True,
        output=f"Created task {task.task_id} with status '{task.status.value}'.",
        metadata=task.to_dict(),
    )


def handle_list_tasks(params: Dict[str, Any], context: ExecContext) -> Observation:
    status_filter = params.get("status")
    status = TaskStatus(status_filter) if status_filter in [s.value for s in TaskStatus] else None
    tasks = GLOBAL_TASK_REGISTRY.list_tasks(status=status)
    return Observation(
        ok=True,
        output={"total": len(tasks), "tasks": [t.to_dict() for t in tasks]},
        metadata={"count": len(tasks)},
    )


def handle_stop_task(params: Dict[str, Any], context: ExecContext) -> Observation:
    task_id = params.get("task_id", "").strip()
    if not task_id:
        return Observation(ok=False, output=None, error="Missing required parameter 'task_id'.")

    success = GLOBAL_TASK_REGISTRY.stop_task(task_id)
    if success:
        return Observation(ok=True, output=f"Task {task_id} successfully stopped.", metadata={"task_id": task_id})
    return Observation(ok=False, output=None, error=f"Could not stop task '{task_id}' (not found or already terminal).")


def register_task_capabilities(registry: CapabilityRegistry):
    """Registers task management capabilities into GAACA registry."""
    registry.register_implementation(ImplementationSpec(
        name="create_task",
        description="Creates a tracked sub-agent or background task packet",
        input_schema={"type": "object", "properties": {"prompt": {"type": "string"}, "description": {"type": "string"}}, "required": ["prompt"]},
        output_schema={"type": "string"},
        autonomy_action="create_task",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.1),
        handler=handle_create_task,
    ))

    registry.register_implementation(ImplementationSpec(
        name="list_tasks",
        description="Lists tracked sub-agent and background tasks in the TaskRegistry",
        input_schema={"type": "object", "properties": {"status": {"type": "string"}}},
        output_schema={"type": "object"},
        autonomy_action="list_tasks",
        risk="NONE",
        cost=CostModel(estimated_seconds=0.1),
        handler=handle_list_tasks,
    ))

    registry.register_implementation(ImplementationSpec(
        name="stop_task",
        description="Stops an active sub-agent or background task",
        input_schema={"type": "object", "properties": {"task_id": {"type": "string"}}, "required": ["task_id"]},
        output_schema={"type": "string"},
        autonomy_action="stop_task",
        risk="LOW",
        cost=CostModel(estimated_seconds=0.1),
        handler=handle_stop_task,
    ))
