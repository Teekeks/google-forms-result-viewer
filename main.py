import logging

from googleapiclient.discovery import build
from google.oauth2 import service_account
from aiohttp_jinja2 import setup as jinja2_setup, template
import jinja2
import aiohttp
from aiohttp import web
from os import path
from cachetools import cached, TTLCache

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

creds = service_account.Credentials.from_service_account_file('forms-viewer-825e7c854b9b.json', scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()
logging.basicConfig(level=logging.INFO)

app: web.Application = web.Application()
jinja2_setup(app,
             context_processors=[],
             loader=jinja2.FileSystemLoader(str(path.join(path.dirname(__file__), 'templates/'))))
routes = web.RouteTableDef()


# cache the response for up to a minute
@cached(cache=TTLCache(maxsize=1024, ttl=60))
def get_sheet_values(sheet_id: str):
    logging.info(f'fetching values from sheet {sheet_id}...')
    sheet_data = sheet.get(spreadsheetId=sheet_id).execute()
    title = sheet_data['properties']['title']
    result = sheet.values().get(spreadsheetId=sheet_id, range='A1:AA').execute()
    values = result.get('values', [])
    questions = values[0]
    answers = values[1:]
    return list(enumerate([set(zip(questions, answer)) for answer in answers], start=1)), title

@routes.get('/a/{sheet_id}')
@template('result.html')
async def show_results(request: web.Request):
    data, title = get_sheet_values(request.match_info['sheet_id'])
    return {'answers': data, 'title': title}


app.add_routes(routes)
web.run_app(app, port=8081)
