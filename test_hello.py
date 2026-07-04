from hello import greet

def test_greet():
    assert greet("World") == "Hello, World!"
    print("Test passed!")

if __name__ == "__main__":
    test_greet()