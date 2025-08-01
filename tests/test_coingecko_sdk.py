import unittest

class TestCoingeckoSDK(unittest.TestCase):
    def setUp(self):
        return super().setUp()
    
    def tearDown(self):
        return super().tearDown()
    
    def test_tokens_save(self):
        from services.coingecko import CoingeckoAggregator

        aggregator = CoingeckoAggregator()

        is_succeeded = False
        
        try:
            aggregator.save_all_coins_with_check()
            is_succeeded = True
        except Exception as e:
            print(e)
            is_succeeded = False
        
        return self.assertEqual(is_succeeded, True)
    
    def test_exchanges_save(self):
        from services.coingecko import CoingeckoAggregator

        aggregator = CoingeckoAggregator(is_demo=False)

        is_succeeded = False
        
        try:
            aggregator.save_all_exchanges_with_check()
            is_succeeded = True
        except Exception as e:
            print(e)
            is_succeeded = False
        
        return self.assertEqual(is_succeeded, True)
    
if __name__ == '__main__':
    unittest.main()
