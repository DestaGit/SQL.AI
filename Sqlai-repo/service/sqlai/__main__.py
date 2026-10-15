"""Run the API locally: python -m sqlai"""
import uvicorn

from .api import create_app

if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
