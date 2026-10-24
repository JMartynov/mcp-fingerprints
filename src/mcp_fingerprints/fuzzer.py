from enum import Enum
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Union, Tuple
import random
import json
import subprocess
import time
import queue
import threading
import os

from mcp_fingerprints.runtime_sandbox import sanitize_environment, enqueue_output, RuntimeSandbox

class PayloadCategory(str, Enum):
    type_confusion = "type_confusion"
    int64_overflow = "int64_overflow"
    deep_nesting = "deep_nesting"
    empty_or_null_required = "empty_or_null_required"
    sql_injection = "sql_injection"
    path_traversal = "path_traversal"
    command_injection = "command_injection"
    control_bytes = "control_bytes"

class FuzzOutcome(str, Enum):
    clean_error = "clean_error"
    handled_result = "handled_result"
    protocol_violation = "protocol_violation"
    timeout_hang = "timeout_hang"
    process_crash = "process_crash"

@dataclass
class FuzzCaseResult:
    tool_name: str
    category: PayloadCategory
    payload: Dict[str, Any]
    outcome: FuzzOutcome
    duration_ms: float
    error_code: Optional[int] = None
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "category": self.category.value,
            "payload": self.payload,
            "outcome": self.outcome.value,
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
            "detail": self.detail,
        }

@dataclass
class FuzzReport:
    target_command: List[str]
    total_cases: int
    clean_errors: int
    handled_results: int
    protocol_violations: int
    timeouts: int
    crashes: int
    results: List[FuzzCaseResult]
    passport_name: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.protocol_violations == 0 and self.timeouts == 0 and self.crashes == 0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_command": self.target_command,
            "passport_name": self.passport_name,
            "total_cases": self.total_cases,
            "clean_errors": self.clean_errors,
            "handled_results": self.handled_results,
            "protocol_violations": self.protocol_violations,
            "timeouts": self.timeouts,
            "crashes": self.crashes,
            "passed": self.passed,
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

class PayloadMutator:
    @staticmethod
    def generate_payloads(tool_name: str, input_schema: Dict[str, Any], max_cases: Optional[int] = None) -> List[Tuple[PayloadCategory, Dict[str, Any]]]:
        rng = random.Random(f"{tool_name}_mutator_seed")
        cases: List[Tuple[PayloadCategory, Dict[str, Any]]] = []
        
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        def base_payload():
            payload = {}
            for p, p_schema in properties.items():
                t = p_schema.get("type", "string")
                if t == "string": payload[p] = "test_string"
                elif t in ("integer", "number"): payload[p] = 42
                elif t == "boolean": payload[p] = True
                elif t == "array": payload[p] = []
                elif t == "object": payload[p] = {}
                else: payload[p] = "test"
            return payload

        # 1. type_confusion
        for p, p_schema in properties.items():
            payload = base_payload()
            t = p_schema.get("type", "string")
            if t == "string": payload[p] = 123
            elif t in ("integer", "number"): payload[p] = "not_a_number"
            elif t == "boolean": payload[p] = {"is": "object"}
            elif t == "array": payload[p] = 123
            elif t == "object": payload[p] = []
            cases.append((PayloadCategory.type_confusion, payload))
        if not properties:
            cases.append((PayloadCategory.type_confusion, {"unexpected": True}))
            
        # 2. int64_overflow
        for p, p_schema in properties.items():
            t = p_schema.get("type", "string")
            if t in ("integer", "number"):
                for val in [2**63 - 1, -2**63, 2**128, 0, -1, 1e308, -1e308]:
                    payload = base_payload()
                    payload[p] = val
                    cases.append((PayloadCategory.int64_overflow, payload))
        if not any(p_schema.get("type") in ("integer", "number") for p_schema in properties.values()):
            cases.append((PayloadCategory.int64_overflow, {"__fuzz_num": 2**128}))

        # 3. deep_nesting
        deep_obj = {}
        curr = deep_obj
        for _ in range(64):
            curr["nested"] = {}
            curr = curr["nested"]
        curr["val"] = 1
        
        payload_deep = base_payload()
        if properties:
            p = list(properties.keys())[0]
            payload_deep[p] = deep_obj
        else:
            payload_deep["__deep"] = deep_obj
        cases.append((PayloadCategory.deep_nesting, payload_deep))

        # 4. empty_or_null_required
        if required:
            for r in required:
                payload = base_payload()
                val = rng.choice([None, "", {}])
                payload[r] = val
                cases.append((PayloadCategory.empty_or_null_required, payload))
                
                payload_omit = base_payload()
                if r in payload_omit:
                    del payload_omit[r]
                cases.append((PayloadCategory.empty_or_null_required, payload_omit))
        else:
            cases.append((PayloadCategory.empty_or_null_required, {}))

        # 5. sql_injection
        sql_payloads = ["test_quote' --", "sample; SELECT 1", "'; DROP TABLE users; --", "admin' OR 1=1--"]
        for sql in sql_payloads:
            payload = base_payload()
            for p, p_schema in properties.items():
                if p_schema.get("type", "string") == "string":
                    payload[p] = sql
            if not properties:
                payload["__sql"] = sql
            cases.append((PayloadCategory.sql_injection, payload))
            
        # 6. path_traversal
        path_payloads = ["../relative/sample.txt", "..\\\\relative\\\\config.ini", "../../../../../etc/passwd"]
        for pt in path_payloads:
            payload = base_payload()
            for p, p_schema in properties.items():
                if p_schema.get("type", "string") == "string":
                    payload[p] = pt
            if not properties:
                payload["__path"] = pt
            cases.append((PayloadCategory.path_traversal, payload))

        # 7. command_injection
        cmd_payloads = ["sample; echo test", "test | cat", "$(whoami)", "`id`"]
        for cmd in cmd_payloads:
            payload = base_payload()
            for p, p_schema in properties.items():
                if p_schema.get("type", "string") == "string":
                    payload[p] = cmd
            if not properties:
                payload["__cmd"] = cmd
            cases.append((PayloadCategory.command_injection, payload))

        # 8. control_bytes
        ctrl_payloads = ["test\\x00null\\x07\\x1b[31m", "\\x00\\x01\\x02", "hello\\x0a\\x0d\\x0bworld"]
        for ctrl in ctrl_payloads:
            payload = base_payload()
            for p, p_schema in properties.items():
                if p_schema.get("type", "string") == "string":
                    payload[p] = ctrl
            if not properties:
                payload["__ctrl"] = ctrl
            cases.append((PayloadCategory.control_bytes, payload))
            
        categories_seen = {c: [] for c in PayloadCategory}
        for cat, pyld in cases:
            categories_seen[cat].append((cat, pyld))
            
        final_cases = []
        while any(categories_seen.values()):
            for cat in PayloadCategory:
                if categories_seen[cat]:
                    final_cases.append(categories_seen[cat].pop(0))
        
        if max_cases is not None:
            if len(final_cases) > max_cases:
                if max_cases >= 8:
                    res = final_cases[:8]
                    res.extend(final_cases[8:max_cases])
                    final_cases = res
                else:
                    final_cases = final_cases[:max_cases]
            elif len(final_cases) < max_cases:
                idx = 0
                while len(final_cases) < max_cases:
                    final_cases.append(final_cases[idx % len(cases)])
                    idx += 1
                    
        return final_cases

class SchemaDrivenFuzzer:
    def __init__(
        self,
        target_command: List[str],
        passport: Optional[Union[str, Dict[str, Any]]] = None,
        schemas: Optional[List[Dict[str, Any]]] = None,
        iterations: int = 10,
        timeout: float = 5.0
    ):
        self.target_command = target_command
        self.passport = passport
        self.schemas = schemas
        self.iterations = iterations
        self.timeout = timeout
        
        self.process: Optional[subprocess.Popen] = None
        self.q = queue.Queue()
        self.t: Optional[threading.Thread] = None
        self.msg_id = 1
        
    def _start_process(self) -> bool:
        self._stop_process()
        
        self.sandbox = RuntimeSandbox(self.target_command)
        self.process = self.sandbox.start()
            
        if self.process is None or self.process.stdin is None or self.process.stdout is None:
            self._stop_process()
            return False
            
        self.q = queue.Queue()
        self.t = threading.Thread(target=enqueue_output, args=(self.process.stdout, self.q))
        self.t.daemon = True
        self.t.start()
        
        return self._handshake()
        
    def _stop_process(self):
        if hasattr(self, 'sandbox') and self.sandbox:
            self.sandbox.stop()
            self.sandbox = None
            self.process = None
            
    def _send(self, req: dict) -> None:
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(json.dumps(req) + "\n")
                self.process.stdin.flush()
            except Exception:
                pass
            
    def _recv(self, timeout: float) -> Optional[dict]:
        start = time.time()
        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                return None
            try:
                line = self.q.get(timeout=min(0.1, max(0, timeout - elapsed)))
            except queue.Empty:
                if self.process and self.process.poll() is not None:
                    return None
                continue
            
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                return {"_MALFORMED": True, "raw": line}

    def _handshake(self) -> bool:
        self.msg_id = 1
        req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "McpFingerprintsFuzzer", "version": "1.0"},
            }
        }
        self._send(req)
        
        start = time.time()
        initialized = False
        while True:
            elapsed = time.time() - start
            if elapsed > self.timeout:
                return False
            resp = self._recv(min(0.1, max(0, self.timeout - elapsed)))
            if not resp:
                if self.process and self.process.poll() is not None:
                    return False
                continue
            if resp.get("_MALFORMED"):
                return False
            if resp.get("id") == self.msg_id and "result" in resp:
                initialized = True
                break
                
        if not initialized:
            return False
            
        self._send({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })
        self.msg_id += 1
        return True
        
    def _fetch_schemas(self) -> List[Dict[str, Any]]:
        if self.schemas:
            return self.schemas
            
        if self.passport:
            if isinstance(self.passport, dict) and "tools" in self.passport:
                return self.passport["tools"]

            if isinstance(self.passport, str) and os.path.exists(self.passport):
                try:
                    with open(self.passport, "r") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        if "tools" in data:
                            return data["tools"]
                except Exception:
                    pass
                    
        self.msg_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "tools/list",
            "params": {}
        }
        self._send(req)
        start = time.time()
        tools = []
        while True:
            elapsed = time.time() - start
            if elapsed > self.timeout:
                break
            resp = self._recv(min(0.1, max(0, self.timeout - elapsed)))
            if not resp:
                if self.process and self.process.poll() is not None:
                    break
                continue
            if resp.get("_MALFORMED"):
                break
            if resp.get("id") == self.msg_id and "result" in resp:
                res = resp["result"]
                if "tools" in res and isinstance(res["tools"], list):
                    for t in res["tools"]:
                        if "name" in t and "inputSchema" in t:
                            tools.append({
                                "name": t["name"],
                                "inputSchema": t["inputSchema"]
                            })
                break
        return tools
        
    def fuzz(self) -> FuzzReport:
        if not self._start_process():
            return FuzzReport(
                target_command=self.target_command,
                passport_name=self.passport if isinstance(self.passport, str) else None,
                total_cases=0,
                clean_errors=0,
                handled_results=0,
                protocol_violations=1,
                timeouts=0,
                crashes=1,
                results=[]
            )
            
        schemas = self._fetch_schemas()
        results: List[FuzzCaseResult] = []
        
        test_cases = []
        for t in schemas:
            t_name = t.get("name", "unknown")
            t_schema = t.get("inputSchema", {})
            cases = PayloadMutator.generate_payloads(t_name, t_schema, self.iterations)
            for cat, payload in cases:
                test_cases.append((t_name, cat, payload))
                
        clean_errors = 0
        handled_results = 0
        protocol_violations = 0
        timeouts = 0
        crashes = 0
        
        for t_name, cat, payload in test_cases:
            if self.process is None or self.process.poll() is not None:
                if not self._start_process():
                    res = FuzzCaseResult(
                        tool_name=t_name,
                        category=cat,
                        payload=payload,
                        outcome=FuzzOutcome.process_crash,
                        duration_ms=0,
                        detail="Failed to restart process"
                    )
                    results.append(res)
                    crashes += 1
                    continue
                    
            self.msg_id += 1
            req_id = self.msg_id
            req = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": "tools/call",
                "params": {
                    "name": t_name,
                    "arguments": payload
                }
            }
            
            start = time.time()
            self._send(req)
            
            outcome: Optional[FuzzOutcome] = None
            err_code = None
            detail = ""
            
            while True:
                elapsed = time.time() - start
                if elapsed > self.timeout:
                    outcome = FuzzOutcome.timeout_hang
                    detail = "Timed out waiting for response"
                    timeouts += 1
                    self._stop_process()
                    break
                    
                resp = self._recv(min(0.1, max(0, self.timeout - elapsed)))
                if not resp:
                    if self.process and self.process.poll() is not None:
                        outcome = FuzzOutcome.process_crash
                        detail = f"Process exited with code {self.process.poll()}"
                        crashes += 1
                        break
                    continue
                    
                if resp.get("_MALFORMED"):
                    outcome = FuzzOutcome.protocol_violation
                    detail = f"Malformed JSON: {resp.get('raw', '')[:50]}"
                    protocol_violations += 1
                    self._stop_process()
                    break
                    
                if resp.get("jsonrpc") != "2.0":
                    outcome = FuzzOutcome.protocol_violation
                    detail = "Missing or invalid jsonrpc version"
                    protocol_violations += 1
                    self._stop_process()
                    break
                    
                if resp.get("id") == req_id:
                    if "error" in resp:
                        err = resp["error"]
                        if isinstance(err, dict) and "code" in err:
                            outcome = FuzzOutcome.clean_error
                            err_code = err["code"]
                            detail = str(err.get("message", ""))
                            clean_errors += 1
                        else:
                            outcome = FuzzOutcome.protocol_violation
                            detail = "Malformed error object"
                            protocol_violations += 1
                    elif "result" in resp:
                        outcome = FuzzOutcome.handled_result
                        handled_results += 1
                    else:
                        outcome = FuzzOutcome.protocol_violation
                        detail = "Response has neither result nor error"
                        protocol_violations += 1
                    break
                    
            if outcome is None:
                outcome = FuzzOutcome.process_crash
                crashes += 1
                
            dur_ms = (time.time() - start) * 1000.0
            
            res = FuzzCaseResult(
                tool_name=t_name,
                category=cat,
                payload=payload,
                outcome=outcome,
                duration_ms=dur_ms,
                error_code=err_code,
                detail=detail
            )
            results.append(res)
            
        self._stop_process()
        
        return FuzzReport(
            target_command=self.target_command,
            passport_name=self.passport if isinstance(self.passport, str) else None,
            total_cases=len(results),
            clean_errors=clean_errors,
            handled_results=handled_results,
            protocol_violations=protocol_violations,
            timeouts=timeouts,
            crashes=crashes,
            results=results
        )
