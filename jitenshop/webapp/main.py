"""Launch the webapp in debug mode.

WARNING: only for development purpose!!
"""

from flask import Flask, render_template

from jitenshop.webapp.api import api
from jitenshop.webapp import CustomJSONEncoder, ListConverter


# App declaration
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['ERROR_404_HELP'] = False
app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
app.url_map.converters['list'] = ListConverter
app.json_encoder = CustomJSONEncoder


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/doc')
def swagger_ui():
    return render_template("swagger-ui.html")


@app.route("/lyon")
def city_view():
    return render_template('city.html')


@app.route("/lyon/<int:station_id>")
def station_view(station_id):
    return render_template('station.html', station_id=station_id)


if __name__ == '__main__':

    api.init_app(app)
    app.run(port=7999, debug=True)
