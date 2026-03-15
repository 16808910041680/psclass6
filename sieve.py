def SieveofEratosthenesflip(n):
    #sieve of eratosthenes but going backwards
    primes = []
    for i in range(n, 1, -1):
        is_prime = True
        for j in range(2, int(i**0.5) + 1):
            if i % j == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(i)
    return primes

n = 3000
primes = SieveofEratosthenesflip(n)
print(primes)
