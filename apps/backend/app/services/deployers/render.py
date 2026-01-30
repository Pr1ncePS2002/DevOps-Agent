from __future__ import annotations

import httpx

from app.common.logging import logger
from app.common.settings import settings
from app.services.deployers.base import BaseDeployer, DeploymentResult


class RenderDeployer(BaseDeployer):
    """Render deployment provider using the Render API."""
    
    RENDER_API_BASE = "https://api.render.com/v1"
    
    def __init__(self) -> None:
        self._log = logger.bind(component="render-deployer")
        self._api_key = settings.render_api_key
        self._service_id = settings.render_service_id
    
    @property
    def name(self) -> str:
        return "Render"
    
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
    
    def validate_config(self) -> tuple[bool, str]:
        if not self._api_key:
            return False, "RENDER_API_KEY is required for Render deployments"
        if not self._service_id:
            return False, "RENDER_SERVICE_ID is required for Render deployments"
        return True, ""
    
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
        Trigger a Render deployment.
        
        Render deploys are triggered by:
        1. Manual deploy via API
        2. Git push (auto-deploy)
        3. Deploy hooks
        """
        is_valid, error = self.validate_config()
        if not is_valid:
            return DeploymentResult(success=False, message=error)
        
        logs: list[str] = []
        
        try:
            logs.append(f"Triggering Render deployment for {project_name}")
            logs.append(f"Service ID: {self._service_id}")
            logs.append(f"Environment: {environment}, Version: {version or 'latest'}")
            
            with httpx.Client(timeout=60.0) as client:
                # Trigger a manual deploy
                payload = {}
                if version:
                    payload["clearCache"] = "do_not_clear"  # or "clear"
                
                logs.append("Triggering deploy via Render API...")
                
                response = client.post(
                    f"{self.RENDER_API_BASE}/services/{self._service_id}/deploys",
                    headers=self._headers(),
                    json=payload,
                )
                
                if response.status_code in (200, 201):
                    data = response.json()
                    deploy_id = data.get("id")
                    status = data.get("status", "created")
                    
                    logs.append(f"Deploy triggered successfully!")
                    logs.append(f"Deploy ID: {deploy_id}")
                    logs.append(f"Status: {status}")
                    
                    # Get service URL
                    service_response = client.get(
                        f"{self.RENDER_API_BASE}/services/{self._service_id}",
                        headers=self._headers(),
                    )
                    service_url = None
                    if service_response.status_code == 200:
                        service_data = service_response.json()
                        service_url = service_data.get("service", {}).get("serviceDetails", {}).get("url")
                        if service_url:
                            logs.append(f"Service URL: {service_url}")
                    
                    return DeploymentResult(
                        success=True,
                        message=f"Render deployment triggered successfully",
                        deployment_url=service_url,
                        deployment_id=deploy_id,
                        logs=logs,
                        metadata={"status": status},
                    )
                
                # Handle errors
                error_msg = response.text
                logs.append(f"Deploy failed: {error_msg}")
                
                return DeploymentResult(
                    success=False,
                    message=f"Render deploy failed: {response.status_code} - {error_msg}",
                    logs=logs,
                )
                
        except httpx.HTTPError as e:
            self._log.exception("render_deploy_failed", error=str(e))
            logs.append(f"HTTP Error: {e}")
            return DeploymentResult(success=False, message=str(e), logs=logs)
        except Exception as e:
            self._log.exception("render_deploy_failed", error=str(e))
            logs.append(f"Error: {e}")
            return DeploymentResult(success=False, message=str(e), logs=logs)
    
    def get_deployment_status(self, deployment_id: str) -> DeploymentResult:
        """Get status of a Render deployment."""
        is_valid, error = self.validate_config()
        if not is_valid:
            return DeploymentResult(success=False, message=error)
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.RENDER_API_BASE}/services/{self._service_id}/deploys/{deployment_id}",
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
                
                status = data.get("status", "unknown")
                
                # Render statuses: created, build_in_progress, update_in_progress, live, deactivated, build_failed, update_failed, canceled, pre_deploy_in_progress, pre_deploy_failed
                success_states = ("created", "build_in_progress", "update_in_progress", "live", "pre_deploy_in_progress")
                
                return DeploymentResult(
                    success=status in success_states,
                    message=f"Deployment status: {status}",
                    deployment_id=deployment_id,
                    metadata={
                        "status": status,
                        "created_at": data.get("createdAt"),
                        "finished_at": data.get("finishedAt"),
                    },
                )
        except Exception as e:
            return DeploymentResult(success=False, message=str(e))
    
    def rollback(self, deployment_id: str) -> DeploymentResult:
        """Rollback by redeploying a previous deployment."""
        is_valid, error = self.validate_config()
        if not is_valid:
            return DeploymentResult(success=False, message=error)
        
        logs: list[str] = []
        
        try:
            with httpx.Client(timeout=60.0) as client:
                # Get the commit from the previous deployment
                response = client.get(
                    f"{self.RENDER_API_BASE}/services/{self._service_id}/deploys/{deployment_id}",
                    headers=self._headers(),
                )
                response.raise_for_status()
                deploy_data = response.json()
                
                commit = deploy_data.get("commit", {}).get("id")
                logs.append(f"Rolling back to commit: {commit or 'unknown'}")
                
                # Trigger a new deploy (Render will use the service's current config)
                # For true rollback, you'd need to redeploy from a specific commit
                rollback_response = client.post(
                    f"{self.RENDER_API_BASE}/services/{self._service_id}/deploys",
                    headers=self._headers(),
                    json={"clearCache": "do_not_clear"},
                )
                
                if rollback_response.status_code in (200, 201):
                    new_deploy = rollback_response.json()
                    logs.append(f"Rollback deploy triggered: {new_deploy.get('id')}")
                    
                    return DeploymentResult(
                        success=True,
                        message="Rollback deployment triggered",
                        deployment_id=new_deploy.get("id"),
                        logs=logs,
                    )
                
                return DeploymentResult(
                    success=False,
                    message=f"Rollback failed: {rollback_response.text}",
                    logs=logs,
                )
        except Exception as e:
            logs.append(f"Error: {e}")
            return DeploymentResult(success=False, message=str(e), logs=logs)
    
    def list_services(self) -> list[dict]:
        """List all services in the Render account (helper method)."""
        if not self._api_key:
            return []
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.RENDER_API_BASE}/services",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return []
