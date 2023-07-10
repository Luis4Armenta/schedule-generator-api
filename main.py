from fastapi import FastAPI, Query, File, UploadFile, Form
from services.courses import CoursesService
from dotenv import dotenv_values
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from repositories.teachers_repository import TeacherRepository
from repositories.mongo_teachers_repository import MongoTeachersRepository
from models.teacher import Teacher
from services.teacher import TeacherService
from services.scraper import BS4WebScraper
from services.polarity_evaluator import TextBlobEvaluator, PolarityEvaluator
from services.translator import GoogleTranslator, Translator
from bs4 import BeautifulSoup
from lxml import etree
from models.course import Course, ScheduleCourse, session
from typing import List, Annotated
from services.schedule import SchedulesService

config = dotenv_values('.env')

app = FastAPI()
app.title = 'Profesores-API'
app.version = '0.0.1'

@app.on_event('startup')
def startup_db_clients():
  app.teachers: TeacherRepository = MongoTeachersRepository({
    'host': config['MONGODB_HOST'],
    'port': int(config['MONGODB_PORT']),
    'database': config['MONGODB_DATABASE']
  })
  
  app.teachers.connect()
  

@app.get('/', tags=['home'])
def message() -> HTMLResponse:
  print(config['MONGODB_HOST'])
  print(config['MONGODB_PORT'])
  print(config['MONGODB_DATABASE'])
  return HTMLResponse('<h1>Profesores API</h1>')

@app.get('/teachers/', tags=['Teachers'])
def get_teacher_by_name(teacher_name: str = Query(min_length=5)):
  google_translator: Translator = GoogleTranslator()
  polarity_evaluator: PolarityEvaluator = TextBlobEvaluator(google_translator)
  teacher_service = TeacherService(app.teachers, BS4WebScraper(polarity_evaluator))
  teacher = teacher_service.get_teacher(teacher_name.strip().upper())



  if teacher:
    return JSONResponse(content=jsonable_encoder(teacher), status_code=202)
  else:
    return JSONResponse(content={"message": "Teacher not found..."}, status_code=404)

@app.post('/upload/')
async def load(
    file: UploadFile,
    level: Annotated[str, Form()],
    semester: Annotated[str, Form()],
    start_time: Annotated[str, Form()],
    end_time: Annotated[str, Form()]
  ):
  courses_service = CoursesService()
  schedules_service = SchedulesService()
  
  
  courses: List[Course] = courses_service.parse_courses(await file.read())
 
  courses = courses_service.filter_coruses(courses, level, semester, start_time, end_time)
  
  schedules = schedules_service.generate_schedules(courses, 7)
  
  schedules = sorted(schedules, key=lambda x: x.popularity, reverse=True)
  
  print(len(schedules))
  return schedules
  
  

@app.on_event('shutdown')
def shutdown_db_clients():
  app.teachers.disconnect()
