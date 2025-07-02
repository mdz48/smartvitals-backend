#!/usr/bin/env python3
"""
Script para probar la conexión WebSocket y verificar que los datos llegan
"""
import asyncio
import websockets
import json
import time

async def test_websocket():
    """Prueba la conexión WebSocket y escucha mensajes"""
    uri = "ws://localhost:8000/ws/sensores"
    
    try:
        print("🔌 Conectando al WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket conectado exitosamente!")
            print("📡 Esperando mensajes de sensores...")
            print("💡 Ejecuta 'python test.py' en otra terminal para enviar datos")
            print("-" * 50)
            
            # Escuchar mensajes por 60 segundos
            start_time = time.time()
            while time.time() - start_time < 60:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"📊 Mensaje recibido: {json.dumps(data, indent=2)}")
                except asyncio.TimeoutError:
                    # No hay mensajes, continuar esperando
                    pass
                except Exception as e:
                    print(f"❌ Error recibiendo mensaje: {e}")
                    break
            
            print("⏰ Tiempo de prueba completado")
            
    except Exception as e:
        print(f"❌ Error conectando al WebSocket: {e}")
        print("💡 Asegúrate de que la API esté ejecutándose con: uvicorn main:app --reload")

if __name__ == "__main__":
    print("🧪 Iniciando prueba de WebSocket...")
    asyncio.run(test_websocket()) 