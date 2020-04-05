from flask import Flask, request, render_template_string, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy



# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app3.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning
    SQLALCHEMY_ECHO = False

def create_app():
    """ Flask application factory """

    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        email = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        
    # Create all database tables (every time a new table is added it runs this, otherwise it doesn't)
    db.create_all()

    # Create 'member@example.com' user with no roles
    if not User.query.filter(User.email == 'member@example.com').first():
        user = User(
            email='member@example.com',
            first_name='Joe',
            last_name='Doe'
        )
        db.session.add(user)
        db.session.commit()

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        return render_template('index.html')

    @app.route('/user_edit/<user_id>', methods={'GET','POST'})
    def user_edit(user_id):
        validation_error = ""
        user = User.query.filter(User.id == user_id).first()

        if request.method == 'GET':
            request.form.first_name = user.first_name
            request.form.last_name = user.last_name
            request.form.email = user.email
        elif request.method == 'POST':

            if '@' not in request.form['email']:
                validation_error = "Invalid Email!"
            else:
                user.first_name = request.form['first_name']
                user.last_name = request.form['last_name']
                user.email = request.form['email']

                db.session.add(user)
                db.session.commit()
                flash('User Updated!!', 'success')
                flash('Demo error message...', 'error')
                return redirect(url_for('home_page'))

        return render_template('user_edit.html', validation_error=validation_error)

    return app


# Start development web server...
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=4000, debug=True)
