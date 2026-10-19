"""Collect actual Sol output from an existing short-ID handoff, without an API call."""
import json
from pathlib import Path
import sys
PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT.parents[1]/'Tools/localization'))
import translation_workflow as w
import ainiee_bridge as bridge
from workflow_task_contract import canonical_api_result

def collect(session):
    flow=w.Workflow(PROJECT)
    with flow.db() as db:
        run=dict(flow._batch_run(db,session))
        task=dict(flow.valid_task(db,run['task_id'],run['token']))
    path=Path(run['result_file'])
    raw=path.with_name('response.raw.txt')
    parsed=bridge.parse_response(raw.read_text('utf-8'),path.with_name('response.normalization.json'))
    result=canonical_api_result(parsed,w.read_json(path.with_name('api_id_transport.v2.json')),
        session,task['id'],task['input_hash'],json.loads(run['scope']))
    w.write_json(path,result)
    w.write_json(path.with_name('sol_execution.json'),{'backend':'codex','model':'gpt-6-sol',
        'worker':run['worker'],'raw_sha256':w.digest(raw),'api_request':False})
    print(json.dumps(flow.batch_finish(session),ensure_ascii=True))

if __name__=='__main__':collect(sys.argv[1])
