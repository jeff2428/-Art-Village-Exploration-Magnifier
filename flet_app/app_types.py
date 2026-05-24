from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class ToxicityInfo(TypedDict):
    label: str
    detail: str


class InvasiveInfo(TypedDict):
    label: str
    detail: str


class CareInfo(TypedDict, total=False):
    澆水: str
    日照: str
    生命週期: str
    照護難度: str


class CapturedImage(TypedDict):
    src: str
    label: str


class PlantCandidate(TypedDict):
    zh_name: str
    aliases: list[str]
    eng_name: str
    sci_name: str
    emoji: str
    type: str
    desc: str
    confidence: float
    is_low_confidence: bool
    toxicity: ToxicityInfo
    invasive: InvasiveInfo
    care: CareInfo
    metadata_source: str
    metadata_status: str
    alternatives: NotRequired[list[PlantCandidate]]
    needs_confirmation: NotRequired[bool]
    captured_image: NotRequired[CapturedImage]
    organ: NotRequired[str]
    organ_label: NotRequired[str]
    worker_timing: NotRequired[dict[str, Any]]


class AnimalEntry(TypedDict):
    type: str
    emoji: str
    role: str
    desc: str
    portrait: str
    photos: list[str]


class PokedexEntry(TypedDict, total=False):
    zh_name: str
    type: str
    emoji: str
    role: str
    desc: str
    portrait: str
    photos: list[str]
    aliases: list[str]
    eng_name: str
    sci_name: str
    confidence: float
    is_low_confidence: bool
    toxicity: ToxicityInfo
    invasive: InvasiveInfo
    care: CareInfo
    metadata_source: str
    metadata_status: str
    alternatives: list[PlantCandidate]
    captured_image: CapturedImage
    organ: str
    organ_label: str
    worker_timing: dict[str, Any]


class PerenualMetadata(TypedDict, total=False):
    status: str
    source: str
    query: str
    id: int
    common_name: str
    scientific_name: str
    family: str
    description: str
    cycle: str
    watering: str
    sunlight: list[str]
    care_level: str
    poisonous_to_humans: bool | None
    poisonous_to_pets: bool | None
    invasive: bool | None
    detail: str


class WorkerTiming(TypedDict, total=False):
    total_ms: int
    plantnet_ms: int
    perenual_ms: int
    perenual_cache: str


class PlantNetResult(TypedDict, total=False):
    results: list[dict[str, Any]]
    perenual: PerenualMetadata
    timing: WorkerTiming
