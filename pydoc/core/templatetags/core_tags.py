from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.encoding import force_bytes, force_text

register = template.Library()


@register.filter(is_safe=True)
def restructuredtext(value, short=False):
    try:
        from docutils.core import publish_parts
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in 'restructuredtext' filter: "
                "The Python docutils library isn't installed."
            )
        return force_text(value)
    else:
        docutils_settings = {
            'raw_enabled': False,
            'file_insertion_enabled': False,
        }
        docutils_settings.update(getattr(settings, 'RESTRUCTUREDTEXT_FILTER_SETTINGS', {}))
        parts = publish_parts(source=force_bytes(value), writer_name="html4css1",
                              settings_overrides=docutils_settings)
        out = force_text(parts["html_body"])
        try:
            if short:
                out = out.split("\n")[0]
        except IndexError:
            pass
        finally:
            return mark_safe(out)
