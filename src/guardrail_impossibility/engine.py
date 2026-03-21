"""
ZK Recurrent Executor. Decodes b64 config, selects AST medium,
compiles, injects params at runtime, loops until termination.
No LLM sees the config contents.

Usage: python engine.py config.b64
"""
import base64, json, sys, time
from guardrail_impossibility.mediums import get_medium


def decode_config(path):
    with open(path, 'rb') as f:
        return json.loads(base64.b64decode(f.read()))


def check_termination(results, iteration, config):
    term = config.get('termination', {'type': 'count', 'value': 1})
    t = term['type']
    if t == 'count':
        return iteration >= term.get('value', 1)
    if t == 'has_results':
        return bool(results)
    if t == 'min_results':
        if isinstance(results, dict) and 'path' in results:
            return len(results['path']) > 0
        return bool(results) and len(results) >= term.get('value', 1)
    if t == 'score_threshold':
        return isinstance(results, dict) and results.get('score', 0) >= term['value']
    return True


def mutate_params(params, iteration, config):
    m = config.get('mutation', {})
    if m.get('type') == 'paginate':
        k = m.get('key', 'page')
        params[k] = params.get(k, 1) + 1
    elif m.get('type') == 'backoff':
        time.sleep(min(2 ** iteration, 30))
    return params


def main():
    config = decode_config(sys.argv[1] if len(sys.argv) > 1 else 'config.b64')
    params = config['params']
    build_ast = get_medium(config['medium'])

    ns = {}
    exec(compile(build_ast(), f'<{config["medium"]}>', 'exec'), ns)
    run = ns['run']

    max_iter = config.get('max_iterations', 10)
    results = None
    for i in range(1, max_iter + 1):
        print(f"[engine] iteration {i}/{max_iter}")
        try:
            results = run(**params)
        except Exception as e:
            print(f"[engine] error: {e}")
        if check_termination(results, i, config):
            break
        params = mutate_params(params, i, config)

    print(f"\n[engine] RESULTS:")
    if isinstance(results, list):
        for j, item in enumerate(results, 1):
            t = item.strip() if isinstance(item, str) else str(item)
            if t:
                print(f"  {j}. {t}")
    elif isinstance(results, dict):
        print(json.dumps(results, indent=2))
    else:
        print(results)


if __name__ == '__main__':
    main()
