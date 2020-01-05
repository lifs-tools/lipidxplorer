import unittest
from LX2_targets import MFQL_util

class TestLX2_MS_reader(unittest.TestCase):
    
    def setUp(self):
        elements = {'C':(30,300),'H':(40,300),'O':(10,10),'N':(1,1),'P':(1,1) }
        self.test = MFQL_util(elements)
            
    def test_makeAllCombo(self):
        pr = self.test._df.sample(n=10, random_state = 1)
        fr = self.test._df.sample(n=3, random_state = 2)
        df = self.test.makeAllCombo(pr,fr)
        in_df = self.test.suchThat(df,'C_pr % 2 == 0')

        self.assertEqual(len(df), 30)
        self.assertEqual(len(in_df), 21)
    
if __name__ == '__main__':
    unittest.main()