from typing import Union
from contextlib import suppress

from fastapi import FastAPI
from pydantic import BaseModel

import asyncio
import os
import shutil

app = FastAPI()
try:
    os.chdir("/app")
except:
    pass
directory = os.getcwd()

@app.get("/")
async def landing():
    return {"message":"welcome..."}

class CompileRequest(BaseModel):
    filename: str
    content: str
    id: str # uid

class CompileResponse(BaseModel):
    id: str # uid
    final: str
    preproc: str # preprocessor code
    xml: list[str]
    message: str # compiler output
    success: bool # True if successful

@app.post("/compile/")
async def start_compile(cr: CompileRequest) -> CompileResponse:
    path = os.path.join(directory, cr.id)
    shutil.rmtree(path,True)
    os.mkdir(path)
    filename = os.path.join(path, "test.c")
    print("path",path, "file",filename)
    with open(filename, "w") as f:
        f.write(cr.content+"\n")
    env = os.environ.copy()
    env["CXMLC_CONFIG"] = "/app/config.ini"
    proc = await asyncio.create_subprocess_exec("/app/wrappercc.py","./test.c", stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE, env=env, cwd=path)
    stdout, stderr = await proc.communicate()
    print("retcode:",proc.returncode)
    print("stdout",stdout.decode())
    print("stderr", stderr.decode())
    from os import walk

    filenames = next(walk(path), (None, None, []))[2]
    print("filenames",filenames)
    response = CompileResponse(id=cr.id, final="",preproc="",xml=[],message="", success = proc.returncode == 0)
    response.message = stderr.decode() + stdout.decode()
    with suppress(FileNotFoundError):
        with open(os.path.join(path, "cxmlc", "input0.c"),"r") as f:
            response.preproc = f.read()
        with open(os.path.join(path, "cxmlc", "Pass1.xml"),"r") as f:
            response.xml = [f.read()]
        with open(os.path.join(path, "cxmlc", "final.c"),"r") as f:
            response.final = f.read()
    return response