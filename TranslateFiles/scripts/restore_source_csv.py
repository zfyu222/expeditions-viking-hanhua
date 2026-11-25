"""Restore the published translation's source CSV from its resource key table."""

import csv
import hashlib
import io
import json
from pathlib import Path


def main():
    project = Path(__file__).resolve().parents[2]
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    with (project / 'extracted_strings.csv').open(encoding='utf-8-sig', newline='') as stream:
        writer.writerows([row['原文']] for row in csv.DictReader(stream))

    data = output.getvalue().encode('utf-8-sig')
    report = json.loads((project / 'TranslateFiles/reports/final_validation.json').read_bytes())
    if hashlib.sha256(data).hexdigest() != report['source_sha256']:
        raise ValueError('The resource key table no longer matches the reviewed source CSV')

    source = project / 'expeditions-viking_text.csv'
    with source.open('xb') as stream:
        stream.write(data)
    print(source)


if __name__ == '__main__':
    main()
