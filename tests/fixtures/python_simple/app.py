from utils import add, multiply

def run_app():
    res = add(2, 3)
    return multiply(res, 4)

if __name__ == "__main__":
    print(run_app())
