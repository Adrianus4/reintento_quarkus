from unittest.mock import Mock
from app.core import compiler


def project(tmp_path):
    (tmp_path/'pom.xml').write_text('<project></project>')
    (tmp_path/'App.java').write_text('package demo; public class App {}')
    return tmp_path


def test_missing_maven_never_reports_compilation_success(tmp_path,monkeypatch):
    monkeypatch.setattr(compiler,'get_maven_binary',lambda:None)
    ok,_,_,details=compiler.run_compilation_verification(project(tmp_path))
    assert not ok
    assert details['phase_results']['test-compile']=='FAILED'


def test_native_maven_receives_goals_without_posix_shell(tmp_path,monkeypatch):
    monkeypatch.setattr(compiler,'get_maven_binary',lambda:'/usr/bin/mvn')
    run=Mock(return_value=Mock(returncode=0,stdout='BUILD SUCCESS',stderr=''))
    monkeypatch.setattr(compiler.subprocess,'run',run)
    ok,_,_,_=compiler.run_compilation_verification(project(tmp_path))
    assert ok
    assert run.call_args.args[0][-2:]==['clean','test-compile']
    assert run.call_args.kwargs['shell']==(compiler.os.name=='nt')
