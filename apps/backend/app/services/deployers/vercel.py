from __future__ import annotations

import httpx

from app.common.logging import logger
from app.common.settings import settings
from app.services.deployers.base import BaseDeployer, DeploymentResult


class VercelDeployer(BaseDeployer):
    """Vercel deployment provider using the Vercel API."""
    
    VERCEL_API_BASE = "https://api.vercel.com"
    
    def __init__(self) -> None:
        self._log = logger.bind(component="vercel-deployer")
        self._token = settings.vercel_token
        self._org_id = settings.vercel_org_id
        self._project_id = settings.vercel_project_id
    
    @property
    def name(self) -> str:
        return "Vercel"
    
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
    
    def validate_config(self) -> tuple[bool, str]:
        if not self._token:
            return False, "VERCEL_TOKEN is required for Vercel deployments"
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
        Trigger a Vercel deployment.
        
        For Git-connected projects, this triggers a deployment via deploy hooks.
        For manual deployments, you'd need to use the Vercel CLI or upload files.
        """
        is_valid, error = self.validate_config()
        if not is_valid:
            return DeploymentResult(success=False, message=error)
        
        logs: list[str] = []
        
        try:
            # Map environment to Vercel target
            target = "production" if environment in ("production", "prod") else "preview"
            
            logs.append(f"Triggering Vercel deployment for {project_name}")
            logs.append(f"Target: {target}, Version: {version or 'latest'}")
            
            # If we have a project ID, we can trigger deployment via API
            if self._project_id:
                return self._deploy_via_api(project_name, target, version, logs)
            
            # Otherwise, trigger via deploy hook if configured
            if repo_url:
                return self._deploy_via_git(repo_url, target, version, logs)
            
            return DeploymentResult(
                success=False,
                message="No VERCEL_PROJECT_ID or repo_url configured for deployment",
                logs=logs,
            )
            
        except httpx.HTTPError as e:
            self._log.exception("vercel_deploy_failed", error=str(e))
            logs.append(f"HTTP Error: {e}")
            return DeploymentResult(success=False, message=str(e), logs=logs)
        except Exception as e:
            self._log.exception("vercel_deploy_failed", error=str(e))
            logs.append(f"Error: {e}")
            return DeploymentResult(success=False, message=str(e), logs=logs)
    
    def _deploy_via_api(
        self, project_name: str, target: str, version: str | None, logs: list[str]
    ) -> DeploymentResult:
        """Deploy using Vercel API to create a new deployment."""
        
        with httpx.Client(timeout=60.0) as client:
            # Create deployment
            payload = {
                "name": project_name,
                "target": target,
                "projectSettings": {
                    "framework": None,  # Auto-detect
                },
            }
            
            if version:
                payload["gitSource"] = {
                    "ref": version,
                    "type": "github",  # or gitlab, bitbucket
                }
            
            params = {}
            if self._org_id:
                params["teamId"] = self._org_id
            
            logs.append(f"Creating deployment via Vercel API...")
            
            # List recent deployments to get latest or trigger new one
            response = client.get(
                f"{self.VERCEL_API_BASE}/v6/deployments",
                headers=self._headers(),
                params={**params, "projectId": self._project_id, "limit": 1},
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("deployments"):
                latest = data["deployments"][0]
                deployment_url = f"https://{latest.get('url', '')}"
                logs.append(f"Latest deployment: {deployment_url}")
                logs.append(f"State: {latest.get('state', 'unknown')}")
                
                # Trigger redeploy
                redeploy_response = client.post(
                    f"{self.VERCEL_API_BASE}/v13/deployments",
                    headers=self._headers(),
                    params=params,
                    json={
                        "name": project_name,
                        "target": target,
                        "deploymentId": latest["uid"],  # Redeploy from this
                    },
                )
                
                if redeploy_response.status_code in (200, 201):
                    new_deployment = redeploy_response.json()
                    new_url = f"https://{new_deployment.get('url', '')}"
                    logs.append(f"New deployment triggered: {new_url}")
                    
                    return DeploymentResult(
                        success=True,
                        message=f"Deployment triggered successfully",
                        deployment_url=new_url,
                        deployment_id=new_deployment.get("id"),
                        logs=logs,
                        metadata={"state": new_deployment.get("readyState", "BUILDING")},
                    )
            
            logs.append("No existing deployments found. Connect your Git repo to Vercel first.")
            return DeploymentResult(
                success=False,
                message="No deployments found. Please connect your Git repository to Vercel.",
                logs=logs,
            )
    
    def _deploy_via_git(
        self, repo_url: str, target: str, version: str | None, logs: list[str]
    ) -> DeploymentResult:
        """For Git-connected projects, pushing to the repo triggers deployment."""
        logs.append(f"Git-based deployment: Push to your repo to trigger Vercel deployment")
        logs.append(f"Repo: {repo_url}")
        logs.append(f"Vercel will auto-deploy on push to main/master branch")
        
        return DeploymentResult(
            success=True,
            message="Git-connected projects deploy automatically on push. Check Vercel dashboard.",
            logs=logs,
            metadata={"deploy_method": "git_push"},
        )
    
    def get_deployment_status(self, deployment_id: str) -> DeploymentResult:
        """Get status of a Vercel deployment."""
        is_valid, error = self.validate_config()
        if not is_valid:
            return DeploymentResult(success=False, message=error)
        
        try:
            with httpx.Client(timeout=30.0) as client:
                params = {}
                if self._org_id:
                    params["teamId"] = self._org_id
                
                response = client.get(
                    f"{self.VERCEL_API_BASE}/v13/deployments/{deployment_id}",
                    headers=self._headers(),
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                
                state = data.get("readyState", "UNKNOWN")
                url = f"https://{data.get('url', '')}"
                
                return DeploymentResult(
                    success=state in ("READY", "QUEUED", "BUILDING"),
                    message=f"Deployment state: {state}",
                    deployment_url=url,
                    deployment_id=deployment_id,
                    metadata={"state": state, "created": data.get("created")},
                )
        except Exception as e:
            return DeploymentResult(success=False, message=str(e))
    
    def rollback(self, deployment_id: str) -> DeploymentResult:
        """Rollback by promoting a previous deployment."""
        is_valid, error = self.validate_config()
        if not is_valid:
            return DeploymentResult(success=False, message=error)
        
        try:
            with httpx.Client(timeout=60.0) as client:
                params = {}
                if self._org_id:
                    params["teamId"] = self._org_id
                
                # Promote the specified deployment to production
                response = client.post(
                    f"{self.VERCEL_API_BASE}/v10/projects/{self._project_id}/promote/{deployment_id}",
                    headers=self._headers(),
                    params=params,
                )
                
                if response.status_code in (200, 201):
                    return DeploymentResult(
                        success=True,
                        message=f"Rolled back to deployment {deployment_id}",
                        deployment_id=deployment_id,
                    )
                
                return DeploymentResult(
                    success=False,
                    message=f"Rollback failed: {response.text}",
                )
        except Exception as e:
            return DeploymentResult(success=False, message=str(e))
