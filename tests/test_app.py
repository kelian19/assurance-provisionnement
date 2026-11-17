from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]

def test_business_journey_and_no_stale_bootstrap():
 app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
 assert not app.exception
 assert app.metric[0].value=='18 680 847,77'
 app.selectbox(key='simulations').set_value(500)
 app.button(key='run_bootstrap').click().run()
 assert not app.exception
 assert app.session_state['bootstrap_result']['result'].diagnostics['simulations']==500
 assert any(m.label=='Quantile 95 %' for m in app.metric)
 app.selectbox(key='dataset').set_value('cas').run()
 assert not app.exception
 assert app.metric[0].value=='12 586 821,36'
 assert not any(m.label=='Quantile 95 %' for m in app.metric)
 app.selectbox(key='dataset').set_value('raa').run()
 app.button(key='run_bootstrap').click().run()
 assert not app.exception
 assert any('incréments' in error.value for error in app.error)


def test_schnieper_tab_shows_course_reference_and_runs_its_own_bootstrap():
 app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
 assert not app.exception
 values={m.label:m.value for m in app.metric}
 assert values['Provision Schnieper']=='283,94' and values['Mack, même triangle cumulé']=='464,24'
 assert not any(m.label=='Q95 (Schnieper)' for m in app.metric)
 app.selectbox(key='schnieper_simulations').set_value(1000)
 app.button(key='run_schnieper_bootstrap').click().run()
 assert not app.exception
 result=app.session_state['schnieper_bootstrap_result']
 assert result.diagnostics['simulations']==1000 and result.diagnostics['is_mack_bootstrap'] is False
 assert any(m.label=='Q95 (Schnieper)' for m in app.metric)
 app.selectbox(key='dataset').set_value('cas').run()
 assert not app.exception
 assert app.metric[0].value=='12 586 821,36'
 assert {m.label:m.value for m in app.metric}['Provision Schnieper']=='283,94'
