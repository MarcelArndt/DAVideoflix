from django.apps import AppConfig

'''
to register the signals.py
 def ready(self):
        import auth_app.signals
'''
class AuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'
    def ready(self):
        import auth_app.signals

