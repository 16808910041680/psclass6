from math import sqrt
n = int(input("Enter a number:"))

def isprime (n):
    if n <= 1:
        return False
    for i in range(2, int(sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def factors(n):
    factors = []
    for i in range(1, n + 1):
        if n % i == 0:
            factors.append(i)
    return factors

print(isprime(n))
if isprime(n) == False:
    print(factors(n))
