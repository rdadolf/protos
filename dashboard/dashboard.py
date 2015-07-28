import sys
import os
import os.path

import flask
import flask.json

import protos
import protos.query
import protos.internal

app = flask.Flask(__name__, instance_path='/var/www/flask_instance')
app.debug=True

@app.route('/')
def display_dashboard():
  protos.config.load(os.path.join(app.instance_path,'protos.config'))

  autoload = flask.request.args.get('autoload',default='default',type=str)
  xfilter = flask.request.args.get('filter',default='{}',type=str)

  try:
    xfilter = flask.json.dumps(flask.json.loads(xfilter))
    error = ''
  except ValueError as e:
    error_type = type(e).__name__
    error_msg = 'Invalid experiment filter in URL: '+str(e)
    error = flask.render_template('flash_alert.html',type=error_type,message=error_msg)
    xfilter = '{}'

  return flask.render_template('dashboard.html', autoload=autoload, filter=xfilter, error=error)

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
  bundles_md = [b['metadata'] for b in bundles]

  return flask.render_template('experiment_details.html', exp_md=exp_md, bundles_md=bundles_md, has_error=(exp_md['last_error']!=''))

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
  try:
    exps = protos.query.search_experiments(mask)
  except Exception as e:
    response.append(flask.render_template('flash_alert.html',type=type(e).__name__,message='Failed to lookup experiment list. '+str(e)))
    exps = []

  m_exps = [exp.metadata() for exp in exps]

  s_exps = sorted(m_exps, key=lambda x: protos.internal.parse_timestamp(x['time']))

  #app.logger.debug(exps)
  for exp in s_exps:
    for field in ['id','progress','name','time','tags','last_error']:
      if field not in exp:
        flask.abort(400, description='Experiment "{0}" missing metadata field: "{1}"'.format(str(exp.id),field))
    error=False
    if exp['last_error']!='':
      error=True
    response.append(flask.render_template('experiment.html',experiment=exp, error=error))

  return flask.json.dumps(response)
