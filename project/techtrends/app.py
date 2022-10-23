import logging
import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`

db_connections = 0
# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
fm = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('application.logs')
handler.setFormatter(fm)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)
def get_db_connection():
    global db_connections
    app.logger.info("Getting db connection")
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_connections+=1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global db_connections
    app.logger.info("getting article with id {}".format(str(post_id)))
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    db_connections-=1
    return post


# Define the main route of the web application 
@app.route('/')
def index():
    global db_connections
    app.logger.info("getting all articles")
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    db_connections -= 1
    connection.close()
    app.logger.info("fetched {} articles".format( len(posts)))
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info("article with id {}, not found".format(post_id))
        return render_template('404.html'), 404
    else:
        app.logger.info("article with id {} found".format(str(post_id)))
        app.logger.info("The title is {}".format(str(post[2])))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("Reched about page")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    app.logger.info("Creating article")
    global db_connections
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            db_connections -= 1
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def status():
    global db_connections
    app.logger.info("Reached health endpoint")
    try:
        connection = get_db_connection()

        connection.execute('SELECT * FROM posts ')
        connection.close()
        db_connections-=1

        return app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    except:
        return app.response_class(
            response=json.dumps({"result": "Un healthy"}),
            status=500,
            mimetype='application/json'
        )

    return response

@app.route('/metrics')
def metrics():
    global db_connections
    connection = get_db_connection()
    app.logger.info("Counting number of articles")
    sample = connection.execute('select Count() from posts')

    number_posts = sample.fetchone()[0]
    number_connections = db_connections
    connection.commit()
    db_connections -= 1
    connection.close()
    response = app.response_class(
            response=json.dumps({"post_count": number_posts, "db_connection_count": number_connections}),
            status=200,
            mimetype='application/json'
    )

    return response

# start the application on port 3111
if __name__ == "__main__":
    db_connections = 0
    app.run(host='0.0.0.0', port='3111')
