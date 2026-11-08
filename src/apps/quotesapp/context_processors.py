def layout_proto(request):
    """The layout prototype in use, if any (see quotesapp/proto.py)."""
    from .proto import current_layout, LAYOUTS
    return {'layout': current_layout(request), 'proto_layouts': LAYOUTS.items()}
