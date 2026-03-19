from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ajustes de configuración para la aplicación definidos aquí parámetros para todo el proyecto
    APP_NAME: str = "Aquí va el nombre de nuestra aplicación"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True 

    UMBRAL_SOSPECHOSO: float = 0.6 #aquí se define el umbral para considerar un mensaje como sospechoso, tendremos que ajustar para verde, amarillo o rojo.
    

    class Config:
        env_file = ".env"  # Archivo de entorno para cargar variables de configuración
        env_file_encoding = "utf-8"  # Codificación del archivo de entorno

settings = Settings()  # Instancia de configuración que se puede importar en otras partes del proyecto