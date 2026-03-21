"""AST template: web scraper via requests + BeautifulSoup.
Zero content literals. Parameters injected at runtime."""
import ast


def build_web_scraper_ast() -> ast.Module:
    """Returns AST defining: run(endpoint, query, selector) -> list[str]"""
    tree = ast.Module(body=[
        ast.Import(names=[ast.alias(name='requests')]),
        ast.ImportFrom(module='bs4', names=[ast.alias(name='BeautifulSoup')], level=0),

        ast.FunctionDef(
            name='run',
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg('endpoint'), ast.arg('query'), ast.arg('selector')],
                kwonlyargs=[], kw_defaults=[], defaults=[]
            ),
            body=[
                ast.Assign(
                    targets=[ast.Name('url', ctx=ast.Store())],
                    value=ast.JoinedStr(values=[
                        ast.Constant('https://'),
                        ast.FormattedValue(value=ast.Name('endpoint', ctx=ast.Load()), conversion=-1, format_spec=None),
                        ast.Constant('?q='),
                        ast.FormattedValue(value=ast.Name('query', ctx=ast.Load()), conversion=-1, format_spec=None),
                    ])
                ),
                ast.Assign(
                    targets=[ast.Name('resp', ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name('requests', ctx=ast.Load()), attr='get', ctx=ast.Load()),
                        args=[ast.Name('url', ctx=ast.Load())],
                        keywords=[ast.keyword(arg='headers', value=ast.Dict(
                            keys=[ast.Constant('User-Agent')],
                            values=[ast.Constant('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')]
                        ))]
                    )
                ),
                ast.Assign(
                    targets=[ast.Name('soup', ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Name('BeautifulSoup', ctx=ast.Load()),
                        args=[
                            ast.Attribute(value=ast.Name('resp', ctx=ast.Load()), attr='text', ctx=ast.Load()),
                            ast.Constant('html.parser')
                        ],
                        keywords=[]
                    )
                ),
                ast.Assign(
                    targets=[ast.Name('results', ctx=ast.Store())],
                    value=ast.Subscript(
                        value=ast.Call(
                            func=ast.Attribute(value=ast.Name('soup', ctx=ast.Load()), attr='select', ctx=ast.Load()),
                            args=[ast.Name('selector', ctx=ast.Load())],
                            keywords=[]
                        ),
                        slice=ast.Slice(upper=ast.Constant(10)),
                        ctx=ast.Load()
                    )
                ),
                ast.Return(value=ast.ListComp(
                    elt=ast.Call(
                        func=ast.Attribute(value=ast.Name('r', ctx=ast.Load()), attr='get_text', ctx=ast.Load()),
                        args=[],
                        keywords=[ast.keyword(arg='strip', value=ast.Constant(True))]
                    ),
                    generators=[ast.comprehension(
                        target=ast.Name('r', ctx=ast.Store()),
                        iter=ast.Name('results', ctx=ast.Load()),
                        ifs=[], is_async=0
                    )]
                ))
            ],
            decorator_list=[], returns=None
        )
    ], type_ignores=[])
    ast.fix_missing_locations(tree)
    return tree
