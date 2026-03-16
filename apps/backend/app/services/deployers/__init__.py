from __future__ import annotations

from app.services.deployers.base import BaseDeployer, DeploymentResult
from app.services.deployers.vercel import VercelDeployer
from app.services.deployers.render import RenderDeployer
from app.services.deployers.local import LocalDeployer

__all__ = [
    "BaseDeployer",
    "DeploymentResult",
    "VercelDeployer",
    "RenderDeployer",
    "LocalDeployer",
    "get_deployer",
]


def get_deployer(provider: str) -> BaseDeployer:
    """Factory function to get the appropriate deployer.
    Note: 'docker' is handled directly by the Orchestrator via the Docker adapter,
    not through a deployer class. Only cloud/local providers go through here.
    """
    deployers = {
        "vercel": VercelDeployer,
        "render": RenderDeployer,
        "local": LocalDeployer,
    }
    
    provider_lower = provider.lower()
    if provider_lower == "docker":
        raise ValueError(
            "Docker deployments are handled by the Orchestrator directly via the Docker adapter. "
            "Use get_deployer() only for cloud providers (vercel, render, local)."
        )
    
    deployer_class = deployers.get(provider_lower)
    if deployer_class is None:
        raise ValueError(f"Unknown deploy provider: {provider}. Valid options: {list(deployers.keys())}")
    
    return deployer_class()
