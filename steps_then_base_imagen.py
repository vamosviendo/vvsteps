import requests
from io import BytesIO
from PIL import Image

from behave import then

from vvsteps.helpers import tomar_atributo


@then('Veo que el elemento dado "{atrib}" '
      'se ve a su tamaño real')
def tamanio_real(context, atrib):
    elemento = tomar_atributo(context, atrib)
    response = requests.get(elemento.get_attribute('src'))
    imagen = Image.open(BytesIO(response.content))

    context.test.assertAlmostEqual(
        elemento.size['width'],
        imagen.width,
        places=0
    )
    context.test.assertAlmostEqual(
        elemento.size['height'],
        imagen.height,
        places=0
    )
