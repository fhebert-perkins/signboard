from flask import Flask
from kanban import kanban

app=Flask(__name__)
app.register_blueprint(kanban)

if __name__ == "__main__":
    app.run()
