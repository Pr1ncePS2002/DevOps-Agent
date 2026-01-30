from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    message: str
    deployment_url: str | None = None
    deployment_id: str | None = None
    logs: list[str] | None = None
    metadata: dict[str, Any] | None = None


class BaseDeployer(ABC):
    """Abstract base class for deployment providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the deployment provider."""
        pass
    
    @abstractmethod
    def deploy(
        self,
        *,
        project_name: str,
        repo_path: str | None = None,
        repo_url: str | None = None,
        environment: str = "production",
        version: str | None = None,
    ) -> DeploymentResult:
        """
        Deploy the application.
        
        Args:
            project_name: Name of the project
            repo_path: Local path to the repository
            repo_url: Git URL of the repository
            environment: Target environment (production, staging, preview)
            version: Version or git ref to deploy
            
        Returns:
            DeploymentResult with deployment status and details
        """
        pass
    
    @abstractmethod
    def get_deployment_status(self, deployment_id: str) -> DeploymentResult:
        """Get the status of a deployment."""
        pass
    
    @abstractmethod
    def rollback(self, deployment_id: str) -> DeploymentResult:
        """Rollback to a previous deployment."""
        pass
    
    def validate_config(self) -> tuple[bool, str]:
        """
        Validate that the deployer has required configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, ""
