"""
Base Capability Specification for TCS Quarkus Factory.
Defines extension coordinates, multi-profile configurations, skeleton templates, and test harnesses.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MavenCoordinate(BaseModel):
    group_id: str
    artifact_id: str
    version: Optional[str] = None  # None means version managed by Quarkus BOM
    scope: Optional[str] = None    # "test", "compile", "provided"


class CapabilityDescriptor(BaseModel):
    name: str
    description: str
    category: str  # "inbound", "outbound", "cross_cutting"
    extensions: List[MavenCoordinate] = Field(default_factory=list)
    dev_properties: Dict[str, str] = Field(default_factory=dict)
    test_properties: Dict[str, str] = Field(default_factory=dict)
    prod_properties: Dict[str, str] = Field(default_factory=dict)
    required_test_extensions: List[MavenCoordinate] = Field(default_factory=list)


class BaseCapability(ABC):

    @abstractmethod
    def get_descriptor(self) -> CapabilityDescriptor:
        pass

    @abstractmethod
    def generate_skeleton_files(self, pkg_prefix: str, spec: Any) -> Dict[str, str]:
        """Generate architectural skeleton interfaces, adapters, and configuration."""
        pass

    @abstractmethod
    def generate_acceptance_test_harness(self, pkg_prefix: str, spec: Any) -> Dict[str, str]:
        """Generate immutable test harness files (RestAssured, Testcontainers, in-memory stubs)."""
        pass

