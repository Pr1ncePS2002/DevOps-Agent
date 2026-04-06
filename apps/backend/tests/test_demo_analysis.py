import asyncio
from pathlib import Path
from app.services.project_analysis import analyze_project, generate_dockerfile, detect_stack

def test_demo_app_analysis():
    demo_app_path = Path(r"c:\Users\psing\Desktop\DevOps Agent\apps\demo-app")
    
    # Run the analysis
    result = analyze_project(demo_app_path)
    
    # Assertions
    assert result["detected_stack"] == "node", f"Expected stack to be node, got {result['detected_stack']}"
    assert result["dockerfile_generated"] == True, "Expected dockerfile_generated to be True"
    assert result["dockerfile_path"] is not None, "Expected dockerfile_path to be set"
    
    # Delete the generated dockerfile up after test
    dockerfile = Path(result["dockerfile_path"])
    content = dockerfile.read_text()
    
    assert "FROM node:20-alpine AS builder" in content, "Expected multi-stage dockerfile"
    assert "EXPOSE 3000" in content, "Expected EXPOSE 3000"
    
    print("Test passed! Dockerfile successfully generated for demo-app.")
    
if __name__ == "__main__":
    test_demo_app_analysis()
