"""
factory_contract.py — Validation mechanisms for jobs (X02 Factory Contract)

Enforces schemas for job inputs/outputs and checks compliance against
expected naming conventions and Definition of Done (DoD).
"""

import os
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("spark.factory_contract")

# Chapter X02 Job Contract specifications
JOB_CONTRACTS = {
    "video_generate": {
        "required_inputs": ["prompt"],
        "required_outputs": ["output_url"],
        "naming_pattern": "{job_id}.mp4"
    },
    "image_generate": {
        "required_inputs": ["prompt"],
        "required_outputs": ["output_url"],
        "naming_pattern": "{job_id}.png"
    },
    "music_generate": {
        "required_inputs": ["prompt"],
        "required_outputs": ["output_url"],
        "naming_pattern": "{job_id}.wav"
    }
}

def validate_inputs(job_type: str, params: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify that the inputs conform to the job contract requirements."""
    if job_type not in JOB_CONTRACTS:
        return True, "No validation contract defined; assuming valid."
    
    contract = JOB_CONTRACTS[job_type]
    for required in contract["required_inputs"]:
        if required not in params or not params[required]:
            return False, f"Missing or empty required input parameter: '{required}'"
            
    return True, "Inputs conform to factory contract schema."

def validate_outputs(job_type: str, job_id: str, output_dir: str) -> Tuple[bool, str]:
    """Verify that the outputs comply with folder schemas, naming conventions, and DoD."""
    if job_type not in JOB_CONTRACTS:
        return True, "No validation contract defined; assuming valid."
        
    contract = JOB_CONTRACTS[job_type]
    expected_filename = contract["naming_pattern"].format(job_id=job_id)
    expected_path = os.path.join(output_dir, expected_filename)
    
    if not os.path.exists(expected_path):
        # Let's search if the file is inside the directory but named differently
        # or check if it's there
        return False, f"Definition of Done (DoD) failed: expected output file '{expected_filename}' not found in {output_dir}."
        
    if os.path.getsize(expected_path) == 0:
        return False, f"Definition of Done (DoD) failed: output file '{expected_filename}' is empty."
        
    return True, f"DoD satisfied. Output file verified: {expected_filename} ({os.path.getsize(expected_path)} bytes)."
