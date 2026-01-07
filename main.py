"""
API de Automação com Python
Comandos de controle de mouse e teclado
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import asyncio
from typing import Optional

app = FastAPI(title="API de Automação", version="1.0.0")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
