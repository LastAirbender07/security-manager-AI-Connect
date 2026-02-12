from pocketflow import AsyncNode
import os
import tempfile
import subprocess
import shutil


class VerificationNode(AsyncNode):
    async def prep_async(self, shared):
        return {
            "remediation_plan": shared.get("remediation_plan", []),
            "repo_path": shared.get("repo_path", "."),
            "ecosystem": shared.get("ecosystem", {}),
        }

    async def exec_async(self, prep_res):
        remediation_plan = prep_res["remediation_plan"]
        repo_path = prep_res["repo_path"]
        eco = prep_res["ecosystem"]
        verified_fixes = []

        # DooD fix: temp dirs inside the worker container (/tmp/xxx)
        # are NOT visible when mounting into sibling containers.
        host_work_dir = os.getenv("HOST_WORK_DIR", "")
        
        # Get ecosystem info (set by EcosystemDetectionNode)
        docker_image = eco.get("docker_image", "alpine:latest")
        dep_install_cmd = eco.get("dep_install_cmd", "")
        dep_file_path = eco.get("dep_file_path", "")
        syntax_cmd = eco.get("syntax_cmd", [])
        test_cmd = eco.get("test_cmd", [])
        
        print(f"Verification: Using ecosystem → {eco.get('language', 'unknown')} ({eco.get('ecosystem', 'unknown')})")
        
        for fix in remediation_plan:
            fix_filename = os.path.basename(fix["path"])
            
            # Create temp dir under host-mapped path for DooD compatibility
            if host_work_dir:
                tmp_dir = tempfile.mkdtemp(prefix="verify-", dir="/app")
                mount_path = os.path.join(host_work_dir, os.path.basename(tmp_dir))
            else:
                tmp_dir = tempfile.mkdtemp(prefix="verify-")
                mount_path = tmp_dir
            
            try:
                # 1. Write Fix File
                fix_path = os.path.join(tmp_dir, fix_filename)
                with open(fix_path, "w") as f:
                    f.write(fix["fix_code"])
                
                # 2. Copy dependency file (detected by EcosystemDetectionNode)
                install_prefix = ""
                if dep_file_path and os.path.exists(dep_file_path):
                    dep_basename = os.path.basename(dep_file_path)
                    shutil.copy(dep_file_path, os.path.join(tmp_dir, dep_basename))
                    install_prefix = f"{dep_install_cmd} && " if dep_install_cmd else ""
                
                # 3. Build the run command
                if fix.get("test_code") and test_cmd:
                    test_filename = f"test_{fix_filename}"
                    test_path = os.path.join(tmp_dir, test_filename)
                    with open(test_path, "w") as f:
                        f.write(fix["test_code"])
                    run_cmd = " ".join(test_cmd) + f" /check/{test_filename}"
                    check_type = "Unit Test"
                elif syntax_cmd:
                    run_cmd = " ".join(syntax_cmd) + f" /check/{fix_filename}"
                    check_type = "Syntax Check"
                else:
                    print(f"Verification: No syntax/test cmd for {fix_filename}. Skipping.")
                    fix["verified"] = False
                    fix["error"] = "No verification command available"
                    verified_fixes.append(fix)
                    continue

                # Full command: install deps → run test/check
                full_cmd = f"{install_prefix}{run_cmd}"

                docker_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{mount_path}:/check",
                    "-w", "/check",
                    docker_image,
                    "sh", "-c", full_cmd
                ]
                
                print(f"Verification: Running {check_type} for {fix_filename} ({docker_image})...")
                print(f"Verification: Command: {' '.join(docker_cmd)}")
                
                try:
                    result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        print(f"Verification: ✓ {fix['path']} verified ({check_type}).")
                        fix["verified"] = True
                    else:
                        print(f"Verification: ✗ {fix['path']} failed: {result.stderr or result.stdout}")
                        fix["verified"] = False
                        fix["error"] = result.stderr + "\n" + result.stdout
                except subprocess.TimeoutExpired:
                    print(f"Verification: ✗ {fix['path']} timed out (120s).")
                    fix["verified"] = False
                    fix["error"] = "Verification timed out after 120s"
                except Exception as e:
                    print(f"Verification: ✗ Docker execution failed: {e}")
                    fix["verified"] = False
                    fix["error"] = str(e)
                
                verified_fixes.append(fix)
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            
        return verified_fixes

    async def post_async(self, shared, prep_res, exec_res):
        if not exec_res:
            shared.setdefault("node_logs", []).append({
                "step": "Verification",
                "tokens_input": 0,
                "tokens_output": 0,
                "model_name": None,
                "message": "No fixes to verify"
            })
            return "failed"
        
        verified = sum(1 for f in exec_res if f.get("verified"))
        total = len(exec_res)
        shared["verified_fixes"] = exec_res
        shared.setdefault("node_logs", []).append({
            "step": "Verification",
            "tokens_input": 0,
            "tokens_output": 0,
            "model_name": None,
            "message": f"Verified {verified}/{total} fixes"
        })
        return "success"
