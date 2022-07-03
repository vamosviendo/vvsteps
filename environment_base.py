from vvutils.os import env_or_input
from vvsteps.driver import MiFirefox

from vvsteps.helpers import crear_usuario_base


def before_all(context):
    context.browser = MiFirefox()
    context.test_username = env_or_input('TEST_USERNAME')
    context.test_password = env_or_input('TEST_PASSWORD', password=True)


def after_all(context):
    context.browser.quit()


def before_scenario(context, scenario):
    crear_usuario_base(context.test_username, context.test_password)
