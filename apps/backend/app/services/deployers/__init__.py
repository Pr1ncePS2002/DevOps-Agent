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
    """Factory function to get the appropriate deployer."""
    deployers = {
        "vercel": VercelDeployer,
        "render": RenderDeployer,
        "local": LocalDeployer,
    }
    
    deployer_class = deployers.get(provider.lower())
    if deployer_class is None:
        raise ValueError(f"Unknown deploy provider: {provider}. Valid options: {list(deployers.keys())}")
    
    return deployer_class()
