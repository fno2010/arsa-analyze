import random

if __name__ == '__main__':
    cnt = 100
    for i in range(60):
        cnt += random.randint(10, 20)
        print(cnt)
