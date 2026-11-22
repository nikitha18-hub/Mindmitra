from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    username: str
    role: str


@dataclass
class Memory:
    id: int
    patient_id: int
    title: str
    description: str
    category: str


@dataclass
class MindmapNode:
    id: int
    patient_id: int
    label: str
    description: str
    category: str


@dataclass
class Reminder:
    id: int
    patient_id: int
    title: str
    time_label: str
    complete: bool