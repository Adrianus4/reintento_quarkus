import io
import json
import os
import zipfile
import pytest

os.environ['DATABASE_URL'] = 'sqlite://'
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.api.v1.orchestrator import router
from app.api.deps import get_verified_user
from app.core.database import Base, get_db
from app.core.spec_linter import SpecLinter
from app.graph.nodes import spec_lint_and_feasibility_node
from app.models.job import GenerationJob
from app.schemas.service_spec import ServiceSpec


@pytest.fixture
def api():
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app = FastAPI()
    app.include_router(router, prefix='/api/v1/orchestrator')
    def db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = db
    app.dependency_overrides[get_verified_user] = lambda: {'user_id':'test', 'role':'ADMIN','assigned_clients':['*']}
    with factory() as session:
        session.add(GenerationJob(id='empty',user_id='test',client_code='001',requirements='test',status='FAILED',files_json='{}',error_message='Package configuration mismatch'))
        session.add(GenerationJob(id='ready',user_id='test',client_code='001',requirements='test',status='COMPLETED',files_json=json.dumps({'pom.xml':'<project/>','src/main/java/Hello.java':'class Hello {}'})))
        session.commit()
    yield app, TestClient(app)
    engine.dispose()


def test_empty_job_returns_the_actual_failure(api):
    _, client = api
    r=client.get('/api/v1/orchestrator/jobs/empty/download')
    assert r.status_code==400
    assert r.json()['detail']=='Package configuration mismatch'


def test_failed_job_cannot_be_approved(api):
    _, client = api
    r=client.post('/api/v1/orchestrator/jobs/empty/approve')
    assert r.status_code==409
    assert 'verification' in r.json()['detail']


def test_zip_contains_the_generated_sources(api):
    _, client=api
    r=client.get('/api/v1/orchestrator/jobs/ready/download')
    assert r.status_code==200 and r.headers['content-type']=='application/zip'
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert z.testzip() is None
        assert z.read('pom.xml')==b'<project/>'
        assert z.read('src/main/java/Hello.java')==b'class Hello {}'


def test_download_requires_session(api):
    app, client=api
    app.dependency_overrides.pop(get_verified_user)
    assert client.get('/api/v1/orchestrator/jobs/ready/download').status_code==401


def test_download_respects_client_scope(api):
    app, client=api
    app.dependency_overrides[get_verified_user]=lambda:{'user_id':'test','role':'DEVELOPER','assigned_clients':['other']}
    assert client.get('/api/v1/orchestrator/jobs/ready/download').status_code==403


def specification(prefix):
    return ServiceSpec(service={'name':'library','purpose':'inventory'},
        inbound=[{'id':'get','kind':'rest'}],
        behaviors=[{'id':'read','given':'books exist','when':'GET','inbound_ref':'get','then':'return books'}],
        governance_ref={'client_code':'001','package_prefix':prefix})


def test_explicit_studio_prefix_with_numeric_client():
    spec=specification('com.tcs.library.inventory')
    state={'service_spec':spec.model_dump(mode='json'),'config':{'package_prefix':'com.tcs.library.inventory'},'governance_context':{'client':{'package_prefix':'pe.com.001'}}}
    result=spec_lint_and_feasibility_node(state)
    assert result['status']=='SPEC_VALIDATED'


def test_configured_namespace_boundary_is_enforced():
    valid, errors=SpecLinter.lint_and_verify_feasibility(specification('com.companyevil'),{'package_prefix':'com.company'})
    assert not valid and any('configured prefix' in error for error in errors)


@pytest.mark.parametrize('prefix',['pe.com.001','com.class.service'])
def test_invalid_java_package_is_rejected(prefix):
    valid, errors=SpecLinter.lint_and_verify_feasibility(specification(prefix),{'package_prefix':prefix})
    assert not valid and any('Invalid Java package' in error for error in errors)
