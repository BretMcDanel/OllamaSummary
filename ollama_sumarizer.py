"""
OllamaGhidra - Ghidra extension for AI-powered function summarization
Copyright (c) 2023 [Your Name]
Licensed under the BSD 3-Clause License
"""

import requests
import time
from ghidra.app.decompiler import Decompiler
from ghidra.app.decompiler import DecompiledFunction
from ghidra.util.task import TaskMonitor
from ghidra.program.model.listing import Function

class OllamaSummarizer:
    """Summarizes functions using Ollama and adds comments to Ghidra"""
    
    def __init__(self, monitor: TaskMonitor):
        self.monitor = monitor
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama3"
        self.max_tokens = 100

    def run(self):
        """Process all functions in the current program"""
        self.monitor.setMessage("Starting Ollama function summarization...")
        functions = currentProgram.getFunctionManager().getFunctions(True)
        total = functions.size()
        
        for i, func in enumerate(functions):
            if self.monitor.isCancelled():
                break
                
            self.monitor.setProgress(i / total)
            self.monitor.setMessage(f"Summarizing: {func.getName()} ({i+1}/{total})")
            
            try:
                self.summarize_function(func)
            except Exception as e:
                print(f"Error summarizing {func.getName()}: {str(e)}")
                continue
            
            time.sleep(1)  # Avoid Ollama rate limits

    def summarize_function(self, func: Function):
        """Get function body, send to Ollama, add comment"""
        # Get function body via decompiler
        decomp = Decompiler()
        if not decomp.decompileFunction(func, self.monitor):
            return
            
        decomp_func = decomp.getDecompiledFunction()
        if not decomp_func:
            return
            
        body = decomp_func.getBody()
        if not body or len(body) < 20:  # Skip trivial functions
            return

        # Truncate large functions
        max_body_len = 1000
        if len(body) > max_body_len:
            body = body[:max_body_len] + " [truncated]"

        # Generate prompt
        prompt = (
            "Summarize this function's purpose and behavior in 1-2 sentences. "
            "Do not include any technical details like register names or memory addresses. "
            "Focus on the high-level logic and purpose. "
            f"Function body: {body}"
        )

        # Send to Ollama
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": self.max_tokens}
                },
                timeout=30
            )
            response.raise_for_status()
            summary = response.json().get("response", "").strip()
            
            if not summary:
                return
                
            # Add comment to function
            comment = f"// Ollama Summary: {summary}"
            func.setComment(comment)
            
        except requests.exceptions.RequestException as e:
            print(f"Ollama connection error: {str(e)}")
            return

if __name__ == "__main__":
    # Run as a standalone script in Ghidra
    monitor = TaskMonitor()
    summarizer = OllamaSummarizer(monitor)
    summarizer.run()
