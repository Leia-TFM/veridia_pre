from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ajustes de configuración para la aplicación definidos aquí parámetros para todo el proyecto
    APP_NAME: str = "VERID.IA"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    PROMPT: str = ""
    API_KEY: str = "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"
    MODELO: str = "Qwen2.5-72B-Instruct"  

    class Config:
        env_file = ".env"  # Archivo de entorno para cargar variables de configuración
        env_file_encoding = "utf-8"  # Codificación del archivo de entorno

settings = Settings()  # Instancia de configuración que se puede importar en otras partes del proyecto