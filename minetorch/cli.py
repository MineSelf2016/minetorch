import os
import subprocess
import sys
from pathlib import Path
from multiprocessing import Process

import append_sys_path  # noqa: F401
import click
from dotenv import load_dotenv

load_dotenv()
PYTHON_INTERPRETER = 'python3'


def start_rpc_server():
    from rpc import RpcServer
    server = RpcServer(10, f"{os.getenv('SERVER_ADDR')}:{os.getenv('RPC_SERVER_PORT')}")
    server.serve()


def start_web_server():
    import minetorch.web as web
    os.environ["FLASK_ENV"] = 'development'
    os.environ["FLASK_APP"] = web.__file__
    process = subprocess.Popen(
        [PYTHON_INTERPRETER, '-m', 'flask', 'run', '-p', os.getenv('WEB_SERVER_PORT')],
        stdout=sys.stdout,
        cwd=Path(__file__).parent
    )
    process.wait()


def start_webpack_dev_server():
    import minetorch.web as web
    process = subprocess.Popen(
        ['yarn', 'run', 'dev'],
        cwd=Path(web.__file__).parent,
        stdout=sys.stdout
    )
    process.wait()


def start_socket_server():
    process = subprocess.Popen(
        ['gunicorn', '-b', f"{os.getenv('SERVER_ADDR')}:{os.getenv('WEB_SOCKET_PORT')}", '--worker-class', 'eventlet', '--reload', 'pusher:app'],
        cwd=Path(__file__).parent,
        stdout=sys.stdout
    )
    process.wait()


@click.group()
def cli():
    pass


@cli.command('dev')
@click.option('--webpack/--no-webpack', help='should start webpack-dev-server process', default=True)
def development(webpack):
    subprocs = []

    subprocs.append(Process(target=start_rpc_server))
    subprocs.append(Process(target=start_web_server))
    subprocs.append(Process(target=start_socket_server))
    if webpack:
        subprocs.append(Process(target=start_webpack_dev_server))

    for process in subprocs:
        process.start()
    for process in subprocs:
        process.join()


@cli.command('db:init')
def db_init():
    from minetorch.orm import Component, Experiment, Snapshot, Timer, Graph, Point
    for model_class in [Component, Experiment, Snapshot, Timer, Graph, Point]:
        model_class.drop_table()
        print(f"creating {model_class}")
        model_class.create_table(safe=False)
        print(f"{model_class} created")


@cli.command('proto:compile')
def proto_compile():
    minetorch_dir = Path(__file__).resolve().parents[1]
    proto_dir = Path('minetorch') / 'proto'
    subprocess.Popen([
        PYTHON_INTERPRETER,
        "-m",
        "grpc_tools.protoc",
        f"-I.",
        f"--python_out=.",
        f"--grpc_python_out=.",
        f"{proto_dir / 'minetorch.proto'}"
    ], stdout=sys.stdout, cwd=minetorch_dir)


@cli.command('runtime:run')
@click.option('--config', help='Absolute path of the config file', required=True)
def runtime_run(config):
    from run import main
    main(config)


if __name__ == '__main__':
    cli()
