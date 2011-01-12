
def square(n):
    return n*n

def calculate_square_sum(start, end):
    sqsum = 0
    for i in range(start, end):
        sqsum += square(i)
    return sqsum

if __name__ == '__main__':
    sqsum = calculate_square_sum(1, 10)
    print(sqsum)
