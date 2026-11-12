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
