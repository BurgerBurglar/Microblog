import json
import requests
from flask_babel import _
from flask import current_app


def translate(text, source_language, dest_language):
    try:
        key = current_app.config["MS_TRANSLATOR_KEY"]
        if not key:
            raise KeyError
    except KeyError:
        return _("Translation unavailable right now - service not configured")
    auth = {'Ocp-Apim-Subscription-Key': key}
    r = requests.get(
        'https://api.microsofttranslator.com/v2/Ajax.svc' +
        '/Translate?text={}&from={}&to={}'.format(
            text, source_language, dest_language),
        headers=auth)
    if r.status_code != 200:
        return _("Translation unavailable right now - service failed")
    return json.loads(r.content.decode("utf-8-sig"))
