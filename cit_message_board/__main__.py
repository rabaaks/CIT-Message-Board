from . import create_app

# If the module is invoked directly, launch the website in debug mode
# When using it in production, the WSGI server will do this
if __name__ == '__main__':
    app = create_app()
    app.run('0.0.0.0', debug=True)