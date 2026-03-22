"""Encode a JSON config to b64. No LLM sees plaintext values.
Usage: python encode_config.py config.json [output.b64]
       python encode_config.py --stdin [output.b64]
"""
import base64, json, sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python encode_config.py <config.json> [output.b64]")
        print("       echo '{...}' | python encode_config.py --stdin [output.b64]")
        sys.exit(1)

    if sys.argv[1] == '--stdin':
        config = json.loads(sys.stdin.read())
    else:
        with open(sys.argv[1]) as f:
            config = json.load(f)

    out = sys.argv[2] if len(sys.argv) > 2 else 'config.b64'
    encoded = base64.b64encode(json.dumps(config).encode())
    with open(out, 'wb') as f:
        f.write(encoded)
    print(f"[encode] {out} ({len(encoded)}B) medium={config.get('medium','?')} keys={list(config.get('params',{}).keys())}")

if __name__ == '__main__':
    main()
