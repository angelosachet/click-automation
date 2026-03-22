"""
API de Automação com Python
Comandos de controle de mouse e teclado
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import asyncio
from typing import Optional
import ctypes
import mmap
import websockets
import json
from contextlib import asynccontextmanager

class SPageFileGraphics(ctypes.Structure):
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("status", ctypes.c_int),
        ("session", ctypes.c_int),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
    ]

class SPageFileStatic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("smVersion", ctypes.c_wchar * 15),
        ("acVersion", ctypes.c_wchar * 15),
        ("numberOfSessions", ctypes.c_int),
        ("numCars", ctypes.c_int),  
        ("carModel", ctypes.c_wchar * 33),
        ("track", ctypes.c_wchar * 33),
    ]

def open_shared_memory(name, size):
    try:
        return mmap.mmap(-1, size, name)
    except Exception:
        return None  # jogo provavelmente não está aberto

graphics_map = open_shared_memory("acpmf_graphics", ctypes.sizeof(SPageFileGraphics))
static_map = open_shared_memory("acpmf_static", ctypes.sizeof(SPageFileStatic))

#True para usar dados mockados quando a memória compartilhada não estiver disponível
#False para quando tiver o jogo rodando e quiser os dados reais
USE_MOCK = False


def get_race_info():
    if USE_MOCK:
        return {
            "carro": "porsche_911_gt3",
            "pista": "monza",
            "ultima_volta": "01:42:321",
            "melhor_volta": "01:41:999",
            "tempo_atual": "00:15:200"
        }

    if not graphics_map or not static_map:
        return None

    try:
        graphics = SPageFileGraphics.from_buffer_copy(graphics_map)
        static = SPageFileStatic.from_buffer_copy(static_map)

        return {
            "carro": static.carModel.strip(),
            "pista": static.track.strip(),
            "ultima_volta": graphics.lastTime.strip(),
            "melhor_volta": graphics.bestTime.strip(),
            "tempo_atual": graphics.currentTime.strip()
        }
    except Exception:
        return None
    
def convert_time_to_ms(time_str): ##gogo dada
    try:
        if not time_str or time_str == "":
            return 0

        parts = time_str.split(":")
        minutes = int(parts[0])
        seconds = int(parts[1])
        millis = int(parts[2])

        return (minutes * 60 * 1000) + (seconds * 1000) + millis
    except:
        return 0

WS_URL = "ws://181.214.95.75:7080/input"

async def send_to_websocket():
    while True:
        data = get_race_info()

        if data:
            payload = {
                "type": "simulator-update",
                "data": {
                    "simNum": 1,
                    "pilot-name": "Player",
                    "car": data["carro"],
                    "track": data.get("pista") or "Unknown",
                    "lapData": {
                        "lapTime": convert_time_to_ms(data["ultima_volta"]),
                        "isValid": True
                    },
                    "bestLap": convert_time_to_ms(data["melhor_volta"])
                }
            }

            try:
                async with websockets.connect(WS_URL) as websocket:
                    print("Enviado:", payload)
                    await websocket.send(json.dumps(payload))

            except Exception as e:
                print("Erro ao enviar websocket:", e)

        await asyncio.sleep(1)  # envia a cada 1 segundo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria a task no loop ativo do FastAPI/Uvicorn.
    app.state.websocket_task = asyncio.create_task(send_to_websocket())
    try:
        yield
    finally:
        task = getattr(app.state, "websocket_task", None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="API de Automação", version="1.0.0", lifespan=lifespan)


def get_pyautogui():
    """Lazy import do pyautogui para evitar erros de display ao iniciar"""
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
    return pyautogui


class CommandRequest(BaseModel):
    code: str


class ClickRequest(BaseModel):
    code: str


@app.post("/click")
async def click_automation(request: ClickRequest):
    """
    Busca um botão igual à imagem button.png, clica nele e move o mouse para x:1000 y:0
    """
    if request.code != "aa22":
        raise HTTPException(status_code=401, detail="Invalid code")
    
    try:
        pyautogui = get_pyautogui()
        
        # Busca a imagem button.png na tela
        button_location = pyautogui.locateOnScreen('button.png', confidence=0.8)
        
        if button_location is None:
            return {
                "success": False,
                "message": "Button not found on screen",
                "error": "Could not locate button.png on the screen"
            }
        
        # Obtém o centro do botão encontrado
        button_center = pyautogui.center(button_location)
        
        # Clica no botão
        pyautogui.click(button_center.x, button_center.y)
        
        # Aguarda um momento
        time.sleep(0.3)
        
        # Move o mouse para a posição especificada
        pyautogui.moveTo(1000, 0, duration=0.5)
        
        return {
            "success": True,
            "message": "Click processed successfully",
            "data": {
                "buttonFound": True,
                "buttonPosition": {"x": button_center.x, "y": button_center.y},
                "finalPosition": {"x": 1000, "y": 0},
                "message": "Button clicked and mouse moved to target position"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Error processing click",
            "error": str(e)
        }


@app.post("/run-auto")
async def run_auto(request: CommandRequest):
    """
    Executa o comando Ctrl+C
    """
    if request.code != "aa22":
        raise HTTPException(status_code=401, detail="Invalid code")
    
    try:
        pyautogui = get_pyautogui()
        
        # Executa Ctrl+C
        pyautogui.hotkey('ctrl', 'c')
        
        return {
            "success": True,
            "message": "Run-auto command executed successfully",
            "data": {
                "command": "Ctrl+C",
                "message": "Copy command executed"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Error executing run-auto command",
            "error": str(e)
        }


@app.post("/kill")
async def kill_process(request: CommandRequest):
    """
    Aperta ESC, aguarda 3 segundos e executa Alt+F4
    """
    if request.code != "aa22":
        raise HTTPException(status_code=401, detail="Invalid code")
    
    try:
        pyautogui = get_pyautogui()
        
        # Aperta ESC
        pyautogui.press('esc')
        
        # Aguarda 3 segundos
        time.sleep(3)
        
        # Executa Alt+F4
        pyautogui.hotkey('alt', 'F4')
        
        return {
            "success": True,
            "message": "Kill command executed successfully",
            "data": {
                "commands": ["ESC", "Wait 3s", "Alt+F4"],
                "message": "Kill sequence completed successfully"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "Error executing kill command",
            "error": str(e)
        }


@app.get("/")
async def root():
    """
    Endpoint de status da API
    """
    return {
        "status": "online",
        "api": "Python Automation API",
        "version": "1.0.0",
        "endpoints": {
            "/click": "Busca botão, clica e move mouse para x:1000 y:0",
            "/run-auto": "Executa Ctrl+C",
            "/kill": "Executa ESC, aguarda 3s e Alt+F4"
        }
    }


@app.get("/race-info")
async def race_info():
    """
    Retorna informações da corrida do Assetto Corsa
    """
    data = get_race_info()

    if data is None:
        raise HTTPException(
            status_code=500,
            detail="Assetto Corsa não está rodando ou memória indisponível"
        )

    return {
        "success": True,
        "data": {
            "piloto": "Player",  # não vem da shared memory
            **data
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001)