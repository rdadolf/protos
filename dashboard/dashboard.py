import sys
import os
import os.path

import flask
import flask.json

import protos
import protos.query
#import protos.internal

app = flask.Flask(__name__, instance_path='/var/www/flask_instance')
app.debug=True

@app.route('/')
def display_dashboard():
  protos.config.load(os.path.join(app.instance_path,'protos.config'))
  #protos.config.server_name = app.config['SERVER_NAME'].split(':')[0] # strip the port number, if there is one
  #app.logger.debug(str([(x,getattr(protos.config,x)) for x in ['storage','storage_server','project_name']]))
  return flask.render_template('dashboard.html')

@app.route('/experiment_info')
def load_experiment_info():
  try:
    project = flask.request.args.get('project', default='default', type=str)
    xid = flask.request.args.get('xid',type=str)
  except ValueError:
    flask.abort(400, description='Invalid arguments supplied to experiment list AJAX request.')

  protos.config.project_name = project
    
  os.environ['PGPASSFILE']='/var/www/flask_instance/pgpass'
  os.environ['POSTGRES_USERNAME']='dashboard'
  
  exp = protos.query.exact_experiment(xid)
  bundles = exp.search_bundles({})

  return flask.render_template('experiment_details.html', xid=xid, bundles=bundles)

@app.route('/experiment_list')
def load_experiment_list():
  try:
    project = flask.request.args.get('project', default='default', type=str)
    serialized_mask = flask.request.args.get('mask', default='{}', type=str)
  except ValueError:
    flask.abort(400, description='Invalid arguments supplied to experiment list AJAX request.')

  protos.config.project_name = project
  mask = flask.json.loads(serialized_mask)

  response = []
  os.environ['PGPASSFILE']='/var/www/flask_instance/pgpass'
  os.environ['POSTGRES_USERNAME']='dashboard'
  exps = protos.query.search_experiments(mask)
  #app.logger.debug(exps)
  for exp in exps:
    exp_data = exp.metadata()
    # Expected fields: 'id', 'progress', 'name', 'time'
    for field in ['id','progress','name','time']:
      if field not in exp_data:
        flask.abort(400, description='Experiment "{0}" missing metadata field: "{1}"'.format(str(exp.id),field))
    response.append(flask.render_template('experiment.html',experiment=exp_data))

  return flask.json.dumps(response)
