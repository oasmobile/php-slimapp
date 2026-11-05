"""报告 schema 使用的 JSON Schema 子集校验；仅依赖标准库。"""
from mdf_core.foundation.errors import MDFError


def check(value, schema, root=None, path='$'):
    root = schema if root is None else root
    if '$ref' in schema:
        node = root
        for key in schema['$ref'].removeprefix('#/').split('/'):
            node = node[key]
        return check(value, node, root, path)
    kind = schema.get('type')
    valid = {'object': isinstance(value, dict), 'array': isinstance(value, list),
             'string': isinstance(value, str), 'integer': type(value) is int,
             'boolean': type(value) is bool}.get(kind, True)
    if not valid:
        raise MDFError(f'{path} 必须为 {kind}', code='invalid_review_report')
    if 'enum' in schema and value not in schema['enum']:
        raise MDFError(f'{path} 不在允许值内', code='invalid_review_report')
    if kind == 'integer' and (value < schema.get('minimum', value) or value > schema.get('maximum', value)):
        raise MDFError(f'{path} 超出允许范围', code='invalid_review_report')
    if kind == 'object':
        fields = schema.get('properties', {})
        if (set(schema.get('required', [])) - set(value)
                or (schema.get('additionalProperties') is False and set(value) - set(fields))):
            raise MDFError(f'{path} 存在缺失或额外字段', code='invalid_review_report')
        for key, item in value.items():
            if key in fields:
                check(item, fields[key], root, path + '.' + key)
    if kind == 'array':
        for index, item in enumerate(value):
            check(item, schema['items'], root, f'{path}[{index}]')
