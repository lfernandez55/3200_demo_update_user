# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

import datetime
from flask import Flask, request, render_template_string, render_template, redirect, url_for
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app3.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'xxxxxx@gmail.com'
    MAIL_PASSWORD = 'xxxxxx'
    MAIL_DEFAULT_SENDER = '"MyApp" <noreply@example.com>'

    # Flask-User settings
    USER_APP_NAME = "Flask-User Basic App"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"


def create_app():
    """ Flask application factory """

    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-BabelEx
    babel = Babel(app)

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User information
        first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

        # Define the relationship to Role via UserRoles
        roles = db.relationship('Role', secondary='user_roles')

    # Define the Role data-model
    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    # Define the UserRoles association table
    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    class Category(db.Model):
        __tablename__ = 'category'
        id = db.Column(db.Integer, primary_key=True)
        description = db.Column(db.String(255), nullable=False)
        books = db.relationship('Book', backref='category', lazy=True)

    class Book(db.Model):
        __tablename__ = 'book'
        id = db.Column(db.Integer(), primary_key=True)
        author = db.Column(db.String(255), nullable=False)
        title = db.Column(db.String(255), nullable=False)
        isbn = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String(255), nullable=False)
        category_id = db.Column(db.Integer, db.ForeignKey('category.id'),
        nullable=False)


    # Create all database tables
    db.create_all()

    # Create 'member@example.com' user with no roles
    if not User.query.filter(User.email == 'member@example.com').first():
        user = User(
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        db.session.add(user)
        db.session.commit()

    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    if not User.query.filter(User.email == 'luke.fernandez@gmail.com').first():
        user = User(
            email='luke.fernandez@gmail.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password2'),
        )
        user.roles.append(Role(name='Admin'))
        user.roles.append(Role(name='Agent'))
        db.session.add(user)
        db.session.commit()

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        return render_template('index.html')

        # The Admin page requires an 'Admin' role.
    @app.route('/admin')
    @roles_required('Admin')    # Use of @roles_required decorator
    def admin_page():
        return render_template('admin.html')

    @app.route('/seedDB')
    @roles_required('Admin')
    def seedDB():
        cat = Category(description='Horror')
        db.session.add(cat)

        cat = Category(description='Sociology')
        db.session.add(cat)

        book = Book(author='Mary Shelly',title='Frankenstein',isbn=123,description='A horror story written by a romantic',category_id=1)
        db.session.add(book)

        #bulk INSERT
        book_objects = [
            Book(author='Henry James',title='The Turn of the Screw',isbn=12,description='Another British horror story',category_id=1),
            Book(author='Karl Marx',title='The Communist Manifesto',isbn=1234,description='The iconic document of communism',category_id=2),
            Book(author='Max Weber',title='The Protestant Ethic and The Spirit of Capitalism',isbn=1235,description='Protestantism catalyzed capitalism',category_id=2),
        ]
        db.session.bulk_save_objects(book_objects)

        #after adding the objects to the session, commit it
        db.session.commit()

        return '<h1>DB Seeded!</h1>'

    @app.route('/erase_DB')
    @roles_required('Admin')
    def eraseDB():
            db.session.query(Book).delete()
            db.session.query(Category).delete()
            db.session.commit()

            return '<h1>DB Erased!</h1>'


    @app.route('/all_books')
    @login_required
    def books():
        my_list_of_books = db.session.query(Category, Book).join(Category).order_by(Category.id)
        # print(type(my_list_of_books))
        # for row in my_list_of_books:
        #     print(row.Book.author)

        return render_template('all_books.html', books=my_list_of_books)


    @app.route('/addbook', methods={'GET','POST'})
    @login_required
    def addbook():
        if request.method == 'POST':
            author = request.form['author']
            title = request.form['title']
            isbn = request.form['isbn']
            description = request.form['description']
            category_field = request.form['category']

            sqlStatement = "SELECT rowid, * FROM Category WHERE description =" + "'" + category_field + "'"
            categoryID = db.engine.execute(sqlStatement)
            my_list_of_categories = []
            for row in categoryID:
                my_list_of_categories.append(row)
            if len(my_list_of_categories) == 0:
                returnStatus = db.engine.execute('INSERT INTO Category (description) VALUES (?)',[category_field],commit=True)
                categoryID = db.engine.execute('SELECT rowid, * FROM Category WHERE description = ? ',[category_field])
                my_list_of_categories = []
                for row in categoryID:
                    my_list_of_categories.append(row)
                categoryID = my_list_of_categories[0][0]
            else:
                categoryID = my_list_of_categories[0][0]

            returnStatus = db.engine.execute('INSERT INTO Book (author, title, isbn, description, category_id) VALUES (?, ?, ?, ?, ?)',
            (author, title, isbn, description, categoryID),commit=True)

            return redirect(url_for('home_page'))

        categories = db.engine.execute('SELECT * FROM Category ORDER BY description ASC')
        return render_template('addbook.html', categories=categories)

    @app.route('/categories')
    @login_required
    def categories():
        categories = db.engine.execute('SELECT rowid, * FROM Category ORDER BY description ASC')
        for cat in categories:
            print(cat['rowid'])
        return render_template('categories.html', categories=categories)


    @app.context_processor
    def utility_processor():
        def isAdmin(user):
            sqlStatement = "SELECT roles.name FROM roles JOIN user_roles ON roles.id=user_roles.role_id JOIN users ON users.id=user_roles.user_id WHERE users.email='" + user + "' AND roles.name='Admin'"
            roleName = db.engine.execute(sqlStatement)
            roleName = [row for row in roleName]
            if len(roleName) > 0 and roleName[0]['name'] == 'Admin':
                returnValue = 1
            else:
                returnValue = 0
            return returnValue
        return dict(isAdmin=isAdmin)
    return app




    return app


# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=4000, debug=True)
