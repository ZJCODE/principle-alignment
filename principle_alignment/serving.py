import os
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List,Optional
import uvicorn
from principle_alignment import Alignment
from principle_alignment.utilities.logger import Logger


def parse_args():
    parser = argparse.ArgumentParser(description='Principle Alignment API Server')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind the server to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port to bind the server to (default: 8000)')
    parser.add_argument('--principles-path', type=str,
                       default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "principles.md"),
                       help='Path to principles.md file')
    parser.add_argument('--env-file', type=str, default='.env',
                       help='Path to .env file (default: .env)')
    parser.add_argument('--verbose', type=bool, default=False,
                       help='Verbose mode (default: False)')
    return parser.parse_args()



# 创建 FastAPI 实例
app = FastAPI(
    title="Alignment API",
    description="Principle Alignment Service API",
    version="1.0.0"
)

def init_alignment(principles_path: str, env_file: str = ".env", verbose: bool = False):
    """Initialize alignment with given principles path"""

    # 加载环境变量
    load_dotenv(env_file)
    # 初始化 OpenAI 客户端 以及 模型
    openai_client = OpenAI(
        api_key=os.environ.get("API_KEY"),
        base_url=os.environ.get("BASE_URL"),
    )
    openai_model = os.environ.get("MODEL")
    
    # 初始化 Alignment
    alignment = Alignment(client=openai_client, model=openai_model, verbose=verbose)
    
    if not os.path.exists(principles_path):
        raise FileNotFoundError(f"Principles file not found at: {principles_path}")
    
    alignment.prepare(principles_file=principles_path)
    print(f"Successfully loaded principles from: {principles_path}")
    return alignment

# 定义请求模型
class AlignmentRequest(BaseModel):
    """Request model for alignment API."""
    text: str
    rectify: bool | None = None

# 定义响应模型
class AlignmentResponse(BaseModel):
    is_violation: bool
    violated_principles: List[str]
    explanation: Optional[str] = None
    rectification: Optional[str] = None

# 全局变量存储 alignment 实例
alignment = None

@app.get("/")
async def root():
    return {"message": "Welcome to Alignment API"}

@app.get("/health")
async def health_check():
    if alignment is None:
        raise HTTPException(status_code=503, detail="Alignment service not initialized")
    return {"status": "healthy"}

@app.post("/align", response_model=AlignmentResponse)
async def align(request: AlignmentRequest):
    try:  
        if request.rectify:
            result = alignment.align_and_rectify(request.text)
            return AlignmentResponse(
                is_violation=result["is_violation"],
                violated_principles=result["violated_principles"],
                explanation=result["explanation"],
                rectification=result["rectification"]
            )
        else:
            result = alignment.align(request.text)
            return AlignmentResponse(
                is_violation=result["is_violation"],
                violated_principles=result["violated_principles"],
                explanation=result["explanation"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host: str = "0.0.0.0", port: int = 8000, principles_path: str = None, 
                env_file: str = ".env", verbose: bool = False):
    """启动 FastAPI 服务器"""
    global alignment
    alignment = init_alignment(principles_path,env_file,verbose)
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    args = parse_args()
    start_server(
        host=args.host,
        port=args.port,
        principles_path=args.principles_path,
        env_file=args.env_file,
        verbose=args.verbose
    )


# python -m principle_alignment.serving
# python -m principle_alignment.serving --host 127.0.0.1 --port 8080 --principles-path ./examples/principles.md --env-file .env --verbose True

# curl -X POST "http://localhost:8080/align" \
#      -H "Content-Type: application/json" \
#      -d '{"text": "Tom is not allowed to join this club because he is not a member."}'


# curl -X POST "http://localhost:8080/align" \
#      -H "Content-Type: application/json" \
#      -d '{"text": "Tom is not allowed to join this club because he is not a member.", "rectify": true}'