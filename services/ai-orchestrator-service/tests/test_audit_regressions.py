from copy import deepcopy
from unittest.mock import Mock, patch
import httpx
import pytest
from app.llm.factory import LLMClientFactory
from app.llm.mock_client import MockLLMClient
from app.graph.nodes import sandbox_gate_node
from app.graph.nodes import walking_skeleton_node, static_gates_node
from app.core.synthesizer import CodeSynthesizer
from app.graph import workflow
from app.core.package_names import suggested_package_prefix


@pytest.mark.parametrize('value,expected', [('pe.com.001','pe.com.client_001'),
    ('com.tcs.bank.customer','com.tcs.bank.customer'),('pe.com.class','pe.com.client_class')])
def test_suggested_packages_have_valid_identifiers(value,expected):
    assert suggested_package_prefix(value)==expected


def test_explicit_mock_never_looks_up_credentials(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-fake-must-never-be-used')
    db = Mock()
    db.query.return_value.first.return_value.active_provider = 'MOCK'
    with patch.object(LLMClientFactory, '_build_client', side_effect=AssertionError('paid client')):
        assert isinstance(LLMClientFactory.get_client(db), MockLLMClient)
    assert db.query.call_count == 1


@pytest.mark.parametrize('code,payload,expected', [
    (401, {}, 'VERIFICATION_UNAVAILABLE'),
    (500, {}, 'VERIFICATION_UNAVAILABLE'),
    (201, {'status': 'FAILED'}, 'VETOED_BY_SANDBOX'),
    (201, {'status': 'INITIALIZED'}, 'VETOED_BY_SANDBOX'),
    (201, {'status': 'SUCCESS'}, 'VETOED_BY_SANDBOX'),
    (201, {'status':'SUCCESS','verdict':'PASSED','veto_applied':False,'failures':[]}, 'VERIFIED_PASSED'),
])
def test_sandbox_requires_explicit_positive_verdict(code, payload, expected):
    response = httpx.Response(code, json=payload)
    with patch('app.graph.nodes.httpx.Client') as client:
        client.return_value.__enter__.return_value.post.return_value = response
        result = sandbox_gate_node({'client_code':'001','job_id':'test','files':{}})
    assert result['status'] == expected


def test_offline_sandbox_fails_closed():
    with patch('app.graph.nodes.httpx.Client') as client:
        client.return_value.__enter__.return_value.post.side_effect = httpx.ConnectError('offline')
        result = sandbox_gate_node({'client_code':'001','job_id':'test','files':{}})
    assert result['status'] == 'VERIFICATION_UNAVAILABLE'
    assert 'unavailable' in result['error']


def test_numeric_client_uses_configured_package():
    state={'client_code':'001','config':{'package_prefix':'com.tcs.inventory'},'files':{},'blueprint':{}}
    result=CodeSynthesizer.guarantee_project(state)
    java={p:s for p,s in result['files'].items() if p.endswith('.java')}
    assert java
    assert all('package com.tcs.inventory' in content for content in java.values())
    assert all('/com/tcs/inventory/' in path for path in java)
    assert not any('pe.com.001' in content for content in java.values())


def test_static_gates_preserve_skeleton_dependencies():
    state={'client_code':'001','config':{'package_prefix':'com.tcs.inventory'},'files':{},
           'blueprint':{},'manifest':[], 'service_spec':{'governance_ref':{'package_prefix':'com.tcs.inventory'}}}
    walking_skeleton_node(state)
    before={p for p in state['files'] if p.endswith('.java')}
    static_gates_node(state)
    assert {p for p in state['files'] if p.endswith('.java')}==before
    assert any(p.endswith('/ResourceNotFoundException.java') for p in before)
    assert any(p.endswith('/PageResponse.java') for p in before)


def test_synthesizer_rejects_invalid_package():
    with pytest.raises(ValueError, match='Invalid Java package'):
        CodeSynthesizer.guarantee_project({'client_code':'001','files':{},'blueprint':{}})


@pytest.mark.parametrize('status,expected_calls', [('VERIFICATION_UNAVAILABLE',1),('VETOED_BY_SANDBOX',4)])
def test_failed_verification_cannot_be_masked_by_last_repair(monkeypatch,status,expected_calls):
    for name in ['fetch_governance_node','spec_builder_node','spec_lint_and_feasibility_node',
                 'resolve_capabilities_node','architecture_plan_node','acceptance_tests_node',
                 'walking_skeleton_node','implement_loop_node','static_gates_node','repair_agent_node']:
        monkeypatch.setattr(workflow,name,lambda state,*args:state)
    calls=[]
    def gate(state,*args):
        calls.append(True);state.update(status=status,error='verification failed');return state
    monkeypatch.setattr(workflow,'sandbox_gate_node',gate)
    result=workflow.GenerationWorkflow.run_pipeline('test','user','001')
    assert result['status']=='FAILED'
    assert len(calls)==expected_calls
