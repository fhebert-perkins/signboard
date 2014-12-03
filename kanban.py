#!/usr/bin/env python

from flask import Blueprint, g, request, render_template, abort, jsonify
# Creating a simple de-normalized, json-based database on top of a RDBMS
import sqlite3
import json

kanban = Blueprint('kanban', __name__, template_folder='kanban_templates')
config = {}
config['DATABASE_URL'] = 'db/database.sqlite'
sqlite3.register_converter("JSON", json.loads)
#kanban.secret_key = 'some random secret key'

@kanban.route('/')
def index():
	return render_template('signboard.html')


@kanban.route('/boards/<int:id>', methods=['GET'])
def get_board(id):
	cursor = g.db.execute('SELECT data FROM boards WHERE id = ?', (id,))
	row = cursor.fetchone()
	if (row is not None):
		# row['data'] was made a python object by the registered converter,
		# then back into a json here. Could eventually be under performant?
		return jsonify(row['data'])
	else:
		abort(404)


@kanban.route('/boards/<int:id>', methods=['PUT'])
def put_board(id):
	g.db.execute('UPDATE boards SET data = ? WHERE id = ?', (request.data, id))
	return ''  # TODO: figure out the correct way to notify client this was successful


# Using thread locals so that requests always have global access to a db
# connection.
@kanban.before_request
def before_request():
	g.db = connect_db()


@kanban.teardown_request
def teardown_request(error=None):
	if hasattr(g, 'db'):
		if error is None:
			g.db.commit()
		else:
			g.db.rollback()
		g.db.close()


def connect_db():
	conn = sqlite3.connect(config['DATABASE_URL'], detect_types=sqlite3.PARSE_DECLTYPES)
	conn.row_factory = sqlite3.Row
	return conn


def init_db():
	''' Create the schema then dump some json data into the newly created table.
	Not including a direct insert of the json in the sql so that I can maintain
	syntax highlighting and linting on the json file.
	'''
	from contextlib import closing

	with closing(connect_db()) as db:
		with kanban.open_resource('db/schema.sql') as schema:
			db.executescript(schema.read())
			with open('db/signboard.json') as data:
				db.execute('INSERT INTO boards(data) VALUES (?)', (data.read(),))
		db.commit()
