def layout_proto(request):
    """The layout prototype in use, if any (see quotesapp/proto.py)."""
    from .proto import current_layout, random_url, LAYOUTS
    # random_url is a callable, so only pages that show the top bar's Random
    # link pay for the parse
    return {'layout': current_layout(request), 'proto_layouts': LAYOUTS.items(),
            'random_url': random_url}
