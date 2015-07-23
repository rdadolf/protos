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

  autoload = flask.request.args.get('autoload',default=None,type=str)
  return flask.render_template('dashboard.html', autoload=autoload)

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
  exp_md = exp.metadata()
  bundles = exp.search_bundles({})

  error = (exp_md['last_error']!='')
  last_error = exp_md['last_error']
  return flask.render_template('experiment_details.html', xid=xid, bundles=bundles, error=error,last_error=last_error)

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
    for field in ['id','progress','name','time','last_error']:
      if field not in exp_data:
        flask.abort(400, description='Experiment "{0}" missing metadata field: "{1}"'.format(str(exp.id),field))
    error=False
    if exp_data['last_error']!='':
      error=True
    response.append(flask.render_template('experiment.html',experiment=exp_data,error=error))

  return flask.json.dumps(response)
