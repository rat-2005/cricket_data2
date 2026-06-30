import data_service as ds
import db

def test():
    # Test ODI single string
    print("Testing string 'ODI'")
    print(ds.get_batter_stats(253802, {"format": "ODI"}))
    
    # Test ODI single list
    print("Testing list ['ODI']")
    print(ds.get_batter_stats(253802, {"format": ["ODI"]}))

    # Test ODI, T20I list
    print("Testing list ['ODI', 'T20I']")
    print(ds.get_batter_stats(253802, {"format": ["ODI", "T20I"]}))
    
    print("Testing list ['T20I']")
    print(ds.get_batter_stats(253802, {"format": ["T20I"]}))

test()
