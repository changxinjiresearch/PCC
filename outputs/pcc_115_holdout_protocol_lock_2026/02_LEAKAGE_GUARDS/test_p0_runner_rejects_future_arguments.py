import inspect
from src.preprocessing.current_only_preprocessing import prepare_current_only_inputs

def test_current_only_api_has_no_future_argument():
 assert 'future' not in inspect.signature(prepare_current_only_inputs).parameters
