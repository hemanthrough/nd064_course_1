import logging
import sqlite3
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`

# Define the Flask application
app = Flask(__name__)
app.config['db_reads'] = 0
fm = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('application.logs')
handler.setFormatter(fm)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(fm)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(fm)
app.logger.addHandler(handler)
app.logger.addHandler(stderr_handler)
app.logger.addHandler(stdout_handler)
app.logger.setLevel(logging.DEBUG)
def get_db_connection():
    app.config['db_reads'] += 1
    app.logger.info("Getting db connection")
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    app.logger.info("getting article with id {}".format(str(post_id)))
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


# Define the main route of the web application 
@app.route('/')
def index():
    app.logger.info("getting all articles")
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    app.logger.info("fetched {} articles".format( len(posts)))
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warn("article with id {}, not found".format(post_id))
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
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def status():
    app.logger.info("Reached health endpoint")
    try:
        connection = get_db_connection()

        connection.execute('SELECT * FROM posts ')
        connection.close()

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
    connection = get_db_connection()
    app.logger.info("Counting number of articles")
    sample = connection.execute('select Count() from posts')

    number_posts = sample.fetchone()[0]
    connection.commit()
    connection.close()
    response = app.response_class(
            response=json.dumps({"post_count": number_posts, "db_connection_count": app.config['db_reads']}),
            status=200,
            mimetype='application/json'
    )

    return response

# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
