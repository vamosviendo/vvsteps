from __future__ import annotations

from datetime import date
from typing import cast, Self
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import InvalidElementStateException, \
    NoSuchElementException, UnexpectedTagNameException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from vvmodel.models import MiModel
from .helpers import esperar


class MiWebElement(WebElement):

    def contiene_elemento(self, elemento: Self, criterio: str = By.ID, debug: bool = False) -> bool:
        """ Devuelve True si encuentra elemento en obj MiWebElement."""
        if debug:
            print('TEXT:', self.text)
            print('HTML:', self.get_attribute('innerHTML'))

        try:
            self.find_element(criterio, elemento)
            return True
        except NoSuchElementException:
            return False

    def ocupa_espacio(self) -> bool:
        if self.value_of_css_property("width") in ["0", "0px", "0%"]:
            return False
        if self.value_of_css_property("display") == ("none"):
            return False
        return True

    def es_visible(self) -> bool:
        if not self.ocupa_espacio():
            return False
        if self.value_of_css_property("opacity") == "0%":
            return False
        if self.value_of_css_property("visibility") == "hidden":
            return False
        if not self.is_displayed():
            return False
        return True

    def int_css_prop(self, cssprop: str) -> int:
        """ Devuelve el valor de una propiedad css numérica como int."""
        return int(self.value_of_css_property(cssprop).rstrip('px%'))

    def innerWidth(self) -> int:
        """ Devuelve el ancho interior de un elemento, sin contar
            padding ni border."""
        if self.value_of_css_property('box-sizing') == 'content-box':
            return int(self.size.get('width')) - (
                    self.int_css_prop('padding-left') +
                    self.int_css_prop('padding-right') +
                    self.int_css_prop('border-left-width') +
                    self.int_css_prop('border-right-width')
            )
        else:
            return int(self.size.get('width'))

    def outerWidth(self) -> int:
        """ Devuelve el ancho externo de un elemento, incluyendo padding,
            border y margin."""
        if self.value_of_css_property('box-sizing') == 'border-box':
            return int(self.size.get('width')) + (
                    self.int_css_prop('padding-left') +
                    self.int_css_prop('padding-right') +
                    self.int_css_prop('border-left-width') +
                    self.int_css_prop('border-right-width') +
                    self.int_css_prop('margin-left') +
                    self.int_css_prop('margin-right')
            )
        else:
            return int(self.size.get('width')) + (
                    self.int_css_prop('margin-left') +
                    self.int_css_prop('margin-right')
            )

    def img_url(self) -> str:
        """ A partir del atributo src de una imagen, devuelve el url
        del campo ImageField correspondiente."""
        src = self.get_attribute('src')
        return urlparse(src).path

    def img_filename(self) -> str:
        """ A partir del atributo src de una imagen, devuelve el nombre de
            archivo del campo ImageField correspondiente."""
        return self.img_url()[len('/media/'):]

    @esperar
    def esperar_elemento(self, elemento: str, criterio: str = By.ID) -> Self:
        return self.find_element(criterio, elemento)

    @esperar
    def esperar_elementos(self, selector: str, criterio: str = By.CLASS_NAME, fail: bool = True) -> list[Self]:
        elementos = self.find_elements(criterio, selector)
        if fail:
            assert len(elementos) != 0, \
                f'no se encontraron elementos coincidentes con "{selector}"'
        return elementos

    @esperar
    def esperar_elemento_con_atributo(
            self, selector: str, atributo: str, valor: str, criterio: str = By.CLASS_NAME) -> Self:
        elementos = self.find_elements(criterio, selector)
        try:
            return next(
                x for x in elementos if x.get_attribute(atributo) == valor)
        except StopIteration:
            raise AssertionError(
                f'{selector} con {atributo} {valor} no encontrado')

    @esperar
    def esperar_enlace_con_titulo(self, titulo: str) -> Self:
        return self.esperar_elemento_con_atributo(
            "a", "title", titulo, By.TAG_NAME)

    def pulsar(self, boton: str = 'id_btn_submit', crit: str = By.ID):
        self.esperar_elemento(boton, crit).click()


class MiFirefox(webdriver.Firefox):
    _web_element_cls = MiWebElement

    def __init__(self, base_url: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url

    def ir_a_pag(self, url: str = ''):
        self.get(f"{self.base_url}{url}")

    @esperar
    def assert_url(self, url: str):
        assert url == urlparse(self.current_url).path

    def movermouse(self, horiz: int, vert: int):
        """ Dispara un movimiento del ratón."""
        webdriver.ActionChains(self).move_by_offset(horiz, vert).perform()

    @esperar
    def esperar_elemento(self, elemento: str, criterio: str = By.ID) -> MiWebElement:
        return cast(MiWebElement, self.find_element(criterio, elemento))

    @esperar
    def esperar_elementos(self, selector: str, criterio: str = By.CLASS_NAME, fail: bool = True) -> list[MiWebElement]:
        elementos = cast(list[MiWebElement], self.find_elements(criterio, selector))
        if fail:
            assert len(elementos) != 0, \
                f'no se encontraron elementos coincidentes con "{selector}"'
        return elementos

    @esperar
    def esperar_que_no_este(self, elemento, criterio=By.ID):
        try:
            self.find_element(criterio, elemento)
            raise AssertionError(
                f'El elemento {elemento}, que no debería existir, existe'
            )
        except NoSuchElementException:
            pass

    @esperar
    def esperar_que_desaparezca_de_elementos(
            self,
            selector: str,
            atributo: str,
            valor: str,
            criterio: str = By.CLASS_NAME,
            fail=True) -> list[MiWebElement]:
        elementos = cast(list[MiWebElement], self.find_elements(criterio, selector))
        if fail:
            assert len(elementos) != 0, \
                f'no se encontraron elementos coincidentes con {selector}'

        for elemento in elementos:
            if elemento.get_attribute(atributo) == valor:
                raise AssertionError(
                    f'Elemento con {atributo} {valor} presente')

        return elementos

    @esperar
    def esperar_elemento_con_atributo(
            self, selector: str, atributo: str, valor: str, criterio: str = By.CLASS_NAME) -> MiWebElement:
        elementos = cast(list[MiWebElement], self.find_elements(criterio, selector))

        try:
            return next(
                x for x in elementos if x.get_attribute(atributo) == valor)
        except StopIteration:
            raise AssertionError(
                f'{selector} con {atributo} {valor} no encontrado')

    def esperar_enlace_con_titulo(self, titulo: str) -> MiWebElement:
        return self.esperar_elemento_con_atributo(
            "a", "title", titulo, By.TAG_NAME)

    def esperar_opciones_de_campo(self, campo: str, form: MiWebElement | None = None) -> list[str]:
        form = form or self.esperar_elemento('form', By.TAG_NAME)
        try:
            select = form.esperar_elemento(f'id_{campo}')
        except NoSuchElementException:
            select = form.esperar_elemento(f'id_select_{campo}')
        return [x.text for x in select.esperar_elementos('option', By.TAG_NAME)]

    @staticmethod
    def completar_checkbox(checkbox: WebElement, boolvalue: bool):
        if checkbox.is_selected() != boolvalue:
            checkbox.click()

    def completar(self, id_campo: str, texto: str, criterio: str = By.ID):
        """ Completa un campo de texto en un form, o selecciona un valor
            de un campo select."""
        campo = self.esperar_elemento(id_campo, criterio=criterio)
        try:
            campo.clear()
            campo.send_keys(str(texto))
        except InvalidElementStateException:
            try:
                Select(campo).select_by_visible_text(texto)
            except UnexpectedTagNameException:
                if type(texto) == bool:
                    valor = texto
                elif texto.lower() == 'true':
                    valor = True
                else:
                    valor = False
                self.completar_checkbox(campo, valor)
            except TypeError:   # texto == None
                pass

    def pulsar(self, boton: str = 'id_btn_submit', crit: str = By.ID):
        self.esperar_elemento(boton, crit).click()

    def completar_form(self, **kwargs: str | date):
        for key, value in kwargs.items():
            self.completar(f"id_{key}", value)
        self.pulsar()

    def controlar_form(self, **kwargs: str | date | float | MiModel):
        for key, value in kwargs.items():
            if value is None:
                value = ""
            if type(value) is date:
                value = value.strftime('%Y-%m-%d')
            elif type(value) is float:
                value = str(value)
            elif isinstance(value, MiModel):
                value = str(value.pk)
            campo = self.esperar_elemento(f"id_{key}")
            assert campo.get_attribute("value") == value

    def controlar_modelform(self, instance: MiModel):
        self.controlar_form(**{
            k: getattr(instance, k) for k in instance.form_fields
        })

    def egresar(self):
        self.esperar_elemento('logout', By.LINK_TEXT).click()
