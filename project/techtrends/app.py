import sqlite3
import logging
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
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
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
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      return render_template('404.html'), 404
    else:
      app.logger.info(f"Article {post['title']} has been retrieved")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
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
            app.logger.info(f"Article {title} has been created")
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
#    logging.basicConfig(level=logging.DEBUG,)

   logging.basicConfig(
    format='%(levelname)s:%(name)s:%(asctime)s %(message)s',
    level=logging.DEBUG,
    datefmt='%d/%m/%Y, %H:%M:%S,')
   app.run(host='0.0.0.0', port='3111', debug=True)
