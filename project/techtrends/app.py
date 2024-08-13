import sqlite3
import logging
import os
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

db_connection_counter=0
# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connection_counter
    db_connection_counter += 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    try:
        connection = get_db_connection()
        post = connection.execute('SELECT * FROM posts WHERE id = ?',
                            (post_id,)).fetchone()
    except sqlite3.Error:
        app.logger.error("SQLite database connection error")
    finally:
        connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    app.logger.info("The homepage has been retrieved.")
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.warning(f"Post with ID {post_id} not found!")
      return render_template('404.html'), 404
    else:
      app.logger.info(f"The <<{post['title']}>> post has been retrieved")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("The about webpage has been retrieved.")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
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
            app.logger.info(f"The <<{title}>> post has been created successfully")
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')


# Define the health check functionality
@app.route('/healthz', methods=["GET"])
def healthz():
    """
    Checks the connection to the database and returns the health status as helath 
    if there is table 'posts' in the database other wise return 500 unhealthy
    """
    try:
        connection = get_db_connection()
        connection.execute('SELECT 1 FROM posts LIMIT 1')
    except sqlite3.OperationalError:
        app.logger.info('Database is not accessible')
        return jsonify({"result": "Unhealthy - database not accessible"}), 500
    app.logger.info('Health check successful')
    return jsonify({"result": "OK - healthy"})

# Define the metrics functionality
@app.route('/metrics', methods=['GET'])
def metrics():
    global db_connection_counter
    connection = get_db_connection()
    total_posts = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    
    connection.close()
    return jsonify({
        'post_count': total_posts,
        'db_connection_count': db_connection_counter
    })

# start the application on port 3111
if __name__ == "__main__":
    loglevel = os.getenv("LOGLEVEL", "DEBUG").upper()
    loglevel = (
        getattr(logging, loglevel)
        if loglevel in ["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING",]
        else logging.DEBUG
    )

    # Create a handler for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)  # Set level for stdout

    # Create a handler for stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)  # Set level for stderr

    format_handler = '%(asctime)s: %(levelname)-8s %(name)-10s  %(message)s' # Format handler

    formatter = logging.Formatter(format_handler, datefmt='%Y-%m-%d, %H:%M:%S')
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)
    handlers = [stdout_handler, stderr_handler]

    # Configure logging
    logging.basicConfig(
        handlers=handlers,
        level=loglevel,
    )
    app.run(host='0.0.0.0', port='3111', debug=True)
