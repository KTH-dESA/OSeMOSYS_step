import pandas as pd
import os
from osemosys_step import results_to_next_step as rtns

class TestResultsTransfer:

    def test_sum_rescap_newcap(self):

        folder = os.path.join('..', 'tests', 'fixtures')
        dp_path = os.path.join(folder, 'data')
        res_path = os.path.join(folder, 'results')

        res_cap = pd.read_csv(os.path.join(dp_path, 'ResidualCapacity.csv'))

        data = [
            ['TEST','TECA',0,1.5],
            ['TEST','TECB',0,1],
            ['TEST','TECB',1,2],
            ['TEST','TECA',1,0.5],
            ['TEST','TECC',0,1],
            ['TEST','TECC',1,0],
        ]

        expected = pd.DataFrame(data=data, columns=['REGION', 'TECHNOLOGY', 'YEAR', 'VALUE'])

        index = ['REGION', 'TECHNOLOGY', 'YEAR']

        rtns.main(dp_path, res_path)
        new_res_cap = pd.read_csv(os.path.join(dp_path, 'ResidualCapacity.csv'))

        pd.testing.assert_frame_equal(new_res_cap.set_index(index), expected.set_index(index), check_index_type=False)

        res_cap.to_csv(os.path.join(dp_path, 'ResidualCapacity.csv'))