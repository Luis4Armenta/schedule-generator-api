from typing import Annotated

from fastapi import Query
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from teachers.domain.model.teacher import Teacher

# from services.scraper import BS4WebScraper
# from services.teacher import TeacherService
# from services.text_analyzer.text_analyzer import TextAnalyzer
# from services.text_analyzer.azure_text_analyzer import AzureTextAnalyzer
from teachers.infrastructure.bs4_web_scraper import BS4WebScraper
from teachers.application.teacher import TeacherService
from teachers.infrastructure.text_analyzer.text_analyzer import TextAnalyzer
from teachers.infrastructure.text_analyzer.azure_text_analyzer import AzureTextAnalyzer

router = APIRouter()

@router.get(
  '/teachers/',
  summary='Obtener profesor',
  response_description="Un profesor que coincide con el nombre dado.",
  description='Ve la información disponible de un profesor dando su nombre.'
)
def get_teacher_by_name(
    teacher_name: Annotated[
        str,
        Query(
          min_length=5,
          max_length=50,
          pattern='^[A-Za-zÁ-Úá-ú]+ [A-Za-zÁ-Úá-ú]+ [A-Za-zÁ-Úá-ú]+$',
          title='Nombre del profesor',
          description='Nombre del profesor que se desea buscar.'
          )
      ]
  ) -> Teacher:
  teacher_evaluator: TextAnalyzer = AzureTextAnalyzer()
  teacher_service = TeacherService(router.teachers, BS4WebScraper(teacher_evaluator))
  teacher = teacher_service.get_teacher(teacher_name)

  if teacher:
    return JSONResponse(content=jsonable_encoder(teacher), status_code=202)
  else:
    return JSONResponse(content={"message": "Teacher not found..."}, status_code=404)
