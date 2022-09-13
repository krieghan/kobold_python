from . import assertions

exclude_from_contents = set(('\n',))


def node_to_dict(node):
    if isinstance(node, str):
        return node

    contents = [x for x in node.contents if x not in exclude_from_contents]
    node_dict = {
        'tag': node.name,
        'attrs': node.attrs}

    if len(contents) == 1 and isinstance(contents[0], str):
        node_dict['text'] = contents[0]
    else:
        children = []
        for element in contents:
            children.append(node_to_dict(element))
        node_dict['children'] = children
    return node_dict

def assert_node_matches(
        html,
        tag_name,
        expected_node_dict,
        attrs=None,
        class_=None,
        type_compare='existing'):
    import bs4
    parsed = bs4.BeautifulSoup(
        html,
        'html.parser')
    kwargs = {}
    args = []
    if attrs is not None:
        kwargs['attrs'] = attrs
    if class_ is not None:
        kwargs['class_'] = class_
    if tag_name is not None:
        args.append(tag_name)
    matches = parsed.findAll(*args, **kwargs)
    if len(matches) == 0:
        raise AssertionError(
            'No html matches for {}, {}'.format(
                args,
                kwargs))
    elif len(matches) > 1:
        raise AssertionError(
            'More than 1 ({}) match for {}, {}'.format(
                len(matches),
                args,
                kwargs))
    else:
        match = matches[0]

    actual_node_dict = node_to_dict(match)
    assertions.assert_match(
        expected_node_dict,
        actual_node_dict,
        type_compare=type_compare)
