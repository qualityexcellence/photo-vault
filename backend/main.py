from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.routes import auth, images, search, admin, analytics

app = FastAPI(
    title="Photo Vault API",
    description="AI-powered photo management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router)
app.include_router(images.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(analytics.router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


def custom_openapi():
    """Custom OpenAPI schema with Bearer token security"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Photo Vault API",
        version="1.0.0",
        description="AI-powered photo management",
        routes=app.routes,
    )
    
    # Add Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token"
        }
    }
    
    # Add security to all endpoints
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation.setdefault("security", [])
                operation["security"].append({"bearerAuth": []})
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
