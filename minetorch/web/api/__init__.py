from flask import Blueprint, jsonify, request, abort, g
import peewee
import json
from minetorch.core import setup_runtime_directory
from minetorch import model, dataset, dataflow, loss, optimizer
from minetorch.orm import Experiment, Model, Snapshot, Dataset, Dataflow, Optimizer, Loss, Component
from flask import render_template

api = Blueprint('api', 'api', url_prefix='/api')
experiment = Blueprint('experiment', 'experiment', url_prefix='/api/experiments/<experiment_id>')

@experiment.before_request
def experiment_before_request():
    experiment_id = request.view_args['experiment_id']
    g.experiment = Experiment.get(id=experiment_id)
    g.snapshot = g.experiment.draft_snapshot()
    if not g.snapshot:
        g.snapshot = g.experiment.create_draft_snapshot()

@experiment.route('', methods=['DELETE'])
def delete_experiment(experiment_id):
    g.experiment.delete()
    return jsonify({'message': 'ok'})

@experiment.route('/running', methods=['POST'])
def train_experiment():
    pass

@api.route('/dataflows', methods=['GET'])
def dtaflows():
    return jsonify(list(map(lambda m: m.to_json_serializable(), dataflow.registed_dataflows)))

@api.route('/losses', methods=['GET'])
def losses():
    return jsonify(list(map(lambda m: m.to_json_serializable(), loss.registed_losses)))

@api.route('/optimizers', methods=['GET'])
def optimizers():
    return jsonify(list(map(lambda m: m.to_json_serializable(), optimizer.registed_optimizers)))

@api.route('/experiments', methods=['GET'])
def experiments_list():
    return jsonify(list(map(
        lambda m: m.to_json_serializable(),
        Experiment.select().where(Experiment.deleted_at == None).order_by(Experiment.created_at.desc())
    )))

@api.route('/experiments', methods=['POST'])
def create_experiment():
    name = request.values['name']
    if not name: abort(422)
    try:
        experiment = Experiment.create(name=name)
    except peewee.IntegrityError: abort(409)
    experiment.create_draft_snapshot()
    return jsonify(experiment.to_json_serializable())

def create_component(component_class):
    name = request.values['name']
    if not name: abort(422)

    settings = request.values.to_dict()
    settings.pop('name')
    try:
        component = component_class.create(
            name=name,
            settings=json.dumps(settings),
            snapshot_id=g.snapshot.id
        )
    except peewee.IntegrityError: abort(409)
    return jsonify(component.to_json_serializable())

def get_component(component_class):
    try:
        component = component_class.select().where(component_class.snapshot == g.snapshot).get()
    except peewee.DoesNotExist:
        return jsonify({})
    return jsonify(component.to_json_serializable())

def update_component(component_class):
    try:
        component = component_class.select().where(component_class.snapshot == g.snapshot).get()
    except peewee.DoesNotExist:
        return abort(404)
    component.settings = json.dumps(request.values.to_dict())
    component.save()
    return jsonify(component.to_json_serializable())

@experiment.route('/datasets', methods=['GET'])
def datasets_list(experiment_id):
    return jsonify(list(map(lambda m: m.to_json_serializable(), dataset.registed_datasets)))

@experiment.route('/datasets', methods=['POST'])
def create_dataset(experiment_id):
    return create_component(Dataset)

@experiment.route('/datasets/selected', methods=['GET'])
def get_dataset(experiment_id):
    return get_component(Dataset)

@experiment.route('/datasets/selected', methods=['PATCH'])
def update_dataset(experiment_id):
    return update_component(Dataset)

@experiment.route('/dataflows', methods=['GET'])
def dataflows_list(experiment_id):
    return jsonify(list(map(lambda m: m.to_json_serializable(), dataflow.registed_dataflows)))

@experiment.route('/dataflows', methods=['POST'])
def create_dataflow(experiment_id):
    return create_component(Dataflow)

@experiment.route('/dataflows/selected', methods=['GET'])
def get_dataflow(experiment_id):
    return get_component(Dataflow)

@experiment.route('/dataflows/selected', methods=['PATCH'])
def update_dataflow(experiment_id):
    return update_component(Dataflow)

@experiment.route('/optimizers', methods=['GET'])
def optimizers_list(experiment_id):
    return jsonify(list(map(lambda m: m.to_json_serializable(), optimizer.registed_optimizers)))

@experiment.route('/optimizers', methods=['POST'])
def create_optimizer(experiment_id):
    return create_component(Optimizer)

@experiment.route('/optimizers/selected', methods=['GET'])
def get_optimizer(experiment_id):
    return get_component(Optimizer)

@experiment.route('/optimizers/selected', methods=['PATCH'])
def update_optimizer(experiment_id):
    return update_component(Optimizer)

@experiment.route('/losses', methods=['GET'])
def losses_list(experiment_id):
    return jsonify(list(map(lambda m: m.to_json_serializable(), loss.registed_losses)))

@experiment.route('/losses', methods=['POST'])
def create_loss(experiment_id):
    return create_component(Loss)

@experiment.route('/losses/selected', methods=['GET'])
def get_loss(experiment_id):
    return get_component(Loss)

@experiment.route('/losses/selected', methods=['PATCH'])
def update_loss(experiment_id):
    return update_component(Loss)

@experiment.route('/models', methods=['POST'])
def create_model(experiment_id):
    return create_component(Model)

@experiment.route('/models/selected', methods=['GET'])
def get_model(experiment_id):
    return get_component(Model)

@experiment.route('/models', methods=['GET'])
def models_list(experiment_id):
    return jsonify(list(map(lambda m: m.to_json_serializable(), model.registed_models)))

@experiment.route('/models/selected', methods=['PATCH'])
def update_model(experiment_id):
    return update_component(Model)

@experiment.route('/training', methods=['POST'])
def start_train(experiment_id):
    g.experiment.publish()
    setup_runtime_directory(g.experiment)
    return jsonify({'message': 'ok'})

@api.errorhandler(422)
def entity_not_processable(error):
    return jsonify({'message': 'Entity is not processable'}), 422

@api.errorhandler(409)
def resource_conflict(error):
    return jsonify({'message': 'Resource already exists'}), 409
