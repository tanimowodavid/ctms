from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.api.v1.api import api_router
from app.core.config import Settings, settings


def create_app(app_settings: Settings = settings) -> FastAPI:
	application = FastAPI(title="CTMS")

	@application.exception_handler(RequestValidationError)
	async def handle_request_validation(request: Request, exc: RequestValidationError):
		if request.method == "POST" and request.url.path.startswith("/api/v1/cohorts/") and request.url.path.endswith("/apply"):
			return JSONResponse(status_code=400, content={"detail": jsonable_encoder(exc.errors())})
		return await request_validation_exception_handler(request, exc)

	application.add_middleware(
		CORSMiddleware,
		allow_origins=app_settings.allowed_origins,
		allow_credentials=False,
		allow_methods=["GET", "POST"],
		allow_headers=["Content-Type"],
	)
	application.include_router(api_router, prefix="/api/v1")
	return application


app = create_app()
