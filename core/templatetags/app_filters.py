from django import template

register = template.Library()

@register.filter(name='get_class_name')
def get_class_name(obj):
    """Retorna o nome da classe de um objeto."""
    if obj:
        return obj.__class__.__name__
    return ''