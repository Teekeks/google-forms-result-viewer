from googleapiclient.discovery import build
from google.oauth2 import service_account
from aiohttp_jinja2 import setup as jinja2_setup, template
import jinja2
import aiohttp
from aiohttp import web
from os import path

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

creds = service_account.Credentials.from_service_account_file('forms-viewer-825e7c854b9b.json', scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


app: web.Application = web.Application()
jinja2_setup(app,
             context_processors=[],
             loader=jinja2.FileSystemLoader(str(path.join(path.dirname(__file__), 'templates/'))))
app['static_root_folder'] = '/static'
routes = web.RouteTableDef()


@routes.get('/a/{sheet_id}')
@template('result.html')
async def show_results(request: web.Request):
    result = sheet.values().get(spreadsheetId=request.match_info['sheet_id'], range='A1:AA').execute()
    values = result.get('values', [])

    questions = values[0]
    answers = values[1:]
    return {'answers': enumerate([zip(questions, answer) for answer in answers])}


app.add_routes(routes)
app.add_routes([web.static('/static', 'static')])
web.run_app(app, port=8081)
