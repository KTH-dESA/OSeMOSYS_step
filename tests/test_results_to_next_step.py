import pandas as pd
from pytest import fixture, raises
from pandas.testing import assert_frame_equal
import main_utils as mu

@fixture
def res_capacity():
    return pd.DataFrame(
        [
            ["UTOPIA", "E01", 1995, 2],
            ["UTOPIA", "E01", 1996, 2],
            ["UTOPIA", "E01", 1997, 2],
            ["UTOPIA", "E01", 1998, 2],
            ["UTOPIA", "E01", 1999, 2],
        ], columns = ["REGION", "TECHNOLOGY", "YEAR", "VALUE"]
    )

@fixture 
def op_life():
    return pd.DataFrame(
        [
            ["E01", 5]
        ], columns=["TECHNOLOGY","VALUE"]
    )

@fixture
def new_capacity():
    return pd.DataFrame(
        [
            ["UTOPIA", "E01", 1995, 1],
            ["UTOPIA", "E01", 1997, 1],
        ], columns = ["REGION", "TECHNOLOGY", "YEAR", "VALUE"]
    )

class TestUpdateResidualCapacity:

    def test_update_residual_capacity_1(self, res_capacity, op_life, new_capacity):
        
        step_years = [1995, 1996]
        
        expected = pd.DataFrame(
            [
                ["UTOPIA", "E01", 1995, 3],
                ["UTOPIA", "E01", 1996, 3],
                ["UTOPIA", "E01", 1997, 3],
                ["UTOPIA", "E01", 1998, 3],
                ["UTOPIA", "E01", 1999, 3],
            ], columns = ["REGION", "TECHNOLOGY", "YEAR", "VALUE"]
        )
        actual = mu.update_res_capacity(
            res_capacity = res_capacity, 
            op_life = op_life, 
            new_capacity = new_capacity, 
            step_years = step_years
        )
        assert_frame_equal(actual, expected)
        
    def test_update_residual_capacity_2(self, res_capacity, op_life, new_capacity):
        
        step_years = [1995, 1996, 1997]
        
        expected = pd.DataFrame(
            [
                ["UTOPIA", "E01", 1995, 3],
                ["UTOPIA", "E01", 1996, 3],
                ["UTOPIA", "E01", 1997, 4],
                ["UTOPIA", "E01", 1998, 4],
                ["UTOPIA", "E01", 1999, 4],
                ["UTOPIA", "E01", 2000, 1],
                ["UTOPIA", "E01", 2001, 1],
            ], columns = ["REGION", "TECHNOLOGY", "YEAR", "VALUE"]
        )
        actual = mu.update_res_capacity(
            res_capacity = res_capacity, 
            op_life = op_life, 
            new_capacity = new_capacity, 
            step_years = step_years
        )
        assert_frame_equal(actual, expected)
        
class TestGetNewCapacityLifetime:
    
    def test_get_new_capacity_lifetime(self, op_life, new_capacity):
        
        expected = pd.DataFrame(
            [
                ["UTOPIA", "E01", 1995, 1],
                ["UTOPIA", "E01", 1996, 1],
                ["UTOPIA", "E01", 1997, 2],
                ["UTOPIA", "E01", 1998, 2],
                ["UTOPIA", "E01", 1999, 2],
                ["UTOPIA", "E01", 2000, 1],
                ["UTOPIA", "E01", 2001, 1],
            ], columns = ["REGION", "TECHNOLOGY", "YEAR", "VALUE"]
        )
        actual = mu.get_new_capacity_lifetime(op_life=op_life, new_capacity=new_capacity)
        assert_frame_equal(actual, expected)
        
class TestApplyOperationalLife:
        
    def test_apply_op_life_one_year(self):
        start_year = 2000
        technology = "EO1"
        mapper = {"EO1": 1}
        
        actual = mu.apply_op_life(start_year, technology, mapper)
        expected = [2000]
        assert actual == expected
        
    def test_apply_op_life_multiple_years(self):
        start_year = 2000
        technology = "EO1"
        mapper = {"EO1": 5}
        
        actual = mu.apply_op_life(start_year, technology, mapper)
        expected = [2000, 2001, 2002, 2003, 2004]
        assert actual == expected
        